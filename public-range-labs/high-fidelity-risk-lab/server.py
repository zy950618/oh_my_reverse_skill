#!/usr/bin/env python3
"""High-fidelity local risk lab backend.

This lab is self-owned localhost infrastructure. It models server-side risk
state, token lifecycle, direct business API acceptance, and worker isolation
without claiming any third-party CAPTCHA/WAF capability.
"""
from __future__ import annotations

import json
import mimetypes
import secrets
import threading
import time
import urllib.parse
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


LAB_DIR = Path(__file__).resolve().parent
SESSION_COOKIE = "hfrl_session"
TOKEN_TTL_MS = 60_000

ALL_STATES = [
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


def now_ms() -> int:
    return int(time.time() * 1000)


def make_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(18)}"


@dataclass
class SessionState:
    session_id: str
    created_at_ms: int
    state: str = "clean"
    verified_actions: set[str] = field(default_factory=set)
    listed_items: dict[str, int] = field(default_factory=dict)
    detail_nonces: dict[str, dict[str, Any]] = field(default_factory=dict)
    request_times_ms: list[int] = field(default_factory=list)
    worker_id: str = ""
    states_seen: list[str] = field(default_factory=lambda: ["clean"])

    def set_state(self, state: str) -> None:
        self.state = state
        if state not in self.states_seen:
            self.states_seen.append(state)


@dataclass
class RiskToken:
    token: str
    session_id: str
    action: str
    nonce: str
    worker_id: str
    issued_at_ms: int
    expires_at_ms: int
    used: bool = False


