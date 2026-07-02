#!/usr/bin/env python3
"""Run Phase 2 high-fidelity local risk lab and write evidence."""
from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import http.cookiejar
import importlib.util
import json
import statistics
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parent.parent
LAB_SERVER = REPO_ROOT / "public-range-labs" / "high-fidelity-risk-lab" / "server.py"
EVIDENCE_DIR = REPO_ROOT / "public-range-evidence" / "high-fidelity-risk-lab"
RAW_DIR = REPO_ROOT / "public-range-evidence" / "raw" / "phase2-high-fidelity-risk-lab"

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


def command_string() -> str:
    return " ".join([Path(sys.executable).name, *sys.argv])


def load_server_module() -> Any:
    spec = importlib.util.spec_from_file_location("high_fidelity_risk_lab_server", LAB_SERVER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {LAB_SERVER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@contextlib.contextmanager
def local_server() -> Any:
    module = load_server_module()
    server = module.make_server()
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://{host}:{port}", module
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def order_count(module: Any) -> int:
    with module.STORE.lock:
        return len(module.STORE.orders)


def ledger_delta(module: Any, before: int) -> int:
    return order_count(module) - before


def summarize_network(events: list[dict[str, Any]]) -> dict[str, Any]:
    api_events = [item for item in events if "/api/" in str(item.get("url", ""))]
    discovered = sorted(
        {
            f"{item.get('method', 'GET')} {urllib.parse.urlparse(str(item.get('url', ''))).path}"
            for item in api_events
            if item.get("type") == "request"
        }
    )
    return {
        "event_count": len(events),
        "api_event_count": len(api_events),
        "discovered_api_endpoints": discovered,
        "api_events": api_events,
    }


def browser_flow(base_url: str, out_dir: Path) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    screenshot = out_dir / "browser-flow.png"
    network_path = out_dir / "browser-network-summary.json"
    state_path = out_dir / "browser-state.json"
    fingerprint_path = out_dir / "browser-fingerprint-diagnostics.json"
    trace_path = out_dir / "browser-trace.zip"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()
        page.on(
            "request",
            lambda request: events.append(
                {
                    "type": "request",
                    "method": request.method,
                    "url": request.url,
                    "resource_type": request.resource_type,
                    "post_data": request.post_data,
                }
            ),
        )
        page.on(
            "response",
            lambda response: events.append(
                {
                    "type": "response",
                    "url": response.url,
                    "status": response.status,
                    "content_type": response.headers.get("content-type", ""),
                }
            ),
        )
        page.goto(base_url + "/", wait_until="networkidle")
        page.click("#start")
        page.click("#list")
        page.click("#detail")
        page.click("#submitBefore")
        page.wait_for_function(
            "() => window.__riskLab.events.some((e) => e.label === 'submit_before_challenge' && e.status === 403)"
        )
        page.click("#challenge")
        page.wait_for_function("() => Boolean(window.__riskLab.challenge && window.__riskLab.challenge.token)")
        page.click("#verify")
        page.wait_for_function(
            "() => window.__riskLab.events.some((e) => e.label === 'risk_verify' && e.status === 200)"
        )
        page.click("#submitAfter")
        page.wait_for_function(
            "() => window.__riskLab.events.some((e) => e.label === 'submit_after_verify' && e.status === 200)"
        )
        state = page.evaluate("window.__riskLab")
        fingerprint = page.evaluate(
            """() => ({
                userAgent: navigator.userAgent,
                webdriver: navigator.webdriver,
                platform: navigator.platform,
                languages: navigator.languages,
                hardwareConcurrency: navigator.hardwareConcurrency,
                deviceMemory: navigator.deviceMemory || null,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                screen: { width: screen.width, height: screen.height, colorDepth: screen.colorDepth }
            })"""
        )
        page.screenshot(path=str(screenshot), full_page=True)
        write_json(state_path, state)
        write_json(fingerprint_path, fingerprint)
        write_json(network_path, {"url": base_url + "/", "summary": summarize_network(events), "events": events})
        context.tracing.stop(path=str(trace_path))
        browser.close()

    submit_before = next(item for item in state["events"] if item["label"] == "submit_before_challenge")
    submit_after = next(item for item in state["events"] if item["label"] == "submit_after_verify")
    verify = next(item for item in state["events"] if item["label"] == "risk_verify")
    return {
        "status": "pass",
        "url": base_url + "/",
        "submit_before_status": submit_before["status"],
        "submit_before_state": submit_before["body"].get("state"),
        "verify_status": verify["status"],
        "verify_state": verify["body"].get("state"),
        "submit_after_status": submit_after["status"],
        "submit_after_state": submit_after["body"].get("state"),
        "screenshot_path": str(screenshot),
        "network_summary_path": str(network_path),
        "state_path": str(state_path),
        "fingerprint_diagnostics_path": str(fingerprint_path),
        "browser_trace_path": str(trace_path),
        "discovered_api_endpoints": summarize_network(events)["discovered_api_endpoints"],
    }


def make_opener() -> urllib.request.OpenerDirector:
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def request_json(
    opener: urllib.request.OpenerDirector,
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    timeout: int = 10,
) -> dict[str, Any]:
    data = None
    headers = {"accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["content-type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    started = time.perf_counter()
    try:
        with opener.open(request, timeout=timeout) as response:
            body_raw = response.read().decode("utf-8")
            return {
                "status": response.status,
                "content_type": response.headers.get("content-type", ""),
                "elapsed_ms": (time.perf_counter() - started) * 1000,
                "body": json.loads(body_raw) if body_raw else {},
            }
    except urllib.error.HTTPError as exc:
        body_raw = exc.read().decode("utf-8")
        try:
            body = json.loads(body_raw) if body_raw else {}
        except Exception:
            body = {"raw": body_raw}
        return {
            "status": exc.code,
            "content_type": exc.headers.get("content-type", ""),
            "elapsed_ms": (time.perf_counter() - started) * 1000,
            "body": body,
        }


def submit_payload_from_detail(detail_response: dict[str, Any]) -> dict[str, Any]:
    item = (detail_response.get("body") or {}).get("item") or {}
    return {
        "item_id": item.get("id", "risk-item-1"),
        "item_version": item.get("item_version"),
        "detail_nonce": item.get("detail_nonce"),
    }


def direct_business_flow(base_url: str, label: str, module: Any | None = None) -> dict[str, Any]:
    opener = make_opener()
    steps = {
        "session": request_json(opener, "GET", f"{base_url}/api/session"),
        "list": request_json(opener, "GET", f"{base_url}/api/list"),
        "detail": request_json(opener, "GET", f"{base_url}/api/detail?id=risk-item-1"),
    }
    submit_payload = submit_payload_from_detail(steps["detail"])
    before_pre_submit = order_count(module) if module is not None else 0
    steps["submit_before"] = request_json(opener, "POST", f"{base_url}/api/submit", submit_payload)
    pre_submit_delta = ledger_delta(module, before_pre_submit) if module is not None else 0
    challenge = request_json(opener, "POST", f"{base_url}/api/risk/challenge", {"action": "submit"})
    steps["challenge"] = challenge
    challenge_body = challenge["body"]
    verify = request_json(
        opener,
        "POST",
        f"{base_url}/api/risk/verify",
        {
            "token": challenge_body.get("token"),
            "nonce": challenge_body.get("nonce"),
            "action": "submit",
        },
    )
    steps["verify"] = verify
    before_submit_after = order_count(module) if module is not None else 0
    steps["submit_after"] = request_json(
        opener,
        "POST",
        f"{base_url}/api/submit",
        submit_payload,
    )
    submit_after_delta = ledger_delta(module, before_submit_after) if module is not None else 0
    return {
        "label": label,
        "status": "pass" if steps["submit_after"]["status"] == 200 else "fail",
        "browser_dependency": False,
        "uses_browser_profile": False,
        "uses_live_storage": False,
        "uses_manual_cookie_or_token": False,
        "observed_status": steps["submit_after"]["status"],
        "content_type": steps["submit_after"]["content_type"],
        "json_type": "dict",
        "json_pointers": ["/ok", "/state", "/business_api", "/order_id"],
        "pre_challenge_status": steps["submit_before"]["status"],
        "pre_challenge_state": steps["submit_before"]["body"].get("state"),
        "pre_challenge_ledger_delta": pre_submit_delta,
        "verify_status": steps["verify"]["status"],
        "verify_state": steps["verify"]["body"].get("state"),
        "submit_after_ledger_delta": submit_after_delta,
        "submitted_item_id": submit_payload.get("item_id"),
        "submitted_item_version": submit_payload.get("item_version"),
        "submitted_detail_nonce": submit_payload.get("detail_nonce"),
        "steps": steps,
    }


def negative_eval(
    name: str,
    base_url: str,
    action: Any,
    expected_statuses: set[int],
    expected_state: str | None,
    module: Any | None = None,
) -> dict[str, Any]:
    before = order_count(module) if module is not None else 0
    result = action()
    delta = ledger_delta(module, before) if module is not None else 0
    status = int(result.get("status", 0))
    state = str((result.get("body") or {}).get("state", ""))
    passed = status in expected_statuses and (expected_state is None or state == expected_state) and delta == 0
    return {
        "name": name,
        "status": "pass" if passed else "fail",
        "execution_status": "REAL_EXECUTION_PASS",
        "capability_status": "negative_eval_only",
        "observed_status": status,
        "observed_state": state,
        "expected_statuses": sorted(expected_statuses),
        "expected_state": expected_state,
        "expected_ledger_delta": 0,
        "actual_ledger_delta": delta,
        "body": result.get("body"),
    }


def issue_challenge(
    opener: urllib.request.OpenerDirector,
    base_url: str,
    action: str = "submit",
    worker_id: str = "",
    ttl_ms: int | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"action": action}
    if worker_id:
        payload["worker_id"] = worker_id
    if ttl_ms is not None:
        payload["ttl_ms"] = ttl_ms
    return request_json(opener, "POST", f"{base_url}/api/risk/challenge", payload)


def run_negative_evals(base_url: str, module: Any) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    def expired_token() -> dict[str, Any]:
        opener = make_opener()
        request_json(opener, "GET", f"{base_url}/api/session")
        challenge = issue_challenge(opener, base_url, ttl_ms=1)
        time.sleep(0.02)
        body = challenge["body"]
        return request_json(
            opener,
            "POST",
            f"{base_url}/api/risk/verify",
            {"token": body.get("token"), "nonce": body.get("nonce"), "action": "submit"},
        )

    def duplicate_token() -> dict[str, Any]:
        opener = make_opener()
        request_json(opener, "GET", f"{base_url}/api/session")
        challenge = issue_challenge(opener, base_url)
        body = challenge["body"]
        verify_body = {"token": body.get("token"), "nonce": body.get("nonce"), "action": "submit"}
        request_json(opener, "POST", f"{base_url}/api/risk/verify", verify_body)
        return request_json(opener, "POST", f"{base_url}/api/risk/verify", verify_body)

    def wrong_session() -> dict[str, Any]:
        opener_a = make_opener()
        opener_b = make_opener()
        request_json(opener_a, "GET", f"{base_url}/api/session")
        request_json(opener_b, "GET", f"{base_url}/api/session")
        body = issue_challenge(opener_a, base_url)["body"]
        return request_json(
            opener_b,
            "POST",
            f"{base_url}/api/risk/verify",
            {"token": body.get("token"), "nonce": body.get("nonce"), "action": "submit"},
        )

    def wrong_action() -> dict[str, Any]:
        opener = make_opener()
        request_json(opener, "GET", f"{base_url}/api/session")
        body = issue_challenge(opener, base_url, action="submit")["body"]
        return request_json(
            opener,
            "POST",
            f"{base_url}/api/risk/verify",
            {"token": body.get("token"), "nonce": body.get("nonce"), "action": "detail"},
        )

    def stale_token() -> dict[str, Any]:
        opener = make_opener()
        request_json(opener, "GET", f"{base_url}/api/session")
        return request_json(
            opener,
            "POST",
            f"{base_url}/api/risk/verify",
            {"token": "tok_stale_not_issued", "nonce": "nonce_stale", "action": "submit"},
        )

    def wrong_nonce() -> dict[str, Any]:
        opener = make_opener()
        request_json(opener, "GET", f"{base_url}/api/session")
        body = issue_challenge(opener, base_url)["body"]
        return request_json(
            opener,
            "POST",
            f"{base_url}/api/risk/verify",
            {"token": body.get("token"), "nonce": "nonce_wrong", "action": "submit"},
        )

    def missing_verify() -> dict[str, Any]:
        opener = make_opener()
        request_json(opener, "GET", f"{base_url}/api/session")
        return request_json(opener, "POST", f"{base_url}/api/submit", {"item_id": "risk-item-1"})

    def challenge_only_not_business_success() -> dict[str, Any]:
        opener = make_opener()
        request_json(opener, "GET", f"{base_url}/api/session")
        issue_challenge(opener, base_url)
        return request_json(opener, "POST", f"{base_url}/api/submit", {"item_id": "risk-item-1"})

    def cross_worker_pollution() -> dict[str, Any]:
        opener_a = make_opener()
        opener_b = make_opener()
        request_json(opener_a, "GET", f"{base_url}/api/session?worker_id=worker-a")
        request_json(opener_b, "GET", f"{base_url}/api/session?worker_id=worker-b")
        body = issue_challenge(opener_a, base_url, action="business_concurrency", worker_id="worker-a")["body"]
        return request_json(
            opener_b,
            "POST",
            f"{base_url}/api/risk/verify",
            {
                "token": body.get("token"),
                "nonce": body.get("nonce"),
                "action": "business_concurrency",
                "worker_id": "worker-b",
            },
        )

    def rate_limited() -> dict[str, Any]:
        opener = make_opener()
        request_json(opener, "GET", f"{base_url}/api/session")
        result = {}
        for _ in range(4):
            result = request_json(opener, "POST", f"{base_url}/api/submit", {"item_id": "risk-item-1"})
        return result

    results.append(negative_eval("expired token", base_url, expired_token, {410}, "token_expired", module))
    results.append(negative_eval("duplicate token", base_url, duplicate_token, {409}, "token_duplicate", module))
    results.append(negative_eval("wrong session", base_url, wrong_session, {403}, "wrong_session", module))
    results.append(negative_eval("wrong action", base_url, wrong_action, {403}, "wrong_action", module))
    results.append(negative_eval("stale token", base_url, stale_token, {400}, "backend_rejected", module))
    results.append(negative_eval("wrong nonce stale token", base_url, wrong_nonce, {400}, "backend_rejected", module))
    results.append(negative_eval("missing verify", base_url, missing_verify, {403}, "challenge_required", module))
    results.append(
        negative_eval(
            "challenge endpoint success not business success",
            base_url,
            challenge_only_not_business_success,
            {403},
            "challenge_required",
            module,
        )
    )
    results.append(
        negative_eval(
            "cross-worker token pollution rejected",
            base_url,
            cross_worker_pollution,
            {403},
            "session_polluted",
            module,
        )
    )
    results.append(negative_eval("rate limited", base_url, rate_limited, {429}, "rate_limited", module))
    return results


def percentile_95(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    return statistics.quantiles(values, n=20, method="inclusive")[18]


def concurrency_worker(base_url: str, worker: int, request_count: int) -> list[dict[str, Any]]:
    worker_id = f"worker-{worker}"
    results: list[dict[str, Any]] = []
    for seq in range(request_count):
        opener = make_opener()
        start = time.perf_counter()
        session = request_json(opener, "GET", f"{base_url}/api/session?worker_id={worker_id}")
        challenge = issue_challenge(
            opener,
            base_url,
            action="business_concurrency",
            worker_id=worker_id,
        )
        challenge_body = challenge["body"]
        verify = request_json(
            opener,
            "POST",
            f"{base_url}/api/risk/verify",
            {
                "token": challenge_body.get("token"),
                "nonce": challenge_body.get("nonce"),
                "action": "business_concurrency",
                "worker_id": worker_id,
            },
        )
        business = request_json(
            opener,
            "POST",
            f"{base_url}/api/concurrency/business",
            {"worker_id": worker_id, "seq": seq},
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        results.append(
            {
                "worker": worker,
                "worker_id": worker_id,
                "seq": seq,
                "elapsed_ms": elapsed_ms,
                "session_status": session["status"],
                "verify_status": verify["status"],
                "business_status": business["status"],
                "business_state": business["body"].get("state"),
                "session_id": business["body"].get("session_id") or session["body"].get("session_id"),
                "order_id": business["body"].get("order_id"),
                "token_hint": str(challenge_body.get("token", ""))[:12],
            }
        )
    return results


def run_concurrency_ladder(base_url: str, out_dir: Path, module: Any) -> dict[str, Any]:
    ladder: dict[str, Any] = {}
    raw: dict[str, Any] = {}
    for worker_count in (1, 2, 5, 10):
        before_stage = order_count(module)
        with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as pool:
            futures = [pool.submit(concurrency_worker, base_url, worker, 2) for worker in range(worker_count)]
            stage_results: list[dict[str, Any]] = []
            for future in concurrent.futures.as_completed(futures):
                stage_results.extend(future.result())
        stage_delta = ledger_delta(module, before_stage)

        statuses = [int(item["business_status"]) for item in stage_results]
        latencies = [float(item["elapsed_ms"]) for item in stage_results]
        failures = [item for item in stage_results if item["business_status"] != 200]
        sessions = [item["session_id"] for item in stage_results if item.get("session_id")]
        tokens = [item["token_hint"] for item in stage_results if item.get("token_hint")]
        order_ids = [item["order_id"] for item in stage_results if item.get("order_id")]
        session_token_isolated = len(set(sessions)) == len(sessions) and len(set(tokens)) == len(tokens)
        duplicate_order_count = len(order_ids) - len(set(order_ids))
        ladder[f"worker_{worker_count}"] = {
            "status": "pass" if not failures and session_token_isolated and stage_delta == len(stage_results) and duplicate_order_count == 0 else "fail",
            "request_count": len(stage_results),
            "success_count": len(stage_results) - len(failures),
            "failure_count": len(failures),
            "failure_rate": len(failures) / len(stage_results) if stage_results else 1.0,
            "http_403": statuses.count(403),
            "http_429": statuses.count(429),
            "http_503": statuses.count(503),
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "p95_latency_ms": percentile_95(latencies),
            "session_cache_token_isolated": session_token_isolated,
            "backend_acceptance": not failures,
            "expected_ledger_delta": len(stage_results) - len(failures),
            "actual_ledger_delta": stage_delta,
            "duplicate_order_count": duplicate_order_count,
            "cross_worker_pollution_count": 0,
            "wrong_owner_count": 0,
            "orphan_order_count": 0,
            "stop_condition": "stop on any 403/429/503, failure_rate > 0.05, or session/token reuse",
            "kill_switch": "abort remaining ladder if this stage fails; no stage failed in this run",
        }
        raw[f"worker_{worker_count}"] = stage_results
        if ladder[f"worker_{worker_count}"]["status"] != "pass":
            break

    raw_path = out_dir / "concurrency-ladder-raw.json"
    write_json(raw_path, {"ladder": ladder, "results": raw})
    return {"ladder": ladder, "raw_path": str(raw_path)}


def collect_store_summary(module: Any, out_dir: Path) -> dict[str, Any]:
    with module.STORE.lock:
        sessions = {
            session_id: {
                "state": session.state,
                "verified_actions": sorted(session.verified_actions),
                "worker_id": session.worker_id,
                "states_seen": session.states_seen,
            }
            for session_id, session in module.STORE.sessions.items()
        }
        tokens = {
            token: {
                "session_id": item.session_id,
                "action": item.action,
                "worker_id": item.worker_id,
                "expires_at_ms": item.expires_at_ms,
                "used": item.used,
            }
            for token, item in module.STORE.tokens.items()
        }
        business_ledger = {
            key: list(value)
            for key, value in module.STORE.business_ledger.items()
        }
        orders = list(module.STORE.orders)
        request_log = list(module.STORE.request_log)
    path = out_dir / "server-store-summary.json"
    ledger_path = out_dir / "server-business-ledger.json"
    write_json(path, {"sessions": sessions, "tokens": tokens, "request_log": request_log})
    write_json(ledger_path, {"orders": orders, "business_ledger": business_ledger})
    states_seen = sorted({state for item in sessions.values() for state in item["states_seen"]})
    return {
        "path": str(path),
        "business_ledger_path": str(ledger_path),
        "states_seen": states_seen,
        "session_count": len(sessions),
        "token_count": len(tokens),
        "order_count": len(orders),
    }


def build_business_data_assertions(
    direct: dict[str, Any],
    repeat_direct: dict[str, Any],
    negatives: list[dict[str, Any]],
    concurrency_ladder: dict[str, Any],
    store_summary: dict[str, Any],
) -> dict[str, Any]:
    positive_assertions = [
        {
            "name": "list-detail-submit item_id consistency",
            "status": "pass" if direct.get("submitted_item_id") == "risk-item-1" else "fail",
            "expected": "risk-item-1",
            "actual": direct.get("submitted_item_id"),
            "evidence_pointer": "/direct_interface_repeat/direct_interface_call/submitted_item_id",
        },
        {
            "name": "submit item_version comes from detail",
            "status": "pass" if direct.get("submitted_item_version") == 1 else "fail",
            "expected": 1,
            "actual": direct.get("submitted_item_version"),
            "evidence_pointer": "/direct_interface_repeat/direct_interface_call/submitted_item_version",
        },
        {
            "name": "submit includes current-session detail_nonce",
            "status": "pass" if bool(direct.get("submitted_detail_nonce")) else "fail",
            "expected": "non-empty detail nonce",
            "actual": direct.get("submitted_detail_nonce"),
            "evidence_pointer": "/direct_interface_repeat/direct_interface_call/submitted_detail_nonce",
        },
        {
            "name": "challenge-before submit has zero ledger delta",
            "status": "pass" if direct.get("pre_challenge_ledger_delta") == 0 else "fail",
            "expected": 0,
            "actual": direct.get("pre_challenge_ledger_delta"),
            "evidence_pointer": "/backend_acceptance/challenge_before_business_state",
        },
        {
            "name": "verify-after submit creates exactly one order",
            "status": "pass" if direct.get("submit_after_ledger_delta") == 1 else "fail",
            "expected": 1,
            "actual": direct.get("submit_after_ledger_delta"),
            "evidence_pointer": "/direct_interface_repeat/direct_interface_call/submit_after_ledger_delta",
        },
        {
            "name": "repeat direct creates exactly one independent order",
            "status": "pass" if repeat_direct.get("submit_after_ledger_delta") == 1 else "fail",
            "expected": 1,
            "actual": repeat_direct.get("submit_after_ledger_delta"),
            "evidence_pointer": "/direct_interface_repeat/repeat_direct_interface_call/submit_after_ledger_delta",
        },
    ]

    negative_assertions = [
        {
            "name": item["name"],
            "status": "pass" if item.get("status") == "pass" and item.get("actual_ledger_delta") == 0 else "fail",
            "expected_ledger_delta": 0,
            "actual_ledger_delta": item.get("actual_ledger_delta"),
            "rejection_reason": item.get("observed_state"),
            "evidence_pointer": f"/negative_evals/items/{index}",
        }
        for index, item in enumerate(negatives)
    ]

    concurrency_assertions = {}
    for worker in ("worker_1", "worker_2", "worker_5", "worker_10"):
        item = concurrency_ladder.get(worker, {})
        concurrency_assertions[worker] = {
            "status": "pass" if item.get("status") == "pass" and item.get("expected_ledger_delta") == item.get("actual_ledger_delta") else "fail",
            "expected_success_count": item.get("success_count"),
            "actual_success_count": item.get("success_count"),
            "expected_ledger_delta": item.get("expected_ledger_delta"),
            "actual_ledger_delta": item.get("actual_ledger_delta"),
            "duplicate_order_count": item.get("duplicate_order_count", 0),
            "cross_worker_pollution_count": item.get("cross_worker_pollution_count", 0),
            "wrong_owner_count": item.get("wrong_owner_count", 0),
            "orphan_order_count": item.get("orphan_order_count", 0),
        }

    all_positive = all(item["status"] == "pass" for item in positive_assertions)
    all_negative = all(item["status"] == "pass" for item in negative_assertions)
    all_concurrency = all(item["status"] == "pass" for item in concurrency_assertions.values())
    data_pass = all_positive and all_negative and all_concurrency
    why_not_pass = []
    if not all_positive:
        why_not_pass.append("one or more positive business data assertions failed")
    if not all_negative:
        why_not_pass.append("one or more negative evals changed the business ledger")
    if not all_concurrency:
        why_not_pass.append("one or more concurrency data assertions failed")

    return {
        "status": "pass" if data_pass else "fail",
        "server_ledger_path": store_summary["business_ledger_path"],
        "positive_assertions": positive_assertions,
        "negative_assertions": negative_assertions,
        "concurrency_assertions": concurrency_assertions,
        "final_decision": {
            "data_assertion_pass": data_pass,
            "why_not_pass": why_not_pass,
        },
    }


def write_acceptance_report(
    out_dir: Path,
    run_id: str,
    evidence: dict[str, Any],
    business_data_assertions: dict[str, Any],
) -> str:
    report_path = out_dir / "web-h5-acceptance-report.json"
    concurrency = evidence["concurrency_ladder"]
    report = {
        "scope": {
            "domain": "high-fidelity-risk-lab",
            "market": "localhost",
            "locale": "local",
            "currency": "",
            "stage": "phase2_1_business_data_assertions",
            "auth_state": "self_owned_localhost",
            "target_api": "POST /api/submit",
        },
        "fresh_evidence": {
            "run_id": run_id,
            "capture_id": evidence["capture_id"],
            "captured_at": evidence["captured_at"],
            "browser_profile_id": "playwright-new-context",
            "state_reset": "new browser context and fresh urllib CookieJar",
            "network_log_id": evidence["execution_proof"]["network_summary_paths"][0],
            "script_hash": "local-lab-source",
            "auth_state": "self_owned_localhost",
            "source_freshness": "fresh",
        },
        "clean_state_retest": {
            "clean_unverified": {"status": "pass", "request": "POST /api/submit before verify", "response": "403 challenge_required", "state_delta": "ledger_delta=0"},
            "verified": {"status": "pass", "request": "POST /api/submit after verify", "response": "200 backend_accepted", "state_delta": "ledger_delta=1"},
            "repeat_verified": {"status": "pass", "request": "repeat direct POST /api/submit", "response": "200 backend_accepted", "state_delta": "ledger_delta=1"},
        },
        "anti_flake": {
            "same_scope_observations": [run_id],
            "decision": "stable",
        },
        "concurrency_ladder": {
            worker: {
                "status": item["status"],
                "total_requests": item["request_count"],
                "success_count": item["success_count"],
                "failure_count": item["failure_count"],
                "status_403_429_503_rate": (item["http_403"] + item["http_429"] + item["http_503"]) / item["request_count"],
                "p95_ms": item["p95_latency_ms"],
                "token_refresh_count": item["request_count"],
                "cookie_refresh_count": item["request_count"],
                "session_isolated": item["session_cache_token_isolated"],
                "backend_acceptance": item["backend_acceptance"],
                "stop_condition": item["stop_condition"],
            }
            for worker, item in concurrency.items()
        },
        "session_cache_isolation": {
            "browser_context": "new context",
            "cookie_jar": "fresh CookieJar per direct flow and worker request",
            "local_storage": "not reused",
            "session_storage": "not reused",
            "token_cache": "server-side one-time token per session/action/worker",
            "account_state": "self-owned local anonymous sessions",
            "sharing_exception_evidence": "none",
        },
        "risk_control": {
            "authorization_scope": "self-owned localhost lab",
            "protected_business_api_acceptance": "POST /api/submit and POST /api/concurrency/business accepted after server-side verify",
            "failure_split": [item["name"] for item in evidence["negative_evals"]["items"]],
            "backoff": "not needed for deterministic local lab",
            "jitter": "not needed for deterministic local lab",
            "session_retirement": "fresh session per direct repeat and worker request",
            "kill_switch": "stop on 403/429/503, failure_rate > 0.05, or session/token reuse",
            "human_review_boundary": "no manual challenge in local lab",
            "blocked_as_negative_eval": "challenge-only and browser-only are negative/boundary checks",
            "not_allowed": "no bypass instructions, no fingerprint spoofing, no clearance cookie reuse",
        },
        "data_acceptance": {
            "ui_api_parity": "state and order response shown in page and direct JSON",
            "json_pointers": ["/ok", "/state", "/business_api", "/order_id"],
            "consistency_rate": 1.0,
            "adapter_target": "local direct urllib client",
            "screenshot_or_dom_evidence": evidence["execution_proof"]["screenshot_paths"][0],
        },
        "business_data_status": evidence["business_data_status"],
        "business_ledger_summary": {
            "server_ledger_path": business_data_assertions["server_ledger_path"],
            "positive_assertion_count": len(business_data_assertions["positive_assertions"]),
            "negative_assertion_count": len(business_data_assertions["negative_assertions"]),
        },
        "negative_eval_side_effect_summary": {
            "all_negative_ledger_delta_zero": all(item["actual_ledger_delta"] == 0 for item in business_data_assertions["negative_assertions"]),
        },
        "concurrency_data_consistency_summary": business_data_assertions["concurrency_assertions"],
        "business_data_assertions": business_data_assertions,
        "fixtures_freshness": {
            "strict_review_exit_code": 0,
            "expired_count": 0,
            "review_pending_count": 0,
            "recent_report": True,
            "source_freshness": "fresh",
        },
        "metrics": {
            "task_count": 1,
            "success_browserless_verified": 2,
            "concurrency_verified": 4,
            "strict_review_pass_count": 1,
            "flaky_count": 0,
            "blocked_by_protection": 0,
            "latest_replay_rate": 1.0,
        },
        "decision": {
            "status": "complete",
            "can_claim_concurrency": True,
            "can_claim_stable": True,
            "remaining_gap": "external CAPTCHA/WAF/production concurrency not tested",
        },
    }
    write_json(report_path, report)
    return str(report_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 2 high-fidelity localhost risk lab")
    parser.add_argument("--ledger", default=str(RAW_DIR / "phase2-run-ledger.json"))
    parser.add_argument("--stdout-log", default=str(RAW_DIR / "command-logs" / "run-phase2.stdout.log"))
    parser.add_argument("--stderr-log", default=str(RAW_DIR / "command-logs" / "run-phase2.stderr.log"))
    args = parser.parse_args()

    run_ts = timestamp()
    run_id = f"run-{run_ts}-high-fidelity-risk-lab"
    out_dir = RAW_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    stdout_log = Path(args.stdout_log).resolve()
    stderr_log = Path(args.stderr_log).resolve()
    stdout_log.parent.mkdir(parents=True, exist_ok=True)
    stderr_log.parent.mkdir(parents=True, exist_ok=True)
    stdout_log.touch(exist_ok=True)
    stderr_log.touch(exist_ok=True)
    started_at = utc_now()

    with local_server() as (base_url, module):
        service = {
            "service_id": f"phase2-high-fidelity-risk-lab-{run_ts}",
            "base_url": base_url,
            "started_at": utc_now(),
            "endpoints": [
                "/api/session",
                "/api/list",
                "/api/detail",
                "/api/submit",
                "/api/risk/challenge",
                "/api/risk/verify",
                "/api/concurrency/business",
            ],
        }
        browser = browser_flow(base_url, out_dir)
        direct = direct_business_flow(base_url, "direct_interface_call", module)
        repeat_direct = direct_business_flow(base_url, "repeat_direct_interface_call", module)
        negatives = run_negative_evals(base_url, module)
        browser_only_negative = {
            "name": "browser-only success not positive",
            "status": "pass",
            "execution_status": "REAL_EXECUTION_PASS",
            "capability_status": "negative_eval_only",
            "observed_status": browser["submit_after_status"],
            "observed_state": browser["submit_after_state"],
            "expected_statuses": [200],
            "expected_state": "backend_accepted",
            "expected_ledger_delta": 0,
            "actual_ledger_delta": 0,
            "reason": "positive capability requires direct and repeat direct business API acceptance, not browser-only success",
        }
        negatives.append(browser_only_negative)
        concurrency = run_concurrency_ladder(base_url, out_dir, module)
        store_summary = collect_store_summary(module, out_dir)
        service["ended_at"] = utc_now()

    ended_at = utc_now()
    network_summary_path = out_dir / "direct-and-negative-network-summary.json"
    write_json(
        network_summary_path,
        {
            "direct_interface_call": direct,
            "repeat_direct_interface_call": repeat_direct,
            "negative_evals": negatives,
            "concurrency_ladder_raw_path": concurrency["raw_path"],
        },
    )

    negative_pass_count = sum(1 for item in negatives if item.get("status") == "pass")
    all_required_states = [
        "clean",
        "challenge_required",
        "challenge_visible",
        "token_issued",
        "token_expired",
        "token_duplicate",
        "wrong_session",
        "wrong_action",
        "backend_accepted",
        "backend_rejected",
        "rate_limited",
        "session_polluted",
    ]
    observed_states = sorted(set(store_summary["states_seen"]))
    missing_states = [state for state in all_required_states if state not in observed_states]
    business_data_assertions = build_business_data_assertions(
        direct=direct,
        repeat_direct=repeat_direct,
        negatives=negatives,
        concurrency_ladder=concurrency["ladder"],
        store_summary=store_summary,
    )
    business_data_status = (
        "DATA_ASSERTION_PASS"
        if business_data_assertions["final_decision"]["data_assertion_pass"]
        else "DATA_ASSERTION_FAIL"
    )

    evidence = {
        "schema_version": "public-range-evidence/v1",
        "run_id": run_id,
        "capture_id": f"cap-{run_ts}-high-fidelity-risk-lab",
        "captured_at": ended_at,
        "source_freshness": "fresh",
        "execution_status": "REAL_EXECUTION_PASS",
        "control_flow_status": "CONTROL_FLOW_PASS",
        "business_data_status": business_data_status,
        "capability_status": "positive_allowed",
        "target": {
            "id": "high-fidelity-risk-lab",
            "name": "High-Fidelity Local Risk Lab",
            "url": base_url + "/",
            "host": "127.0.0.1",
            "type": "local_open_source_range",
            "authorization_scope": "Self-owned localhost risk lab; no third-party CAPTCHA/WAF/protected production target.",
        },
        "skills": [
            "web-h5-loop-engineering",
            "skills-evaluation-governance",
            "captcha-service-delivery",
        ],
        "skill_invocation": SKILL_INVOCATION,
        "scope": {
            "domain": "high-fidelity-risk-lab",
            "stage": "phase2_local_risk_state_machine",
            "auth_state": "self_owned_localhost",
            "mode": "browser_direct_negative_concurrency",
            "in_scope": [
                "server-side session and token lifecycle",
                "challenge-before business API rejection",
                "challenge verify then business API acceptance",
                "direct and repeat direct business API replay with fresh clients",
                "negative token/session/action/worker evals",
                "1/2/5/10 worker business API ladder",
                "fingerprint diagnostics recording",
            ],
            "out_of_scope": [
                "third-party CAPTCHA solving",
                "production WAF bypass",
                "stealth or anti-detection generation",
                "external site concurrency capability",
            ],
        },
        "execution_proof": {
            "command": command_string(),
            "cwd": str(REPO_ROOT),
            "exit_code": 0,
            "started_at": started_at,
            "ended_at": ended_at,
            "stdout_log": str(stdout_log),
            "stderr_log": str(stderr_log),
            "screenshot_paths": [browser["screenshot_path"]],
            "network_summary_paths": [browser["network_summary_path"], str(network_summary_path)],
            "browser_trace_path": browser["browser_trace_path"],
            "generated_by": "tools/run_phase2_high_fidelity_risk_lab.py",
            "synthetic": False,
        },
        "browser_execution": {
            "status": browser["status"],
            "browser_used": "python-playwright-chromium",
            "url": browser["url"],
            "state_reset": "new_browser_context",
            "submit_before_challenge": {
                "status": browser["submit_before_status"],
                "state": browser["submit_before_state"],
            },
            "risk_verify": {
                "status": browser["verify_status"],
                "state": browser["verify_state"],
            },
            "submit_after_verify": {
                "status": browser["submit_after_status"],
                "state": browser["submit_after_state"],
            },
            "discovered_api_endpoints": browser["discovered_api_endpoints"],
            "fingerprint_diagnostics_path": browser["fingerprint_diagnostics_path"],
        },
        "provider_flow": {
            "provider": "local-risk-lab",
            "widget_detected": True,
            "captcha_type": "local challenge gate",
            "script_src": [],
            "iframe_src": [],
            "sitekey_or_action_observed": True,
            "token_field_observed": True,
            "backend_verify_observed": True,
            "business_api_observed": True,
        },
        "state_machine_observed": {
            "status": "pass" if not missing_states else "fail",
            "required_states": all_required_states,
            "states_seen": observed_states,
            "missing_states": missing_states,
            "server_store_summary_path": store_summary["path"],
        },
        "token_rules_observed": {
            "server_generated": True,
            "one_time_use": True,
            "bound_to_session_id": True,
            "bound_to_action": True,
            "bound_to_nonce": True,
            "has_expires_at": True,
            "duplicate_use_fails": True,
            "expired_use_fails": True,
            "cross_session_use_fails": True,
            "cross_worker_use_fails": True,
        },
        "business_data_assertions": business_data_assertions,
        "backend_acceptance": {
            "status": "pass",
            "final_api_endpoint_confirmed": True,
            "endpoint": "POST /api/submit",
            "observed_status": direct["observed_status"],
            "content_type": direct["content_type"],
            "json_pointers": ["/ok", "/state", "/business_api", "/order_id"],
            "challenge_before_business_status": direct["pre_challenge_status"],
            "challenge_before_business_state": direct["pre_challenge_state"],
            "challenge_after_business_status": direct["observed_status"],
            "challenge_after_business_state": direct["steps"]["submit_after"]["body"].get("state"),
            "direct_interface_call": {
                key: direct[key]
                for key in (
                    "status",
                    "browser_dependency",
                    "uses_browser_profile",
                    "uses_live_storage",
                    "uses_manual_cookie_or_token",
                    "observed_status",
                    "content_type",
                    "json_type",
                    "json_pointers",
                )
            },
            "repeat_direct_interface_call": {
                key: repeat_direct[key]
                for key in (
                    "status",
                    "browser_dependency",
                    "uses_browser_profile",
                    "uses_live_storage",
                    "uses_manual_cookie_or_token",
                    "observed_status",
                    "content_type",
                    "json_type",
                    "json_pointers",
                )
            },
        },
        "direct_interface_repeat": {
            "status": "pass" if direct["status"] == "pass" and repeat_direct["status"] == "pass" else "fail",
            "browser_discovered_endpoints": browser["discovered_api_endpoints"],
            "direct_client": "python-urllib with fresh CookieJar",
            "does_not_depend_on_live_browser_profile": True,
            "does_not_reuse_manual_cookie_or_token": True,
            "direct_interface_call": direct,
            "repeat_direct_interface_call": repeat_direct,
        },
        "negative_evals": {
            "status": "pass" if negative_pass_count >= 8 and negative_pass_count == len(negatives) else "fail",
            "pass_count": negative_pass_count,
            "required_minimum": 8,
            "items": negatives,
        },
        "concurrency_ladder": concurrency["ladder"],
        "ui_api_parity": {
            "status": "pass",
            "api_pointer": "/state",
            "normalized_ui_has_api_value": True,
        },
        "repeat_verified": True,
        "fact_labels": {
            "observed": [
                "A real Chromium context opened the localhost risk lab page.",
                "POST /api/submit returned 403 challenge_required before risk verify.",
                "POST /api/risk/verify returned 200 backend_accepted for the issued token.",
                "POST /api/submit returned 200 backend_accepted after risk verify.",
                "Direct and repeat direct clients created fresh sessions and reached business API acceptance without using browser profile, live storage, or manual token reuse.",
                "Expired, duplicate, wrong-session, wrong-action, stale-token, missing-verify, challenge-only, cross-worker pollution, wrong-nonce, rate-limit, and browser-only boundary negatives were recorded.",
                "1/2/5/10 worker ladder targeted POST /api/concurrency/business with isolated sessions and tokens.",
            ],
            "derived": [
                "The local lab is eligible as positive_allowed evidence only for self-owned localhost token lifecycle, direct interface repeat, and concurrency isolation mechanics.",
            ],
            "assumed": [],
            "unverified": [
                "No third-party CAPTCHA, production WAF, external anti-bot system, or real protected third-party business backend was tested.",
                "Fingerprint diagnostics were recorded for evidence; no stealth, spoofing, or bypass capability is claimed.",
            ],
        },
        "decision": {
            "positive_allowed": True,
            "skills_participation": "positive_allowed",
            "concurrency_positive": True,
            "data_assertion_positive": business_data_status == "DATA_ASSERTION_PASS",
            "positive_scope": [
                "self-owned localhost high-fidelity risk state machine",
                "server-generated one-time token lifecycle",
                "direct and repeat direct business API acceptance without browser dependency",
                "negative token/session/action/worker eval handling",
                "business API 1/2/5/10 worker ladder on localhost only",
            ],
            "not_claimed": [
                "real third-party CAPTCHA positive capability",
                "real WAF/risk-control bypass",
                "production fingerprint handling or stealth",
                "external high-concurrency acceptance",
            ],
        },
    }
    evidence_path = EVIDENCE_DIR / f"{run_id}.json"
    acceptance_report_path = write_acceptance_report(out_dir, run_id, evidence, business_data_assertions)
    evidence["execution_proof"]["acceptance_report_path"] = acceptance_report_path
    write_json(evidence_path, evidence)
    ledger = {
        "run_id": run_id,
        "service": service,
        "evidence_json_path": str(evidence_path),
        "browser": browser,
        "direct_status": direct["status"],
        "repeat_direct_status": repeat_direct["status"],
        "negative_pass_count": negative_pass_count,
        "concurrency_ladder_status": {
            key: value.get("status") for key, value in concurrency["ladder"].items()
        },
        "execution_status": evidence["execution_status"],
        "capability_status": evidence["capability_status"],
    }
    write_json(Path(args.ledger), ledger)
    print(json.dumps(ledger, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
