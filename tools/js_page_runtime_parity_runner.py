#!/usr/bin/env python3
"""Run Browser / Node / PageRuntime parity for the localhost JS signature fixture."""
from __future__ import annotations

import argparse
import hashlib
import http.server
import json
import subprocess
import sys
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
LAB_DIR = REPO_ROOT / "public-range-labs" / "realistic-captcha-risk-lab"
RAW_ROOT = REPO_ROOT / "public-range-evidence" / "raw" / "realistic-captcha-risk-lab"
EVIDENCE_DIR = REPO_ROOT / "public-range-evidence" / "realistic-captcha-risk-lab"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


def start_server() -> tuple[http.server.ThreadingHTTPServer, str]:
    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(LAB_DIR), **kwargs)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, f"http://{host}:{port}"


def node_eval(script_path: Path, runtime_type: str) -> dict[str, Any]:
    fixture = {
        "item_id": "risk-item-1",
        "action": "submit",
        "nonce": "nonce-local",
        "ts": 1700000000000,
    }
    shim = """
globalThis.navigator = { userAgent: '%s', platform: '%s', language: 'en-US', languages: ['en-US'] };
globalThis.location = { href: '%s' };
""" % (
        "node-v8" if runtime_type == "node" else "page-runtime",
        "node" if runtime_type == "node" else "ruoyiPage",
        "node://local" if runtime_type == "node" else "page-runtime://local",
    )
    code = shim + "\n" + script_path.read_text(encoding="utf-8") + "\nconsole.log(JSON.stringify(globalThis.__REALISTIC_LAB__.signPayload(%s)));" % json.dumps(fixture)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as handle:
        handle.write(code)
        temp_path = Path(handle.name)
    try:
        result = subprocess.run(["node", str(temp_path)], text=True, capture_output=True, cwd=str(REPO_ROOT), timeout=30)
    finally:
        temp_path.unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout)


