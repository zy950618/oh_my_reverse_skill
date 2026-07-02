#!/usr/bin/env python3
"""Deep local validation for the airline lab order-flow mock server."""
from __future__ import annotations

import argparse
import http.client
import importlib.util
import json
import sys
import threading
from pathlib import Path
from typing import Any, Callable


CaseCheck = Callable[[int, dict[str, Any]], list[str]]


def load_server(root: Path) -> Any:
    sys.dont_write_bytecode = True
    path = root / "mock_server" / "server.py"
    spec = importlib.util.spec_from_file_location("airline_lab_mock_server", path)
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


def expect(expected_status: int, **fields: Any) -> CaseCheck:
    def check(observed_status: int, payload: dict[str, Any]) -> list[str]:
        failures: list[str] = []
        if observed_status != expected_status:
            failures.append(f"status {observed_status} != {expected_status}")
        for key, expected in fields.items():
            if payload.get(key) != expected:
                failures.append(f"{key} {payload.get(key)!r} != {expected!r}")
        return failures

    return check


def expect_flight(status: int, payload: dict[str, Any]) -> list[str]:
    failures = expect(200, status="ok")(status, payload)
    flights = payload.get("flights")
    if not isinstance(flights, list) or not flights:
        failures.append("flights must be non-empty")
    elif flights[0].get("flight_id") != "LAB-MH-001":
        failures.append("first flight_id mismatch")
    return failures


def run_case(port: int, case: dict[str, Any]) -> dict[str, Any]:
    status, payload = request(port, case["method"], case["path"], case.get("body"), case.get("headers"))
    failures = case["check"](status, payload)
    return {
        "name": case["name"],
        "status": "PASS" if not failures else "FAIL",
        "request": {
            "method": case["method"],
            "path": case["path"],
            "headers": case.get("headers", {}),
            "body_present": "body" in case,
        },
        "response_status": status,
        "response": payload,
        "failures": failures,
    }


def case_matrix() -> list[dict[str, Any]]:
    quote_body = {"session_id": "lab-session-001", "detail_nonce": "detail-nonce-001", "flight_id": "LAB-MH-001"}
    passenger = {
        "quote_id": "LAB-QUOTE-001",
        "passenger": {"first_name": "LOCAL", "last_name": "PASSENGER", "document_number": "LAB000001"},
    }
    draft = {"session_id": "lab-session-001", "quote_id": "LAB-QUOTE-001", "passenger_validation_id": "LAB-PAX-001"}
    return [
        {
            "name": "valid_search",
            "method": "GET",
            "path": "/api/search?origin=KUL&destination=SIN&date=2026-08-01",
            "check": expect_flight,
        },
        {
            "name": "invalid_route",
            "method": "GET",
            "path": "/api/search?origin=KUL&destination=XXX&date=2026-08-01",
            "check": expect(422, status="error", error="invalid_route", ledger_delta=0),
        },
        {"name": "quote_success", "method": "POST", "path": "/api/quote", "body": quote_body, "check": expect(200, status="ok", quote_id="LAB-QUOTE-001")},
        {
            "name": "quote_expired_token",
            "method": "POST",
            "path": "/api/quote",
            "body": {**quote_body, "detail_nonce": "expired-detail-nonce"},
            "check": expect(409, status="error", error="expired_or_invalid_detail_token", ledger_delta=0),
        },
        {
            "name": "passenger_valid",
            "method": "POST",
            "path": "/api/passenger/validate",
            "body": passenger,
            "check": expect(200, status="ok", passenger_validation_id="LAB-PAX-001"),
        },
        {
            "name": "passenger_invalid",
            "method": "POST",
            "path": "/api/passenger/validate",
            "body": {"quote_id": "LAB-QUOTE-001", "passenger": {"first_name": "LOCAL"}},
            "check": expect(422, status="error", error="invalid_passenger"),
        },
        {"name": "draft_order_success", "method": "POST", "path": "/api/order/draft", "body": draft, "check": expect(200, status="ok", order_id="LAB-ORDER-001", order_state="draft", ledger_delta=0)},
        {
            "name": "duplicate_order_rejected",
            "method": "POST",
            "path": "/api/order/draft",
            "body": draft,
            "check": expect(409, status="error", error="duplicate_order", order_id="LAB-ORDER-001", ledger_delta=0),
        },
        {
            "name": "confirm_order_success",
            "method": "POST",
            "path": "/api/order/confirm",
            "body": {"order_id": "LAB-ORDER-001"},
            "check": expect(200, status="ok", order_id="LAB-ORDER-001", order_state="confirmed", ledger_delta=1, payment_required=False),
        },
        {
            "name": "cancel_order_success",
            "method": "POST",
            "path": "/api/order/cancel",
            "body": {"order_id": "LAB-ORDER-001"},
            "check": expect(200, status="ok", order_id="LAB-ORDER-001", order_state="cancelled", ledger_delta=-1),
        },
        {
            "name": "invalid_sign_rejected",
            "method": "POST",
            "path": "/api/order/draft",
            "headers": {"x-lab-sign": "invalid"},
            "body": draft,
            "check": expect(403, status="error", error="invalid_sign", ledger_delta=0),
        },
        {
            "name": "captcha_required_state",
            "method": "POST",
            "path": "/api/quote",
            "body": {**quote_body, "captcha_required": True},
            "check": expect(403, status="error", error="captcha_required", captcha_required=True, ledger_delta=0),
        },
        {
            "name": "fingerprint_challenge_state",
            "method": "POST",
            "path": "/api/quote",
            "headers": {"x-fingerprint-state": "challenge"},
            "body": quote_body,
            "check": expect(403, status="error", error="fingerprint_challenge", fingerprint_challenge=True, ledger_delta=0),
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--report", type=Path, default=Path(__file__).resolve().parents[1] / "reports" / "deep_validation_report.json")
    args = parser.parse_args()

    root = args.root.resolve()
    server_module = load_server(root)
    server_module.ORDER_STATE.clear()
    server = server_module.ThreadingHTTPServer(("127.0.0.1", 0), server_module.Handler)
    port = int(server.server_address[1])
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        results = [run_case(port, case) for case in case_matrix()]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    failures = [item for item in results if item["status"] != "PASS"]
    report = {
        "schema_version": "airline-lab-deep-validation/v1",
        "status": "PASS" if not failures else "FAIL",
        "scope": "self_owned_localhost_lab",
        "live_site_calls_performed": False,
        "mock_server": "in_process_threading_http_server",
        "cases": results,
        "coverage": [item["name"] for item in results],
        "business_data_boundary": {
            "ledger_delta_positive_confirm": 1,
            "ledger_delta_cancel": -1,
            "negative_ledger_delta": 0,
            "payment_required": False,
        },
        "capability_boundary": {
            "positive_airline_capability_claim": False,
            "third_party_captcha_or_waf_bypass_claim": False,
            "browser_profile_dependency": False,
        },
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(args.report), "cases": len(results)}, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
