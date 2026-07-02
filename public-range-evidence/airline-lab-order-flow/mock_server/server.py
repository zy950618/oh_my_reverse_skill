#!/usr/bin/env python3
"""Local airline order-flow mock server.

This is a self-owned localhost fixture server. It does not call airline sites.
"""
from __future__ import annotations

import argparse
import json
from urllib.parse import parse_qs, urlparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


CATALOG = [
    {
        "flight_id": "LAB-MH-001",
        "origin": "KUL",
        "destination": "SIN",
        "currency": "MYR",
        "price": 120.0,
    }
]

ORDER_STATE: dict[str, str] = {}


def response(status: str, **extra: Any) -> bytes:
    payload = {"status": status, **extra}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "AirlineLabMock/0.1"

    def do_GET(self) -> None:
        if self.path == "/health":
            self.write_json(200, response("ok", service="airline-lab-order-flow"))
            return
        if self.path.startswith("/api/search"):
            query = parse_qs(urlparse(self.path).query)
            if query.get("origin", [""])[0] != "KUL" or query.get("destination", [""])[0] != "SIN":
                self.write_json(422, response("error", error="invalid_route", ledger_delta=0))
                return
            self.write_json(200, response("ok", session_id="lab-session-001", flights=CATALOG))
            return
        self.write_json(404, response("error", error="not_found"))

    def do_POST(self) -> None:
        length = int(self.headers.get("content-length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self.write_json(400, response("error", error="invalid_json"))
            return
        if self.headers.get("x-lab-sign") == "invalid":
            self.write_json(403, response("error", error="invalid_sign", ledger_delta=0))
            return
        if self.headers.get("x-fingerprint-state") == "challenge":
            self.write_json(403, response("error", error="fingerprint_challenge", fingerprint_challenge=True, ledger_delta=0))
            return
        if self.path == "/api/detail":
            if body.get("session_id") != "lab-session-001":
                self.write_json(403, response("error", error="wrong_session"))
                return
            self.write_json(
                200,
                response(
                    "ok",
                    session_id="lab-session-001",
                    flight=CATALOG[0],
                    detail_nonce="detail-nonce-001",
                ),
            )
            return
        if self.path == "/api/quote":
            if body.get("captcha_required") is True:
                self.write_json(403, response("error", error="captcha_required", captcha_required=True, ledger_delta=0))
                return
            if body.get("detail_nonce") != "detail-nonce-001":
                self.write_json(409, response("error", error="expired_or_invalid_detail_token", ledger_delta=0))
                return
            self.write_json(
                200,
                response(
                    "ok",
                    quote_id="LAB-QUOTE-001",
                    currency="MYR",
                    total=120.0,
                    token_state="quote_token_issued",
                    captcha_required=False,
                    fingerprint_challenge=False,
                ),
            )
            return
        if self.path == "/api/passenger/validate":
            if body.get("quote_id") != "LAB-QUOTE-001":
                self.write_json(409, response("error", error="invalid_quote"))
                return
            passenger = body.get("passenger", {})
            if not passenger.get("last_name") or not passenger.get("document_number"):
                self.write_json(422, response("error", error="invalid_passenger"))
                return
            self.write_json(200, response("ok", passenger_validation_id="LAB-PAX-001"))
            return
        if self.path == "/api/order/draft":
            if body.get("session_id") != "lab-session-001":
                self.write_json(403, response("error", error="wrong_session"))
                return
            if body.get("passenger_validation_id") != "LAB-PAX-001":
                self.write_json(409, response("error", error="invalid_passenger_state"))
                return
            if ORDER_STATE.get("LAB-ORDER-001") is not None:
                self.write_json(409, response("error", error="duplicate_order", order_id="LAB-ORDER-001", ledger_delta=0))
                return
            ORDER_STATE["LAB-ORDER-001"] = "draft"
            self.write_json(
                200,
                response(
                    "ok",
                    order_id="LAB-ORDER-001",
                    order_state="draft",
                    ledger_delta=0,
                    idempotency="duplicate_request_rejected",
                ),
            )
            return
        if self.path == "/api/order/confirm":
            if ORDER_STATE.get(body.get("order_id")) != "draft":
                self.write_json(409, response("error", error="invalid_order_state"))
                return
            ORDER_STATE[body["order_id"]] = "confirmed"
            self.write_json(
                200,
                response(
                    "ok",
                    order_id=body["order_id"],
                    order_state="confirmed",
                    ledger_delta=1,
                    payment_required=false_payment_required(),
                ),
            )
            return
        if self.path == "/api/order/cancel":
            if body.get("order_id") not in ORDER_STATE:
                self.write_json(404, response("error", error="order_not_found"))
                return
            ORDER_STATE[body["order_id"]] = "cancelled"
            self.write_json(200, response("ok", order_id=body["order_id"], order_state="cancelled", ledger_delta=-1))
            return
        self.write_json(404, response("error", error="not_found"))

    def write_json(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("cache-control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:
        return


def false_payment_required() -> bool:
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local airline lab mock server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18991)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"airline lab mock server listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
