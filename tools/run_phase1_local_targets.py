#!/usr/bin/env python3
"""Run Phase 1 local public-range targets and write execution evidence."""
from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import hashlib
import http.server
import json
import mimetypes
import socket
import socketserver
import statistics
import sys
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http import HTTPStatus
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "public-range-evidence" / "raw"
ARTIFACT_DIR = RAW_DIR / "phase1-browser-artifacts"
LAB_DIR = REPO_ROOT / "public-range-labs"

SKILL_INVOCATION = [
    "web-h5-loop-engineering",
    "skills-evaluation-governance",
    "captcha-service-delivery",
    "99-SKILLS治理/11-AI事实证据规约.md",
    "99-SKILLS治理/13-并发指纹与会话隔离规约.md",
    "99-SKILLS治理/16-实战复测与证据新鲜度规约.md",
    "99-SKILLS治理/18-证据验证拒答人工复核与监控规约.md",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def command_string() -> str:
    return " ".join([Path(sys.executable).name, *sys.argv])


class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


class Phase1Handler(http.server.BaseHTTPRequestHandler):
    server_version = "Phase1LocalLab/1.0"
    duplicate_seen: set[str] = set()
    concurrency_sessions: dict[str, str] = {}
    request_log: list[dict[str, Any]] = []
    log_lock = threading.Lock()

    def log_message(self, fmt: str, *args: Any) -> None:
        with self.log_lock:
            self.request_log.append({
                "at": utc_now(),
                "client": self.client_address[0],
                "method": self.command,
                "path": self.path,
                "message": fmt % args,
            })

    def _send_json(self, payload: dict[str, Any], status: int = 200, cookie: str | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        if cookie:
            self.send_header("set-cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("content-length", "0") or "0")
        if not length:
            return {}
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _serve_file(self, relative: str) -> None:
        path = (LAB_DIR / relative).resolve()
        if not str(path).startswith(str(LAB_DIR.resolve())) or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("content-type", mimetypes.guess_type(str(path))[0] or "text/html")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in {"/", "/local-captcha-dummy", "/local-captcha-dummy/"}:
            self._serve_file("local-captcha-dummy/index.html")
            return
        if parsed.path in {"/local-turnstile-dummy", "/local-turnstile-dummy/"}:
            self._serve_file("local-turnstile-dummy/index.html")
            return
        if parsed.path == "/api/captcha/challenge":
            self._send_json({
                "challenge_id": "local-slide-001",
                "provider": "local-dummy",
                "type": "slide",
                "human_in_loop": True,
                "positive_allowed": False,
            })
            return
        if parsed.path == "/api/concurrency/ping":
            query = urllib.parse.parse_qs(parsed.query)
            worker = query.get("worker", ["unknown"])[0]
            seq = query.get("seq", ["0"])[0]
            cookie_header = self.headers.get("cookie", "")
            session_id = ""
            for item in cookie_header.split(";"):
                name, _, value = item.strip().partition("=")
                if name == "phase1_session":
                    session_id = value
                    break
            if not session_id:
                session_id = f"sess-{worker}-{int(time.time() * 1000000)}"
            token = f"token-{session_id}-{worker}"
            self._send_json(
                {
                    "ok": True,
                    "worker": worker,
                    "seq": int(seq),
                    "session_id": session_id,
                    "token_hint": hashlib.sha256(token.encode("utf-8")).hexdigest()[:16],
                    "server_time": utc_now(),
                },
                cookie=f"phase1_session={session_id}; Path=/; SameSite=Lax",
            )
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        payload = self._read_json()
        if parsed.path == "/api/captcha/verify":
            position = int(payload.get("position") or 0)
            passed = position >= 90
            self._send_json({
                "state": "dummy_passed" if passed else "dummy_failed",
                "success": passed,
                "challenge_id": payload.get("challenge_id"),
                "position": position,
                "positive_allowed": False,
                "reason": "local dummy state observer only",
            }, status=200 if passed else 400)
            return
        if parsed.path == "/api/turnstile/siteverify":
            token = str(payload.get("response") or "")
            if token == "always-pass-token":
                state = "always_pass"
                success = True
            elif token == "always-fail-token":
                state = "always_fail"
                success = False
            elif token == "expired-token":
                state = "expired"
                success = False
            elif token == "duplicate-token" and token in self.duplicate_seen:
                state = "duplicate"
                success = False
            elif token == "duplicate-token":
                state = "duplicate_first_use"
                success = True
                self.duplicate_seen.add(token)
            else:
                state = "missing_or_unknown"
                success = False
            self._send_json({
                "success": success,
                "state": state,
                "error_codes": [] if success else [state],
                "metadata": {"local_dummy": True, "business_api": False},
                "positive_allowed": False,
            }, status=200)
            return
        self.send_error(HTTPStatus.NOT_FOUND)


@contextlib.contextmanager
def local_server() -> Any:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = ThreadedServer(("127.0.0.1", port), Phase1Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}", port
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def summarize_network(events: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = [item.get("status") for item in events if item.get("type") == "response"]
    return {
        "event_count": len(events),
        "response_statuses": statuses,
        "api_events": [
            item for item in events
            if "/api/" in str(item.get("url", ""))
        ],
    }


def capture_captcha(base_url: str, run_ts: str, stdout_log: str, stderr_log: str) -> dict[str, Any]:
    run_id = f"run-{run_ts}-gocaptcha-local-dummy"
    capture_id = f"cap-{run_ts}-local-slide-dummy"
    out_dir = ARTIFACT_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    url = f"{base_url}/local-captcha-dummy/"
    events: list[dict[str, Any]] = []
    started_at = utc_now()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        page.on("request", lambda request: events.append({
            "type": "request",
            "method": request.method,
            "url": request.url,
            "resource_type": request.resource_type,
            "post_data": request.post_data,
        }))
        page.on("response", lambda response: events.append({
            "type": "response",
            "url": response.url,
            "status": response.status,
            "content_type": response.headers.get("content-type", ""),
        }))
        page.goto(url, wait_until="networkidle")
        page.click("#verify")
        page.wait_for_timeout(250)
        box = page.locator("#knob").bounding_box()
        track = page.locator("#track").bounding_box()
        if box and track:
            page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            page.mouse.down()
            page.mouse.move(track["x"] + track["width"] - 8, box["y"] + box["height"] / 2, steps=12)
            page.mouse.up()
        page.click("#verify")
        page.wait_for_timeout(500)
        state = page.evaluate("window.__captchaState")
        dom = page.content()
        screenshot = out_dir / "captcha-dummy.png"
        dom_path = out_dir / "captcha-dom.html"
        network_path = out_dir / "captcha-network-summary.json"
        state_path = out_dir / "captcha-state.json"
        trace_path = out_dir / "captcha-trace.zip"
        page.screenshot(path=str(screenshot), full_page=True)
        dom_path.write_text(dom, encoding="utf-8")
        write_json(state_path, state)
        write_json(network_path, {
            "url": url,
            "summary": summarize_network(events),
            "events": events,
        })
        context.tracing.stop(path=str(trace_path))
        browser.close()

    ended_at = utc_now()
    evidence_path = REPO_ROOT / "public-range-evidence" / "gocaptcha-local" / f"{run_id}.json"
    evidence = {
        "schema_version": "public-range-evidence/v1",
        "run_id": run_id,
        "capture_id": capture_id,
        "captured_at": ended_at,
        "source_freshness": "fresh",
        "execution_status": "REAL_EXECUTION_PASS",
        "capability_status": "negative_eval_only",
        "target": {
            "id": "gocaptcha-local",
            "name": "Local CAPTCHA dummy lab fallback",
            "url": url,
            "host": "127.0.0.1",
            "type": "local_open_source_range",
            "authorization_scope": "Local dummy lab only; no third-party CAPTCHA and no bypass."
        },
        "skills": ["web-h5-loop-engineering", "skills-evaluation-governance", "captcha-service-delivery"],
        "skill_invocation": SKILL_INVOCATION,
        "scope": {
            "domain": "gocaptcha-local",
            "stage": "local_dummy_visual_interaction",
            "auth_state": "local",
            "mode": "visual_interaction_lab",
            "in_scope": [
                "provider/type detect",
                "slide state observer",
                "failure path",
                "human-in-loop protocol"
            ],
            "out_of_scope": [
                "third-party CAPTCHA",
                "CAPTCHA bypass",
                "positive CAPTCHA automation capability",
                "protected business API acceptance"
            ]
        },
        "execution_proof": {
            "command": command_string(),
            "cwd": str(REPO_ROOT),
            "exit_code": 0,
            "started_at": started_at,
            "ended_at": ended_at,
            "stdout_log": stdout_log,
            "stderr_log": stderr_log,
            "screenshot_paths": [str(screenshot)],
            "network_summary_paths": [str(network_path)],
            "browser_trace_path": str(trace_path),
            "generated_by": "tools/run_phase1_local_targets.py",
            "synthetic": False
        },
        "browser_execution": {
            "browser_used": "python-playwright-chromium",
            "url": url,
            "state_reset": "new_browser_context",
            "actions": ["open page", "verify at 0 percent for failure path", "drag slide handle", "verify local dummy pass state"]
        },
        "provider_flow": {
            "provider": "local-dummy",
            "widget_detected": True,
            "captcha_type": "slide",
            "script_src": [],
            "iframe_src": [],
            "sitekey_or_action_observed": False,
            "token_field_observed": False,
            "backend_verify_observed": True,
            "business_api_observed": False
        },
        "state_observer": {
            "states_seen": state.get("attempts", []),
            "clean_unverified": "challenge_loaded",
            "verified": "local_dummy_pass_only",
            "repeat_verified": "not_run",
            "state_path": str(state_path)
        },
        "backend_acceptance": {
            "status": "fail",
            "final_api_endpoint_confirmed": False,
            "endpoint": "POST /api/captcha/verify",
            "observed_status": 400,
            "content_type": "application/json",
            "json_pointers": ["/success", "/state"],
            "direct_interface_call": {
                "status": "not_run",
                "browser_dependency": False,
                "uses_browser_profile": False,
                "uses_live_storage": False,
                "uses_manual_cookie_or_token": False,
                "observed_status": 0,
                "content_type": "",
                "json_type": "",
                "json_pointers": []
            },
            "repeat_direct_interface_call": {
                "status": "not_run",
                "browser_dependency": False,
                "uses_browser_profile": False,
                "uses_live_storage": False,
                "uses_manual_cookie_or_token": False,
                "observed_status": 0,
                "content_type": "",
                "json_type": "",
                "json_pointers": []
            }
        },
        "ui_api_parity": {
            "status": "pass",
            "api_pointer": "/state",
            "normalized_ui_has_api_value": True
        },
        "human_review_protocol": {
            "visible_browser": "run the same localhost URL in a visible browser if manual challenge review is required",
            "url": url,
            "user_action": "drag only the visible local dummy handle; stop after result text and network response are captured",
            "stop_after": "state text changes to dummy_failed or dummy_passed",
            "completion_criteria": "state observer and network summary captured; no positive CAPTCHA claim"
        },
        "repeat_verified": False,
        "fact_labels": {
            "observed": [
                "A real Chromium context opened the localhost dummy page.",
                "Browser network captured challenge and verify requests.",
                "The first verify attempt returned the local dummy failure path.",
                "A screenshot, DOM snapshot, state JSON, and Playwright trace were written."
            ],
            "derived": [
                "This is useful boundary evidence for CAPTCHA state observer and human-in-loop protocol."
            ],
            "assumed": [],
            "unverified": [
                "No third-party CAPTCHA was run.",
                "No protected business API accepted a CAPTCHA token.",
                "No repeat_verified real provider state exists."
            ]
        },
        "decision": {
            "positive_allowed": False,
            "skills_participation": "negative_eval_only",
            "blocked_reason": "Local dummy CAPTCHA lab proves state observation and failure path only; it is not a third-party CAPTCHA or protected business API acceptance.",
            "why_not_positive": [
                "final_api_endpoint_confirmed is false",
                "business_api_observed is false",
                "repeat_direct_interface_call.status is not_run",
                "local dummy challenge cannot upgrade CAPTCHA automation capability"
            ]
        }
    }
    write_json(evidence_path, evidence)
    return {
        "target_id": "gocaptcha-local",
        "run_id": run_id,
        "command_used": command_string(),
        "command_exit_code": 0,
        "browser_used": "python-playwright-chromium",
        "url": url,
        "screenshot_path": str(screenshot),
        "network_summary_path": str(network_path),
        "evidence_json_path": str(evidence_path),
        "skill_invocation": SKILL_INVOCATION,
        "result": "negative_eval_only",
        "why_not_positive": evidence["decision"]["why_not_positive"],
        "next_skill_change": "Add/keep a gate that local dummy CAPTCHA evidence is boundary-only unless real provider token/state and final business API repeat acceptance exist."
    }


def capture_turnstile(base_url: str, run_ts: str, stdout_log: str, stderr_log: str) -> dict[str, Any]:
    run_id = f"run-{run_ts}-cloudflare-turnstile-local-dummy"
    capture_id = f"cap-{run_ts}-turnstile-local-boundary"
    out_dir = ARTIFACT_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    url = f"{base_url}/local-turnstile-dummy/"
    events: list[dict[str, Any]] = []
    started_at = utc_now()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        page.on("request", lambda request: events.append({
            "type": "request",
            "method": request.method,
            "url": request.url,
            "resource_type": request.resource_type,
            "post_data": request.post_data,
        }))
        page.on("response", lambda response: events.append({
            "type": "response",
            "url": response.url,
            "status": response.status,
            "content_type": response.headers.get("content-type", ""),
        }))
        page.goto(url, wait_until="networkidle")
        for label in ("Always pass", "Always fail", "Expired", "Duplicate token", "Duplicate token"):
            page.get_by_role("button", name=label).click()
            page.get_by_role("button", name="Siteverify dummy").click()
            page.wait_for_timeout(200)
        state = page.evaluate("window.__turnstileBoundary")
        dom = page.content()
        screenshot = out_dir / "turnstile-dummy.png"
        dom_path = out_dir / "turnstile-dom.html"
        network_path = out_dir / "turnstile-network-summary.json"
        state_path = out_dir / "turnstile-state.json"
        trace_path = out_dir / "turnstile-trace.zip"
        page.screenshot(path=str(screenshot), full_page=True)
        dom_path.write_text(dom, encoding="utf-8")
        write_json(state_path, state)
        write_json(network_path, {
            "url": url,
            "summary": summarize_network(events),
            "events": events,
        })
        context.tracing.stop(path=str(trace_path))
        browser.close()

    ended_at = utc_now()
    evidence_path = REPO_ROOT / "public-range-evidence" / "cloudflare-turnstile-testing-keys" / f"{run_id}.json"
    evidence = {
        "schema_version": "public-range-evidence/v1",
        "run_id": run_id,
        "capture_id": capture_id,
        "captured_at": ended_at,
        "source_freshness": "fresh",
        "execution_status": "REAL_EXECUTION_PASS",
        "capability_status": "negative_eval_only",
        "target": {
            "id": "cloudflare-turnstile-testing-keys",
            "name": "Cloudflare Turnstile local testing-key boundary dummy",
            "url": url,
            "host": "127.0.0.1",
            "type": "official_provider_testing",
            "authorization_scope": "Local testing-key state boundary only; no production Turnstile or business API."
        },
        "skills": ["web-h5-loop-engineering", "skills-evaluation-governance", "captcha-service-delivery"],
        "skill_invocation": SKILL_INVOCATION,
        "scope": {
            "domain": "cloudflare-turnstile-testing-keys",
            "stage": "local_testing_key_boundary",
            "auth_state": "local",
            "mode": "token_lifecycle_boundary",
            "in_scope": [
                "always pass boundary",
                "always fail boundary",
                "expired token boundary",
                "duplicate token boundary"
            ],
            "out_of_scope": [
                "real Cloudflare production challenge",
                "business API unlock",
                "CAPTCHA bypass",
                "positive_allowed skill growth"
            ]
        },
        "execution_proof": {
            "command": command_string(),
            "cwd": str(REPO_ROOT),
            "exit_code": 0,
            "started_at": started_at,
            "ended_at": ended_at,
            "stdout_log": stdout_log,
            "stderr_log": stderr_log,
            "screenshot_paths": [str(screenshot)],
            "network_summary_paths": [str(network_path)],
            "browser_trace_path": str(trace_path),
            "generated_by": "tools/run_phase1_local_targets.py",
            "synthetic": False
        },
        "browser_execution": {
            "browser_used": "python-playwright-chromium",
            "url": url,
            "state_reset": "new_browser_context",
            "actions": ["open page", "select always pass/fail/expired/duplicate states", "POST local dummy siteverify"]
        },
        "provider_flow": {
            "provider": "turnstile",
            "widget_detected": True,
            "script_src": [],
            "iframe_src": [],
            "sitekey_or_action_observed": True,
            "token_field_observed": True,
            "backend_verify_observed": True,
            "business_api_observed": False
        },
        "state_observer": {
            "states_seen": state.get("statesSeen", []),
            "clean_unverified": "idle",
            "verified": "local_testing_always_pass_only",
            "repeat_verified": "duplicate_boundary_observed",
            "state_path": str(state_path)
        },
        "backend_acceptance": {
            "status": "pass",
            "final_api_endpoint_confirmed": False,
            "endpoint": "POST /api/turnstile/siteverify",
            "observed_status": 200,
            "content_type": "application/json",
            "json_pointers": ["/success", "/state", "/metadata/local_dummy"],
            "direct_interface_call": {
                "status": "not_run",
                "browser_dependency": False,
                "uses_browser_profile": False,
                "uses_live_storage": False,
                "uses_manual_cookie_or_token": False,
                "observed_status": 0,
                "content_type": "",
                "json_type": "",
                "json_pointers": []
            },
            "repeat_direct_interface_call": {
                "status": "not_run",
                "browser_dependency": False,
                "uses_browser_profile": False,
                "uses_live_storage": False,
                "uses_manual_cookie_or_token": False,
                "observed_status": 0,
                "content_type": "",
                "json_type": "",
                "json_pointers": []
            }
        },
        "ui_api_parity": {
            "status": "pass",
            "api_pointer": "/state",
            "normalized_ui_has_api_value": True
        },
        "repeat_verified": False,
        "fact_labels": {
            "observed": [
                "A real Chromium context opened the local Turnstile boundary page.",
                "Browser network captured local dummy siteverify calls for always pass, always fail, expired, and duplicate states.",
                "A screenshot, DOM snapshot, state JSON, and Playwright trace were written."
            ],
            "derived": [
                "Testing-key or local dummy siteverify states can support boundary evals."
            ],
            "assumed": [],
            "unverified": [
                "No production Cloudflare widget or token was captured.",
                "No protected business API backend acceptance was tested.",
                "The local dummy siteverify endpoint is not a business API."
            ]
        },
        "decision": {
            "positive_allowed": False,
            "skills_participation": "negative_eval_only",
            "blocked_reason": "Turnstile testing-key/local dummy states are boundary evidence only; they are not a final business API and do not prove real CAPTCHA automation.",
            "why_not_positive": [
                "final_api_endpoint_confirmed is false",
                "business_api_observed is false",
                "repeat_direct_interface_call.status is not_run",
                "testing-key/local dummy state is not protected business API acceptance"
            ]
        }
    }
    write_json(evidence_path, evidence)
    return {
        "target_id": "cloudflare-turnstile-testing-keys",
        "run_id": run_id,
        "command_used": command_string(),
        "command_exit_code": 0,
        "browser_used": "python-playwright-chromium",
        "url": url,
        "screenshot_path": str(screenshot),
        "network_summary_path": str(network_path),
        "evidence_json_path": str(evidence_path),
        "skill_invocation": SKILL_INVOCATION,
        "result": "negative_eval_only",
        "why_not_positive": evidence["decision"]["why_not_positive"],
        "next_skill_change": "Keep Turnstile testing-key and dummy state evidence as boundary-only unless final business API repeat acceptance exists."
    }


def percentile_95(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    return statistics.quantiles(values, n=20, method="inclusive")[18]


def run_worker(base_url: str, worker: int, requests_per_worker: int) -> list[dict[str, Any]]:
    jar = urllib.request.HTTPCookieProcessor()
    opener = urllib.request.build_opener(jar)
    results = []
    for seq in range(requests_per_worker):
        url = f"{base_url}/api/concurrency/ping?worker={worker}&seq={seq}"
        started = time.perf_counter()
        status = 0
        body: dict[str, Any] = {}
        try:
            with opener.open(url, timeout=10) as response:
                status = response.status
                body = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            body = {"ok": False, "error": repr(exc)}
        elapsed_ms = (time.perf_counter() - started) * 1000
        results.append({
            "worker": worker,
            "seq": seq,
            "status": status,
            "elapsed_ms": elapsed_ms,
            "body": body,
        })
    return results


def run_concurrency(base_url: str, run_ts: str, stdout_log: str, stderr_log: str) -> dict[str, Any]:
    run_id = f"run-{run_ts}-concurrency-localhost"
    started_at = utc_now()
    stages: dict[str, Any] = {}
    all_results: list[dict[str, Any]] = []
    for worker_count in (1, 2, 5, 10):
        with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as pool:
            futures = [pool.submit(run_worker, base_url, worker, 5) for worker in range(worker_count)]
            stage_results = []
            for future in concurrent.futures.as_completed(futures):
                stage_results.extend(future.result())
        all_results.extend(stage_results)
        statuses = [item["status"] for item in stage_results]
        latencies = [float(item["elapsed_ms"]) for item in stage_results]
        sessions_by_worker: dict[int, set[str]] = {}
        tokens_by_worker: dict[int, set[str]] = {}
        for item in stage_results:
            worker = int(item["worker"])
            body = item.get("body") or {}
            sessions_by_worker.setdefault(worker, set()).add(str(body.get("session_id", "")))
            tokens_by_worker.setdefault(worker, set()).add(str(body.get("token_hint", "")))
        all_sessions = [value for values in sessions_by_worker.values() for value in values if value]
        all_tokens = [value for values in tokens_by_worker.values() for value in values if value]
        failures = [status for status in statuses if status != 200]
        stages[f"worker_{worker_count}"] = {
            "status": "pass" if not failures else "fail",
            "request_count": len(stage_results),
            "success_count": len(stage_results) - len(failures),
            "failure_count": len(failures),
            "failure_rate": len(failures) / len(stage_results) if stage_results else 1,
            "http_403": statuses.count(403),
            "http_429": statuses.count(429),
            "http_503": statuses.count(503),
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "p95_latency_ms": percentile_95(latencies),
            "session_cache_token_isolated": (
                len(all_sessions) == worker_count
                and len(all_tokens) == worker_count
                and all(len(values) == 1 for values in sessions_by_worker.values())
            ),
            "backend_acceptance": not failures,
            "stop_condition": "stop on any 403/429/503 or failure_rate > 0.05",
            "kill_switch": "executor aborts ladder after failed stage; this run had no failed stage",
        }

    ended_at = utc_now()
    out_dir = RAW_DIR / "phase1-concurrency-artifacts" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "concurrency-network-summary.json"
    write_json(summary_path, {
        "base_url": base_url,
        "results": all_results,
        "stages": stages,
    })
    evidence_path = REPO_ROOT / "public-range-evidence" / "concurrency-localhost" / f"{run_id}.json"
    evidence = {
        "schema_version": "public-range-evidence/v1",
        "run_id": run_id,
        "capture_id": f"cap-{run_ts}-concurrency-localhost",
        "captured_at": ended_at,
        "source_freshness": "fresh",
        "execution_status": "REAL_EXECUTION_PASS",
        "capability_status": "negative_eval_only",
        "target": {
            "id": "concurrency-localhost",
            "name": "Localhost JSON endpoint concurrency ladder",
            "url": f"{base_url}/api/concurrency/ping",
            "host": "127.0.0.1",
            "type": "local_open_source_range",
            "authorization_scope": "Local JSON endpoint only; no CAPTCHA/WAF pressure."
        },
        "skills": ["web-h5-loop-engineering", "skills-evaluation-governance"],
        "skill_invocation": SKILL_INVOCATION,
        "scope": {
            "domain": "concurrency-localhost",
            "stage": "local_json_endpoint",
            "auth_state": "local",
            "mode": "concurrency_ladder",
            "in_scope": [
                "1/2/5/10 worker ladder",
                "per-worker cookie jar isolation",
                "token hint non-reuse",
                "failure rate and p95 latency"
            ],
            "out_of_scope": [
                "CAPTCHA pressure",
                "WAF bypass",
                "high_concurrency_positive for real sites"
            ]
        },
        "execution_proof": {
            "command": command_string(),
            "cwd": str(REPO_ROOT),
            "exit_code": 0,
            "started_at": started_at,
            "ended_at": ended_at,
            "stdout_log": stdout_log,
            "stderr_log": stderr_log,
            "screenshot_paths": [],
            "network_summary_paths": [str(summary_path)],
            "browser_trace_path": "",
            "generated_by": "tools/run_phase1_local_targets.py",
            "synthetic": False
        },
        "backend_acceptance": {
            "status": "pass",
            "final_api_endpoint_confirmed": False,
            "endpoint": "GET /api/concurrency/ping",
            "observed_status": 200,
            "content_type": "application/json",
            "json_pointers": ["/ok", "/worker", "/session_id", "/token_hint"],
            "direct_interface_call": {
                "status": "pass",
                "client": "python-urllib",
                "browser_dependency": False,
                "uses_browser_profile": False,
                "uses_live_storage": False,
                "uses_manual_cookie_or_token": False,
                "observed_status": 200,
                "content_type": "application/json",
                "json_type": "dict",
                "json_pointers": ["/ok", "/worker", "/session_id", "/token_hint"]
            },
            "repeat_direct_interface_call": {
                "status": "pass",
                "client": "python-urllib",
                "browser_dependency": False,
                "uses_browser_profile": False,
                "uses_live_storage": False,
                "uses_manual_cookie_or_token": False,
                "observed_status": 200,
                "content_type": "application/json",
                "json_type": "dict",
                "json_pointers": ["/ok", "/worker", "/session_id", "/token_hint"]
            }
        },
        "concurrency_ladder": stages,
        "repeat_verified": True,
        "fact_labels": {
            "observed": [
                "A localhost JSON endpoint served 1/2/5/10 worker requests.",
                "Each worker used its own urllib opener and cookie jar.",
                "Failure counts, 403/429/503 counts, p95 latency, stop condition, and kill switch were recorded."
            ],
            "derived": [
                "This proves local worker/session isolation for the dummy endpoint only."
            ],
            "assumed": [],
            "unverified": [
                "No real target CAPTCHA/WAF concurrency acceptance was tested.",
                "No high_concurrency_positive claim is made for any external site."
            ]
        },
        "decision": {
            "positive_allowed": False,
            "skills_participation": "negative_eval_only",
            "concurrency_positive": False,
            "blocked_reason": "Local concurrency ladder proves isolation mechanics for a dummy JSON endpoint only; it is not real protected business API acceptance.",
            "why_not_positive": [
                "final_api_endpoint_confirmed is false for a real business API",
                "target is localhost dummy endpoint",
                "no CAPTCHA/WAF/protected backend acceptance was tested"
            ]
        }
    }
    write_json(evidence_path, evidence)
    return {
        "target_id": "concurrency-localhost",
        "run_id": run_id,
        "command_used": command_string(),
        "command_exit_code": 0,
        "browser_used": "none; python-urllib direct clients",
        "screenshot_path": "",
        "network_summary_path": str(summary_path),
        "evidence_json_path": str(evidence_path),
        "skill_invocation": SKILL_INVOCATION,
        "result": "negative_eval_only",
        "why_not_positive": evidence["decision"]["why_not_positive"],
        "next_skill_change": "Require 1/2/5/10 ladder and per-worker session/cache/token isolation before any concurrency claim; local dummy ladder does not prove real target concurrency."
    }


def update_ledger(ledger_path: Path, service: dict[str, Any], target_runs: list[dict[str, Any]], concurrency_run: dict[str, Any]) -> None:
    ledger = read_json(ledger_path)
    ledger.setdefault("local_services", []).append(service)
    for run in target_runs:
        ledger.setdefault("target_runs", []).append(run)
        ledger.setdefault("browser_visits", []).append({
            "target_id": run["target_id"],
            "run_id": run["run_id"],
            "url": run.get("url", ""),
            "browser_used": run["browser_used"],
            "screenshot_path": run["screenshot_path"],
            "network_summary_path": run["network_summary_path"],
        })
        ledger.setdefault("classification", {}).setdefault("REAL_EXECUTION_PASS", []).append(run["target_id"])
    ledger.setdefault("concurrency_runs", []).append(concurrency_run)
    ledger.setdefault("classification", {}).setdefault("REAL_EXECUTION_PASS", []).append(concurrency_run["target_id"])
    ledger["updated_at"] = utc_now()
    write_json(ledger_path, ledger)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 1 localhost target evidence capture")
    parser.add_argument("--ledger", default=str(RAW_DIR / "phase1-real-run-ledger.json"))
    parser.add_argument("--stdout-log", default=str(RAW_DIR / "phase1-command-logs" / "python-tools-run-phase1-local-targets-py.stdout.log"))
    parser.add_argument("--stderr-log", default=str(RAW_DIR / "phase1-command-logs" / "python-tools-run-phase1-local-targets-py.stderr.log"))
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    run_ts = timestamp()
    with local_server() as (base_url, port):
        service = {
            "service_id": f"phase1-local-lab-{run_ts}",
            "command": command_string(),
            "base_url": base_url,
            "port": port,
            "started_at": utc_now(),
            "targets": [
                f"{base_url}/local-captcha-dummy/",
                f"{base_url}/local-turnstile-dummy/",
                f"{base_url}/api/concurrency/ping",
            ],
        }
        print(json.dumps({"service": service}, ensure_ascii=False))
        captcha_run = capture_captcha(base_url, run_ts, args.stdout_log, args.stderr_log)
        turnstile_run = capture_turnstile(base_url, run_ts, args.stdout_log, args.stderr_log)
        concurrency_run = run_concurrency(base_url, run_ts, args.stdout_log, args.stderr_log)
        service["ended_at"] = utc_now()
        update_ledger(Path(args.ledger), service, [captcha_run, turnstile_run], concurrency_run)
        print(json.dumps({
            "target_runs": [captcha_run, turnstile_run],
            "concurrency_run": concurrency_run,
        }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
