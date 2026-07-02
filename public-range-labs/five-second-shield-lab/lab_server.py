#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


SESSIONS: dict[str, dict[str, object]] = {}
ORDERS: list[dict[str, object]] = []
SECRET = "local-shield-secret"


def now() -> float:
    return time.time()


def sign(sid: str, nonce: str, ua_hash: str, script_hash: str, mutation: str, action: str) -> str:
    return hashlib.sha256(f"{sid}:{nonce}:{ua_hash}:{script_hash}:{mutation}:{action}:{SECRET}".encode()).hexdigest()[:24]


def parse_cookies(header: str | None) -> dict[str, str]:
    cookie = SimpleCookie()
    if header:
        cookie.load(header)
    return {key: morsel.value for key, morsel in cookie.items()}


def make_nonce_state(profile: str = "simple_delay_gate") -> dict[str, object]:
    nonce = secrets.token_hex(8)
    mutation = secrets.token_hex(5)
    script_hash = hashlib.sha256(f"{nonce}:{mutation}:{time.time_ns()}".encode()).hexdigest()[:16]
    created_at = now()
    return {
        "nonce": nonce,
        "mutation": mutation,
        "script_hash": script_hash,
        "created_at": created_at,
        "expires_at": created_at + 30,
        "min_delay_ms": 45 + int(nonce[:2], 16) % 30,
        "max_delay_ms": 2500,
        "used": False,
        "script_fetched": False,
        "action": "business_api_after_challenge",
        "profile": profile,
        "redirect_stage": "protected_to_shield_to_challenge_js",
        "retry_after_seconds": 2 if profile == "retry_after_gate" else 0,
        "rate_limit_bucket": "local_session" if profile == "rate_limit_gate" else "",
    }


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, code: int, payload: object, extra_headers: dict[str, str] | None = None) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _session(self) -> tuple[str, dict[str, object], bool]:
        cookies = parse_cookies(self.headers.get("Cookie"))
        sid = cookies.get("shield_sid")
        created = False
        if not sid:
            sid = secrets.token_hex(8)
            created = True
        state = SESSIONS.setdefault(sid, {"sid": sid, "nonces": {}, "clearances": {}})
        return sid, state, created

    def _issue_challenge_page(self, sid: str, state: dict[str, object], profile: str = "simple_delay_gate") -> bytes:
        nonce_state = make_nonce_state(profile)
        nonces = state["nonces"]
        assert isinstance(nonces, dict)
        nonces[str(nonce_state["nonce"])] = nonce_state
        body = (
            "<html><body><h1>Five Second Shield Lab</h1>"
            f"<script src='/challenge.js?nonce={nonce_state['nonce']}&script_hash={nonce_state['script_hash']}&profile={profile}'></script>"
            "<p>shield_required</p></body></html>"
        )
        return body.encode("utf-8")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/protected":
            profile = parse_qs(parsed.query).get("profile", ["simple_delay_gate"])[0]
            sid, state, _ = self._session()
            clearance = parse_cookies(self.headers.get("Cookie")).get("local_clearance")
            if clearance and self._clearance_ok(sid, clearance, require_unused_submit=False):
                self._send_json(200, {"ok": True, "page": "protected", "business_hint": "/api/business"})
                return
            self.send_response(302)
            self.send_header("Set-Cookie", f"shield_sid={sid}; Path=/; HttpOnly")
            self.send_header("Location", f"/shield?profile={profile}")
            self.end_headers()
            return
        if parsed.path == "/shield":
            profile = parse_qs(parsed.query).get("profile", ["simple_delay_gate"])[0]
            sid, state, _ = self._session()
            raw = self._issue_challenge_page(sid, state, profile)
            self.send_response(403)
            self.send_header("Set-Cookie", f"shield_sid={sid}; Path=/; HttpOnly")
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if parsed.path == "/challenge.js":
            qs = parse_qs(parsed.query)
            nonce = qs.get("nonce", [""])[0]
            script_hash = qs.get("script_hash", [""])[0]
            sid, state, _ = self._session()
            nonce_state = state["nonces"].get(nonce) if isinstance(state.get("nonces"), dict) else None
            if not isinstance(nonce_state, dict) or nonce_state.get("script_hash") != script_hash:
                self.send_response(404)
                self.end_headers()
                return
            nonce_state["script_fetched"] = True
            body = (
                "window.localShield={"
                f"nonce:'{nonce}',scriptHash:'{script_hash}',mutation:'{nonce_state['mutation']}',"
                f"profile:'{nonce_state.get('profile', 'simple_delay_gate')}',"
                f"minDelayMs:{nonce_state['min_delay_ms']},maxDelayMs:{nonce_state['max_delay_ms']},"
                "action:'business_api_after_challenge',"
                "algo:'sha256(sid:nonce:ua_hash:script_hash:mutation:action:local-shield-secret)'"
                "};"
            )
            raw = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript")
            self.send_header("X-Local-Script-Hash", script_hash)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if parsed.path == "/api/runtime-contract":
            self._send_json(200, {
                "required_apis": ["crypto.subtle.digest", "TextEncoder", "Date.now", "fetch"],
                "missing_api_detection": True,
                "environment_contract": "browser-node-page-runtime-repeat-parity",
            })
            return
        if parsed.path == "/api/business":
            sid, _, _ = self._session()
            clearance = parse_cookies(self.headers.get("Cookie")).get("local_clearance")
            if not clearance or not self._clearance_ok(sid, clearance, require_unused_submit=False):
                self._send_json(403, {"ok": False, "error": "shield_required"})
                return
            self._send_json(200, {"ok": True, "items": [{"sku": "shield-local", "price": 100}], "session_id": sid})
            return
        if parsed.path == "/server-ledger":
            self._send_json(200, {"orders": ORDERS})
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        parsed = urlparse(self.path)
        sid, state, _ = self._session()
        if parsed.path == "/challenge/verify":
            nonce = str(payload.get("nonce", ""))
            ua_hash = str(payload.get("ua_hash", ""))
            script_hash = str(payload.get("script_hash", ""))
            mutation = str(payload.get("mutation", ""))
            action = str(payload.get("action", "business_api_after_challenge"))
            nonce_state = state["nonces"].get(nonce) if isinstance(state.get("nonces"), dict) else None
            if not isinstance(nonce_state, dict) or nonce_state.get("used") or now() > float(nonce_state.get("expires_at", 0)):
                self._send_json(403, {"ok": False, "error": "stale_nonce"})
                return
            if nonce_state.get("script_fetched") is not True:
                self._send_json(403, {"ok": False, "error": "script_not_fetched"})
                return
            elapsed_ms = int(payload.get("elapsed_ms") or 0)
            if elapsed_ms < int(nonce_state.get("min_delay_ms", 0)) or elapsed_ms > int(nonce_state.get("max_delay_ms", 999999)):
                self._send_json(403, {"ok": False, "error": "delay_window"})
                return
            if script_hash != nonce_state.get("script_hash") or mutation != nonce_state.get("mutation") or action != nonce_state.get("action"):
                self._send_json(403, {"ok": False, "error": "mutation_mismatch"})
                return
            expected = sign(sid, nonce, ua_hash, script_hash, mutation, action)
            if payload.get("signature") != expected:
                self._send_json(403, {"ok": False, "error": "wrong_signature"})
                return
            nonce_state["used"] = True
            clearance = secrets.token_hex(12)
            ttl = float(payload.get("ttl_seconds", 45) or 45)
            clearances = state["clearances"]
            assert isinstance(clearances, dict)
            clearances[clearance] = {
                "expires_at": now() + ttl,
                "used_submit": False,
                "ua_hash": ua_hash,
                "action": action,
                "owner_sid": sid,
                "nonce": nonce,
            }
            self._send_json(200, {"ok": True, "state": "backend_accepted"}, {"Set-Cookie": f"local_clearance={clearance}; Path=/; HttpOnly"})
            return
        if parsed.path in {"/api/submit", "/api/concurrency/business"}:
            clearance = parse_cookies(self.headers.get("Cookie")).get("local_clearance")
            if not clearance:
                self._send_json(403, {"ok": False, "error": "shield_required"})
                return
            if not self._clearance_ok(sid, clearance, require_unused_submit=True):
                self._send_json(403, {"ok": False, "error": "reused_clearance_or_wrong_session"})
                return
            cstate = SESSIONS[sid]["clearances"][clearance]  # type: ignore[index]
            assert isinstance(cstate, dict)
            cstate["used_submit"] = True
            order = {
                "order_id": secrets.token_hex(6),
                "session_id": sid,
                "worker_id": payload.get("worker_id", ""),
                "endpoint": "POST /api/concurrency/business" if parsed.path.endswith("business") else "POST /api/submit",
                "amount": payload.get("amount", 100),
            }
            ORDERS.append(order)
            self._send_json(200, {"ok": True, "order": order})
            return
        self._send_json(404, {"error": "not_found"})

    def _clearance_ok(self, sid: str, clearance: str, require_unused_submit: bool) -> bool:
        state = SESSIONS.get(sid)
        if not state:
            return False
        clearances = state.get("clearances")
        if not isinstance(clearances, dict):
            return False
        cstate = clearances.get(clearance)
        if not isinstance(cstate, dict):
            return False
        if cstate.get("owner_sid") != sid:
            return False
        if now() > float(cstate.get("expires_at", 0)):
            return False
        if require_unused_submit and cstate.get("used_submit"):
            return False
        return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