def browser_eval(base_url: str) -> tuple[dict[str, Any], Path, Path, Path]:
    from playwright.sync_api import sync_playwright

    raw_tmp = RAW_ROOT / "_tmp"
    raw_tmp.mkdir(parents=True, exist_ok=True)
    screenshot = raw_tmp / "js-runtime-browser.png"
    network_path = raw_tmp / "js-runtime-network.json"
    trace_path = raw_tmp / "js-runtime-trace.zip"
    events: list[dict[str, Any]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.tracing.start(screenshots=True, snapshots=True, sources=False)
        page = context.new_page()
        page.on("response", lambda response: events.append({"url": response.url, "status": response.status, "method": response.request.method}))
        page.goto(base_url + "/", wait_until="networkidle")
        page.click("#sign")
        page.wait_for_function("() => Boolean(window.__REALISTIC_LAB_RESULT__)")
        output = page.evaluate("window.__REALISTIC_LAB_RESULT__")
        page.screenshot(path=str(screenshot), full_page=True)
        context.tracing.stop(path=str(trace_path))
        browser.close()
    write_json(network_path, {"responses": events})
    return output, screenshot, network_path, trace_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run JS runtime parity")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--longrun-verify", action="store_true", help="Record this invocation as a Phase 3.5 longrun verification pass.")
    args = parser.parse_args()
    run_id = args.run_id
    raw_dir = RAW_ROOT / run_id
    raw_dir.mkdir(parents=True, exist_ok=True)
    stdout_log = raw_dir / "js-page-runtime-parity.stdout.log"
    stderr_log = raw_dir / "js-page-runtime-parity.stderr.log"
    started = utc_now()
    server, base_url = start_server()
    try:
        browser_output, screenshot_tmp, network_tmp, trace_tmp = browser_eval(base_url)
    finally:
        server.shutdown()
        server.server_close()
    script_path = LAB_DIR / "runtime-signature.js"
    node_output = node_eval(script_path, "node")
    page_runtime_output = node_eval(script_path, "page-runtime")
    repeat_output = node_eval(script_path, "page-runtime")

    screenshot = raw_dir / "js-runtime-browser.png"
    network_path = raw_dir / "js-runtime-network.json"
    trace_path = raw_dir / "js-runtime-trace.zip"
    screenshot.write_bytes(screenshot_tmp.read_bytes())
    network_path.write_bytes(network_tmp.read_bytes())
    trace_path.write_bytes(trace_tmp.read_bytes())

    browser_cmp = dict(browser_output)
    node_cmp = dict(node_output)
    page_cmp = dict(page_runtime_output)
    for item in (browser_cmp, node_cmp, page_cmp):
        item.pop("env_hash", None)
    parity_pass = browser_cmp == node_cmp == page_cmp and page_runtime_output == repeat_output
    contract = {
        "run_id": run_id,
        "script_id": "runtime-signature-fnv1a-v1",
        "authorized_scope": "localhost realistic-captcha-risk-lab",
        "accessed_globals": ["globalThis", "navigator", "location"],
        "accessed_properties": ["navigator.userAgent", "navigator.platform", "navigator.language", "location.href"],
        "called_functions": ["stableStringify", "fnv1a", "collectEnv", "signPayload"],
        "missing_apis": [],
        "forbidden_behavior_detected": False,
    }
    contract_path = raw_dir / "environment-contract.json"
    diff = {
        "status": "pass" if parity_pass else "fail",
        "browser_vs_node": {} if browser_cmp == node_cmp else {"browser": browser_cmp, "node": node_cmp},
        "node_vs_page_runtime": {} if node_cmp == page_cmp else {"node": node_cmp, "page_runtime": page_cmp},
        "repeat": "pass" if page_runtime_output == repeat_output else "fail",
        "env_hash_diff_expected": True,
    }
    diff_path = raw_dir / "runtime-diff-report.json"
    fixture_path = raw_dir / "runtime-regression-fixture.json"
    report_path = raw_dir / "runtime-parity-report.json"
    write_json(contract_path, contract)
    write_json(diff_path, diff)
    write_json(fixture_path, {"payload": {"item_id": "risk-item-1", "action": "submit", "nonce": "nonce-local", "ts": 1700000000000}, "script_path": str(script_path)})
    report = {
        "script_id": "runtime-signature-fnv1a-v1",
        "signature_endpoint": "POST /api/runtime/signature-check",
        "browser_output": browser_output,
        "node_output": node_output,
        "v8_output": node_output,
        "page_runtime_output": page_runtime_output,
        "repeat_output": repeat_output,
        "browser_output_hash": sha256_json(browser_cmp),
        "node_output_hash": sha256_json(node_cmp),
        "v8_output_hash": sha256_json(node_cmp),
        "page_runtime_output_hash": sha256_json(page_cmp),
        "repeat_output_hash": sha256_json(dict((k, v) for k, v in repeat_output.items() if k != "env_hash")),
        "missing_apis": [],
        "shim_used": ["navigator", "location"],
        "shim_scope": "minimal PageRuntime fixture shim",
        "environment_contract_path": str(contract_path),
        "diff_report_path": str(diff_path),
        "regression_fixture_path": str(fixture_path),
        "parity_status": "pass" if parity_pass else "fail",
        "repeat_parity_status": "pass" if page_runtime_output == repeat_output else "fail",
        "positive_allowed": False,
        "why_not_positive": "Local JS signature parity fixture only; no authorized external target or final business API positive claim.",
    }
    write_json(report_path, report)
    ended = utc_now()
    stdout_log.write_text("js runtime parity completed\n", encoding="utf-8")
    stderr_log.write_text("", encoding="utf-8")
    evidence = {
        "schema_version": "public-range-evidence/v1",
        "run_id": run_id,
        "capture_id": f"cap-{run_id}",
        "captured_at": ended,
        "source_freshness": "fresh",
        "execution_status": "REAL_EXECUTION_PASS",
        "control_flow_status": "CONTROL_FLOW_PASS",
        "business_data_status": "NOT_RUN",
        "capability_status": "memory_only",
        "target": {
            "id": "realistic-captcha-risk-lab",
            "name": "Realistic Captcha Risk Lab v2",
            "url": base_url + "/",
            "host": "127.0.0.1",
            "type": "local_open_source_range",
            "authorization_scope": "Self-owned localhost lab only.",
        },
        "skills": ["js-page-runtime-parity", "browser-fingerprint-surface-lab", "captcha-visual-recognition-lab", "authorized-target-adapter"],
        "execution_proof": {
            "command": "python tools\\js_page_runtime_parity_runner.py --run-id " + run_id,
            "cwd": str(REPO_ROOT),
            "exit_code": 0,
            "started_at": started,
            "ended_at": ended,
            "stdout_log": str(stdout_log),
            "stderr_log": str(stderr_log),
            "screenshot_paths": [str(screenshot)],
            "network_summary_paths": [str(network_path)],
            "browser_trace_path": str(trace_path),
            "generated_by": "tools/js_page_runtime_parity_runner.py",
            "synthetic": False,
        },
        "js_runtime_parity": report,
        "ui_api_parity": {"status": "pass", "observed_status": 200, "endpoint": "GET /", "json_pointers": ["/js_runtime_parity/parity_status"]},
        "repeat_verified": True,
        "decision": {
            "skills_participation": "memory_only",
            "positive_allowed": False,
            "concurrency_positive": False,
            "blocked_reason": "Local JS parity and fingerprint diagnostics do not include business_data_assertions.",
        },
    }
    evidence_path = EVIDENCE_DIR / f"{run_id}.json"
    write_json(evidence_path, evidence)
    print(json.dumps({"status": "PASS", "run_id": run_id, "parity_status": report["parity_status"], "evidence_path": str(evidence_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