class RiskStore:
    def __init__(self) -> None:
        self.sessions: dict[str, SessionState] = {}
        self.tokens: dict[str, RiskToken] = {}
        self.request_log: list[dict[str, Any]] = []
        self.orders: list[dict[str, Any]] = []
        self.business_ledger: dict[str, list[dict[str, Any]]] = {
            "list_events": [],
            "detail_events": [],
            "orders": [],
            "rejected_submissions": [],
            "concurrency_orders": [],
        }
        self.lock = threading.Lock()

    def create_session(self, worker_id: str = "") -> SessionState:
        with self.lock:
            session = SessionState(
                session_id=make_id("sess"),
                created_at_ms=now_ms(),
                worker_id=worker_id,
            )
            self.sessions[session.session_id] = session
            return session

    def get_session(self, session_id: str) -> SessionState | None:
        with self.lock:
            return self.sessions.get(session_id)

    def issue_token(
        self,
        session: SessionState,
        action: str,
        worker_id: str,
        ttl_ms: int = TOKEN_TTL_MS,
    ) -> RiskToken:
        with self.lock:
            session.set_state("challenge_visible")
            nonce = make_id("nonce")
            token = RiskToken(
                token=make_id("tok"),
                session_id=session.session_id,
                action=action,
                nonce=nonce,
                worker_id=worker_id,
                issued_at_ms=now_ms(),
                expires_at_ms=now_ms() + max(1, ttl_ms),
            )
            self.tokens[token.token] = token
            session.set_state("token_issued")
            return token

    def verify_token(
        self,
        session: SessionState,
        token_value: str,
        action: str,
        nonce: str,
        worker_id: str,
    ) -> tuple[int, dict[str, Any]]:
        with self.lock:
            token = self.tokens.get(token_value)
            if token is None:
                session.set_state("backend_rejected")
                return 400, {
                    "ok": False,
                    "state": "backend_rejected",
                    "failure_code": "stale_token",
                    "reason": "unknown token",
                }
            if token.session_id != session.session_id:
                if token.worker_id and worker_id and token.worker_id != worker_id:
                    session.set_state("session_polluted")
                    return 403, {
                        "ok": False,
                        "state": "session_polluted",
                        "failure_code": "cross_worker_token_pollution",
                        "reason": "token is bound to another worker/session",
                    }
                session.set_state("wrong_session")
                return 403, {
                    "ok": False,
                    "state": "wrong_session",
                    "failure_code": "wrong_session",
                    "reason": "token is bound to another session",
                }
            if token.used:
                session.set_state("token_duplicate")
                return 409, {
                    "ok": False,
                    "state": "token_duplicate",
                    "failure_code": "duplicate_token",
                    "reason": "token was already used",
                }
            if now_ms() > token.expires_at_ms:
                session.set_state("token_expired")
                return 410, {
                    "ok": False,
                    "state": "token_expired",
                    "failure_code": "expired_token",
                    "reason": "token expired",
                }
            if token.action != action:
                session.set_state("wrong_action")
                return 403, {
                    "ok": False,
                    "state": "wrong_action",
                    "failure_code": "wrong_action",
                    "reason": "token is bound to another action",
                }
            if token.nonce != nonce:
                session.set_state("backend_rejected")
                return 400, {
                    "ok": False,
                    "state": "backend_rejected",
                    "failure_code": "stale_token",
                    "reason": "nonce mismatch",
                }
            if token.worker_id and worker_id and token.worker_id != worker_id:
                session.set_state("session_polluted")
                return 403, {
                    "ok": False,
                    "state": "session_polluted",
                    "failure_code": "cross_worker_token_pollution",
                    "reason": "token is bound to another worker",
                }

            token.used = True
            session.verified_actions.add(action)
            session.set_state("backend_accepted")
            return 200, {
                "ok": True,
                "state": "backend_accepted",
                "verified_action": action,
                "session_id": session.session_id,
                "worker_id": worker_id,
            }

    def record_business_hit(self, session: SessionState) -> bool:
        current = now_ms()
        session.request_times_ms = [
            item for item in session.request_times_ms if current - item <= 1000
        ]
        session.request_times_ms.append(current)
        if len(session.request_times_ms) > 3:
            session.set_state("rate_limited")
            return False
        return True

    def record_list(self, session: SessionState, items: list[dict[str, Any]]) -> None:
        with self.lock:
            for item in items:
                session.listed_items[str(item["id"])] = int(item["item_version"])
            self.business_ledger["list_events"].append(
                {
                    "at_ms": now_ms(),
                    "session_id": session.session_id,
                    "item_ids": [str(item["id"]) for item in items],
                }
            )

    def record_detail(self, session: SessionState, item_id: str, item_version: int) -> str:
        with self.lock:
            detail_nonce = make_id("detail")
            session.detail_nonces[item_id] = {
                "detail_nonce": detail_nonce,
                "item_version": item_version,
                "at_ms": now_ms(),
            }
            self.business_ledger["detail_events"].append(
                {
                    "at_ms": now_ms(),
                    "session_id": session.session_id,
                    "item_id": item_id,
                    "item_version": item_version,
                    "detail_nonce": detail_nonce,
                }
            )
            return detail_nonce

    def reject_submission(
        self,
        session: SessionState,
        endpoint: str,
        reason: str,
        item_id: str = "",
        worker_id: str = "",
        ledger_delta: int = 0,
    ) -> None:
        with self.lock:
            self.business_ledger["rejected_submissions"].append(
                {
                    "at_ms": now_ms(),
                    "session_id": session.session_id,
                    "worker_id": worker_id,
                    "endpoint": endpoint,
                    "item_id": item_id,
                    "reason": reason,
                    "ledger_delta": ledger_delta,
                }
            )

    def create_order(
        self,
        session: SessionState,
        endpoint: str,
        item_id: str,
        item_version: int,
        detail_nonce: str,
        worker_id: str = "",
    ) -> dict[str, Any]:
        with self.lock:
            order = {
                "order_id": make_id("order"),
                "at_ms": now_ms(),
                "session_id": session.session_id,
                "worker_id": worker_id,
                "endpoint": endpoint,
                "item_id": item_id,
                "item_version": item_version,
                "detail_nonce": detail_nonce,
            }
            self.orders.append(order)
            self.business_ledger["orders"].append(order)
            if endpoint == "POST /api/concurrency/business":
                self.business_ledger["concurrency_orders"].append(order)
            return order


STORE = RiskStore()


