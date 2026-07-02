#!/usr/bin/env python3
"""Self-owned realistic CAPTCHA/risk lab v2 backend."""
from __future__ import annotations

import json
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


LAB_DIR = Path(__file__).resolve().parent
STORE = {"sessions": {}, "tokens": {}, "orders": [], "rejected": []}
LOCK = threading.Lock()


def make_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(10)}"


def body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("content-length", "0") or 0)
    if not length:
        return {}
    return json.loads(handler.rfile.read(length).decode("utf-8"))


def send(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    raw = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("content-type", "application/json")
    handler.send_header("content-length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def send_with_cookie(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any], cookie: str) -> None:
    raw = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("set-cookie", cookie)
    handler.send_header("content-type", "application/json")
    handler.send_header("content-length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def session_from(handler: BaseHTTPRequestHandler, worker_id: str = "") -> str:
    cookie = handler.headers.get("cookie", "")
    sid = ""
    for part in cookie.split(";"):
        if part.strip().startswith("rcrl_session="):
            sid = part.split("=", 1)[1].strip()
    with LOCK:
        if not sid or sid not in STORE["sessions"]:
            sid = make_id("sess")
            STORE["sessions"][sid] = {"session_id": sid, "worker_id": worker_id, "created": time.time(), "verified_actions": {}}
    return sid


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        if self.path == "/" or self.path.startswith("/index"):
            raw = (LAB_DIR / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("content-type", "text/html")
            self.send_header("content-length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if self.path == "/runtime-signature.js" or self.path == "/api/runtime/script":
            raw = (LAB_DIR / "runtime-signature.js").read_bytes()
            self.send_response(200)
            self.send_header("content-type", "application/javascript")
            self.send_header("content-length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if self.path.startswith("/api/session"):
            sid = session_from(self)
            send_with_cookie(self, 200, {"session_id": sid, "state": "clean"}, f"rcrl_session={sid}; Path=/; SameSite=Lax")
            return
        if self.path.startswith("/api/list"):
            session_from(self)
            send(self, 200, {"items": [{"id": "risk-item-1", "item_version": 1}]})
            return
        if self.path.startswith("/api/detail"):
            session_from(self)
            send(self, 200, {"item": {"id": "risk-item-1", "item_version": 1, "detail_nonce": "detail-local"}})
            return
        if self.path.startswith("/api/fingerprint/state"):
            send(self, 200, {"risk_state": "observed_only", "block_reason": "not_blocked_localhost"})
            return
        send(self, 404, {"error": "not_found"})

    def do_POST(self) -> None:
        payload = body(self)
        worker_id = str(payload.get("worker_id", ""))
        sid = session_from(self, worker_id)
        if self.path in {"/api/captcha/challenge", "/api/risk/challenge"}:
            cid = make_id("challenge")
            token = make_id("tok")
            with LOCK:
                STORE["tokens"][token] = {
                    "session_id": sid,
                    "worker_id": worker_id,
                    "action": payload.get("action", "submit"),
                    "used": False,
                    "challenge_instance_id": cid,
                    "expires_at": time.time() + 30,
                }
            send(self, 200, {"challenge_instance_id": cid, "token": token, "session_id": sid})
            return
        if self.path in {"/api/captcha/verify", "/api/risk/verify"}:
            token = payload.get("token")
            with LOCK:
                tok = STORE["tokens"].get(token)
                if not tok:
                    reason = "missing_token"
                elif tok["session_id"] != sid:
                    reason = "wrong_session"
                elif tok["worker_id"] != worker_id:
                    reason = "cross_worker_token_pollution"
                elif tok["used"]:
                    reason = "token_duplicate"
                elif tok.get("expires_at", 0) < time.time():
                    reason = "token_expired"
                elif payload.get("action") and payload.get("action") != tok.get("action"):
                    reason = "wrong_action"
                else:
                    reason = ""
                if reason:
                    STORE["rejected"].append({"session_id": sid, "worker_id": worker_id, "reason": reason})
                    send(self, 403, {"ok": False, "state": "backend_rejected"})
                    return
                tok["used"] = True
                STORE["sessions"].setdefault(sid, {"verified_actions": {}}).setdefault("verified_actions", {})[tok.get("action", "submit")] = True
            send(self, 200, {"ok": True, "state": "backend_accepted"})
            return
        if self.path in {"/api/submit", "/api/concurrency/business"}:
            signature = payload.get("js_signature")
            with LOCK:
                verified = STORE["sessions"].get(sid, {}).get("verified_actions", {}).get("submit") is True
            if not verified:
                with LOCK:
                    STORE["rejected"].append({"session_id": sid, "worker_id": worker_id, "reason": "missing_verify"})
                send(self, 403, {"ok": False, "reason": "missing_verify"})
                return
            if not signature:
                with LOCK:
                    STORE["rejected"].append({"session_id": sid, "worker_id": worker_id, "reason": "missing_signature"})
                send(self, 403, {"ok": False, "reason": "missing_signature"})
                return
            order = {"order_id": make_id("order"), "session_id": sid, "worker_id": worker_id, "item_id": payload.get("item_id", "risk-item-1"), "js_signature": signature}
            with LOCK:
                STORE["orders"].append(order)
            send(self, 200, {"ok": True, **order})
            return
        if self.path == "/api/runtime/signature-check" or self.path == "/api/runtime/parity-check":
            send(self, 200, {"ok": True, "accepted": True})
            return
        send(self, 404, {"error": "not_found"})


def make_server() -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", 0), Handler)


if __name__ == "__main__":
    server = make_server()
    print(f"http://{server.server_address[0]}:{server.server_address[1]}")
    server.serve_forever()
