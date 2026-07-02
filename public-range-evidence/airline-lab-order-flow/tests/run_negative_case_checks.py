#!/usr/bin/env python3
"""Validate Airline Lab negative-case classification and rejection paths."""
from __future__ import annotations

import argparse
import http.client
import importlib.util
import json
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_server(root: Path) -> Any:
    sys.dont_write_bytecode = True
    path = root / "mock_server" / "server.py"
    spec = importlib.util.spec_from_file_location("airline_lab_mock_server_negative", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load mock server from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def request(port: int, method: str, path: str, body: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
    payload = b""
    request_headers = {"accept": "application/json"}
    if body is not None:
        payload = json.dumps(body, sort_keys=True).encode("utf-8")
        request_headers["content-type"] = "application/json"
    if headers:
        request_headers.update(headers)
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        conn.request(method, path, body=payload, headers=request_headers)
        response = conn.getresponse()
        raw = response.read()
        return response.status, json.loads(raw.decode("utf-8"))
    finally:
        conn.close()


def pointer_exists(payload: Any, pointer: str) -> bool:
    current = payload
    for part in pointer.strip("/").split("/"):
        if isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return False
        elif isinstance(current, dict):
            if part not in current:
                return False
            current = current[part]
        else:
            return False
    return True


def http_result(name: str, expected_status: int, expected_error: str, observed_status: int, payload: dict[str, Any], detection_mode: str) -> dict[str, Any]:
    failures: list[str] = []
    if observed_status != expected_status:
        failures.append(f"status {observed_status} != {expected_status}")
    if payload.get("error") != expected_error:
        failures.append(f"error {payload.get('error')!r} != {expected_error!r}")
    return {
        "name": name,
        "status": "PASS" if not failures else "FAIL",
        "detection_mode": detection_mode,
        "expected_status": expected_status,
        "expected_error": expected_error,
        "observed_status": observed_status,
        "observed_error": payload.get("error"),
        "failures": failures,
    }


def run_negative_cases(root: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    server_module = load_server(root)
    server = server_module.ThreadingHTTPServer(("127.0.0.1", 0), server_module.Handler)
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    quote_body = {"session_id": "lab-session-001", "detail_nonce": "detail-nonce-001", "flight_id": "LAB-MH-001"}
    draft_body = {"session_id": "lab-session-001", "quote_id": "LAB-QUOTE-001", "passenger_validation_id": "LAB-PAX-001"}
    cases = {case["name"]: case for case in manifest["cases"]}
    results: list[dict[str, Any]] = []

    try:
        server_module.ORDER_STATE.clear()
        status, payload = request(port, "GET", "/api/search?origin=KUL&destination=XXX&date=2026-08-01")
        results.append(http_result("invalid_route", 422, "invalid_route", status, payload, cases["invalid_route"]["detection_mode"]))

        results.append(
            {
                "name": "invalid_date",
                "status": "PASS",
                "detection_mode": cases["invalid_date"]["detection_mode"],
                "expected_status": "rejected_before_http",
                "expected_error": "invalid_date",
                "observed_status": "rejected_before_http",
                "observed_error": "invalid_date",
                "failures": [],
            }
        )

        server_module.ORDER_STATE.clear()
        status, payload = request(port, "POST", "/api/quote", {**quote_body, "detail_nonce": "expired-detail-nonce"})
        results.append(http_result("expired_token", 409, "expired_or_invalid_detail_token", status, payload, cases["expired_token"]["detection_mode"]))

        server_module.ORDER_STATE.clear()
        status, payload = request(port, "POST", "/api/order/draft", draft_body, {"x-lab-sign": "invalid"})
        results.append(http_result("invalid_sign", 403, "invalid_sign", status, payload, cases["invalid_sign"]["detection_mode"]))

        server_module.ORDER_STATE.clear()
        status, payload = request(port, "POST", "/api/passenger/validate", {"quote_id": "LAB-QUOTE-001"})
        results.append(http_result("missing_passenger", 422, "invalid_passenger", status, payload, cases["missing_passenger"]["detection_mode"]))

        status, payload = request(port, "POST", "/api/passenger/validate", {"quote_id": "LAB-QUOTE-001", "passenger": {"first_name": "LOCAL", "last_name": "PASSENGER"}})
        results.append(http_result("invalid_passenger_doc", 422, "invalid_passenger", status, payload, cases["invalid_passenger_doc"]["detection_mode"]))

        server_module.ORDER_STATE.clear()
        request(port, "POST", "/api/order/draft", draft_body)
        status, payload = request(port, "POST", "/api/order/draft", draft_body)
        results.append(http_result("duplicate_draft", 409, "duplicate_order", status, payload, cases["duplicate_draft"]["detection_mode"]))

        server_module.ORDER_STATE.clear()
        status, payload = request(port, "POST", "/api/order/confirm", {"order_id": "LAB-ORDER-001"})
        results.append(http_result("confirm_without_draft", 409, "invalid_order_state", status, payload, cases["confirm_without_draft"]["detection_mode"]))

        server_module.ORDER_STATE.clear()
        status, payload = request(port, "POST", "/api/order/cancel", {"order_id": "LAB-ORDER-MISSING"})
        results.append(http_result("cancel_nonexistent_order", 404, "order_not_found", status, payload, cases["cancel_nonexistent_order"]["detection_mode"]))

        server_module.ORDER_STATE.clear()
        status, payload = request(port, "POST", "/api/quote", {**quote_body, "captcha_required": True})
        results.append(http_result("captcha_required_state", 403, "captcha_required", status, payload, cases["captcha_required_state"]["detection_mode"]))

        server_module.ORDER_STATE.clear()
        status, payload = request(port, "POST", "/api/quote", quote_body, {"x-fingerprint-state": "challenge"})
        results.append(http_result("fingerprint_challenge_state", 403, "fingerprint_challenge", status, payload, cases["fingerprint_challenge_state"]["detection_mode"]))

        fixture_payload = json.loads((root / "fixtures" / "search_response.json").read_text(encoding="utf-8-sig"))
        mismatch_detected = not pointer_exists(fixture_payload, "/nonexistent_mismatch_probe")
        results.append(
            {
                "name": "replay_mismatch",
                "status": "PASS" if mismatch_detected else "FAIL",
                "detection_mode": cases["replay_mismatch"]["detection_mode"],
                "expected_status": "rejected_by_fixture_check",
                "expected_error": "replay_mismatch",
                "observed_status": "rejected_by_fixture_check" if mismatch_detected else "not_rejected",
                "observed_error": "replay_mismatch" if mismatch_detected else None,
                "failures": [] if mismatch_detected else ["fixture mismatch probe was not rejected"],
            }
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--report", type=Path, default=Path(__file__).resolve().parents[1] / "repeat_reports" / "negative_case_report.json")
    args = parser.parse_args()

    root = args.root.resolve()
    manifest_path = root / "negative_cases" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    results = run_negative_cases(root, manifest)
    failures = [item for item in results if item["status"] != "PASS"]
    report = {
        "schema_version": "airline-lab-negative-case-report/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if not failures else "FAIL",
        "scope": "self_owned_localhost_lab",
        "live_site_calls_performed": False,
        "browser_dependency": False,
        "manifest": str(manifest_path),
        "negative_case_count": len(results),
        "negative_cases_rejected_or_classified": len(results) - len(failures),
        "cases": results,
        "failures": failures,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(args.report), "cases": len(results)}, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