class RiskLabHandler(BaseHTTPRequestHandler):
    server_version = "HighFidelityRiskLab/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        with STORE.lock:
            STORE.request_log.append(
                {
                    "at_ms": now_ms(),
                    "client": self.client_address[0],
                    "method": self.command,
                    "path": self.path,
                    "message": fmt % args,
                }
            )

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("content-length", "0") or "0")
        if not length:
            return {}
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _cookie_session_id(self) -> str:
        for item in self.headers.get("cookie", "").split(";"):
            name, _, value = item.strip().partition("=")
            if name == SESSION_COOKIE:
                return value
        return ""

    def _session(self) -> SessionState | None:
        session_id = self.headers.get("x-session-id", "") or self._cookie_session_id()
        return STORE.get_session(session_id) if session_id else None

    def _send_json(
        self,
        payload: dict[str, Any],
        status: int = 200,
        session: SessionState | None = None,
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        if session:
            self.send_header(
                "set-cookie",
                f"{SESSION_COOKIE}={session.session_id}; Path=/; SameSite=Lax",
            )
        self.end_headers()
        self.wfile.write(body)

    def _send_no_session(self) -> None:
        self._send_json(
            {
                "ok": False,
                "state": "backend_rejected",
                "failure_code": "missing_session",
                "reason": "call /api/session first",
            },
            status=401,
        )

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
        if parsed.path in {"/", "/index.html"}:
            self._serve_file("index.html")
            return
        if parsed.path == "/api/session":
            query = urllib.parse.parse_qs(parsed.query)
            worker_id = query.get("worker_id", [""])[0]
            session = STORE.create_session(worker_id=worker_id)
            self._send_json(
                {
                    "ok": True,
                    "state": session.state,
                    "session_id": session.session_id,
                    "worker_id": worker_id,
                    "states_seen": session.states_seen,
                },
                session=session,
            )
            return
        if parsed.path == "/api/list":
            session = self._session()
            if not session:
                self._send_no_session()
                return
            items = [
                {"id": "risk-item-1", "name": "Local Risk Item 1", "item_version": 1},
                {"id": "risk-item-2", "name": "Local Risk Item 2", "item_version": 1},
            ]
            STORE.record_list(session, items)
            self._send_json(
                {
                    "ok": True,
                    "state": session.state,
                    "items": items,
                    "session_id": session.session_id,
                }
            )
            return
        if parsed.path == "/api/detail":
            session = self._session()
            if not session:
                self._send_no_session()
                return
            query = urllib.parse.parse_qs(parsed.query)
            item_id = query.get("id", ["risk-item-1"])[0]
            item_version = session.listed_items.get(item_id)
            if item_version is None:
                self._send_json(
                    {
                        "ok": False,
                        "state": "backend_rejected",
                        "failure_code": "detail_without_list",
                        "reason": "detail item must come from current session list",
                    },
                    status=409,
                )
                return
            detail_nonce = STORE.record_detail(session, item_id, item_version)
            self._send_json(
                {
                    "ok": True,
                    "state": session.state,
                    "item": {
                        "id": item_id,
                        "name": f"Local Detail {item_id}",
                        "item_version": item_version,
                        "detail_nonce": detail_nonce,
                        "risk_lab": True,
                    },
                    "session_id": session.session_id,
                }
            )
            return
        if parsed.path == "/api/state":
            session = self._session()
            if not session:
                self._send_no_session()
                return
            self._send_json(
                {
                    "ok": True,
                    "state": session.state,
                    "session_id": session.session_id,
                    "verified_actions": sorted(session.verified_actions),
                    "states_seen": session.states_seen,
                    "all_states": ALL_STATES,
                }
            )
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        payload = self._read_json()
        if parsed.path == "/api/submit":
            self._handle_business_submit(payload)
            return
        if parsed.path == "/api/concurrency/business":
            self._handle_concurrency_business(payload)
            return
        if parsed.path == "/api/risk/challenge":
            self._handle_challenge(payload)
            return
        if parsed.path == "/api/risk/verify":
            self._handle_verify(payload)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def _handle_business_submit(self, payload: dict[str, Any]) -> None:
        session = self._session()
        if not session:
            self._send_no_session()
            return
        item_id = str(payload.get("item_id") or "")
        detail_nonce = str(payload.get("detail_nonce") or "")
        try:
            item_version = int(payload.get("item_version"))
        except Exception:
            item_version = -1
        if not STORE.record_business_hit(session):
            STORE.reject_submission(session, "POST /api/submit", "rate_limited", item_id=item_id)
            self._send_json(
                {
                    "ok": False,
                    "state": "rate_limited",
                    "failure_code": "rate_limited",
                    "reason": "too many business calls in this session",
                },
                status=429,
            )
            return
        if "submit" not in session.verified_actions:
            session.set_state("challenge_required")
            STORE.reject_submission(session, "POST /api/submit", "missing_verify", item_id=item_id)
            self._send_json(
                {
                    "ok": False,
                    "state": "challenge_required",
                    "failure_code": "missing_verify",
                    "reason": "submit requires risk verify first",
                    "business_api": "POST /api/submit",
                },
                status=403,
            )
            return
        if item_id not in session.listed_items:
            session.set_state("backend_rejected")
            STORE.reject_submission(session, "POST /api/submit", "wrong_item_source", item_id=item_id)
            self._send_json(
                {
                    "ok": False,
                    "state": "backend_rejected",
                    "failure_code": "wrong_item_source",
                    "reason": "submit item_id must come from current session list",
                },
                status=409,
            )
            return
        detail = session.detail_nonces.get(item_id)
        if not detail:
            session.set_state("backend_rejected")
            STORE.reject_submission(session, "POST /api/submit", "missing_detail", item_id=item_id)
            self._send_json(
                {
                    "ok": False,
                    "state": "backend_rejected",
                    "failure_code": "missing_detail",
                    "reason": "submit requires current-session detail visit",
                },
                status=409,
            )
            return
        if detail.get("detail_nonce") != detail_nonce:
            session.set_state("backend_rejected")
            STORE.reject_submission(session, "POST /api/submit", "wrong_detail_nonce", item_id=item_id)
            self._send_json(
                {
                    "ok": False,
                    "state": "backend_rejected",
                    "failure_code": "wrong_detail_nonce",
                    "reason": "detail_nonce must come from current session detail response",
                },
                status=409,
            )
            return
        if int(detail.get("item_version", -1)) != item_version:
            session.set_state("backend_rejected")
            STORE.reject_submission(session, "POST /api/submit", "stale_item_version", item_id=item_id)
            self._send_json(
                {
                    "ok": False,
                    "state": "backend_rejected",
                    "failure_code": "stale_item_version",
                    "reason": "item_version must match current detail response",
                },
                status=409,
            )
            return
        order = STORE.create_order(
            session,
            endpoint="POST /api/submit",
            item_id=item_id,
            item_version=item_version,
            detail_nonce=detail_nonce,
        )
        session.set_state("backend_accepted")
        self._send_json(
            {
                "ok": True,
                "state": "backend_accepted",
                "business_api": "POST /api/submit",
                "order_id": order["order_id"],
                "item_id": item_id,
                "item_version": item_version,
                "detail_nonce": detail_nonce,
                "session_id": session.session_id,
            }
        )

    def _handle_concurrency_business(self, payload: dict[str, Any]) -> None:
        session = self._session()
        if not session:
            self._send_no_session()
            return
        worker_id = str(payload.get("worker_id") or session.worker_id or "")
        if "business_concurrency" not in session.verified_actions:
            session.set_state("challenge_required")
            STORE.reject_submission(
                session,
                "POST /api/concurrency/business",
                "missing_verify",
                worker_id=worker_id,
            )
            self._send_json(
                {
                    "ok": False,
                    "state": "challenge_required",
                    "failure_code": "missing_verify",
                    "worker_id": worker_id,
                    "business_api": "POST /api/concurrency/business",
                },
                status=403,
            )
            return
        item_id = f"concurrency-item-{worker_id}-{payload.get('seq', 0)}"
        order = STORE.create_order(
            session,
            endpoint="POST /api/concurrency/business",
            item_id=item_id,
            item_version=1,
            detail_nonce=f"concurrency-detail-{worker_id}",
            worker_id=worker_id,
        )
        session.set_state("backend_accepted")
        self._send_json(
            {
                "ok": True,
                "state": "backend_accepted",
                "business_api": "POST /api/concurrency/business",
                "worker_id": worker_id,
                "session_id": session.session_id,
                "order_id": order["order_id"],
                "result_id": make_id("biz"),
            }
        )

    def _handle_challenge(self, payload: dict[str, Any]) -> None:
        session = self._session()
        if not session:
            self._send_no_session()
            return
        action = str(payload.get("action") or "submit")
        worker_id = str(payload.get("worker_id") or session.worker_id or "")
        ttl_ms = int(payload.get("ttl_ms") or TOKEN_TTL_MS)
        token = STORE.issue_token(session, action=action, worker_id=worker_id, ttl_ms=ttl_ms)
        self._send_json(
            {
                "ok": True,
                "state": "token_issued",
                "challenge_id": make_id("challenge"),
                "token": token.token,
                "nonce": token.nonce,
                "action": token.action,
                "worker_id": worker_id,
                "expires_at_ms": token.expires_at_ms,
                "server_generated": True,
                "one_time": True,
            }
        )

    def _handle_verify(self, payload: dict[str, Any]) -> None:
        session = self._session()
        if not session:
            self._send_no_session()
            return
        status, body = STORE.verify_token(
            session=session,
            token_value=str(payload.get("token") or ""),
            action=str(payload.get("action") or ""),
            nonce=str(payload.get("nonce") or ""),
            worker_id=str(payload.get("worker_id") or session.worker_id or ""),
        )
        self._send_json(body, status=status)


def make_server(host: str = "127.0.0.1", port: int = 0) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), RiskLabHandler)


def main() -> int:
    server = make_server()
    host, port = server.server_address
    print(json.dumps({"base_url": f"http://{host}:{port}"}, ensure_ascii=False), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
