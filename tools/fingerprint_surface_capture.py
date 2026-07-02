#!/usr/bin/env python3
"""Capture observation-only browser fingerprint surfaces for the localhost lab."""
from __future__ import annotations

import argparse
import hashlib
import http.server
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
LAB_DIR = REPO_ROOT / "public-range-labs" / "realistic-captcha-risk-lab"
RAW_ROOT = REPO_ROOT / "public-range-evidence" / "raw" / "realistic-captcha-risk-lab"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


def start_server() -> tuple[http.server.ThreadingHTTPServer, str]:
    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(LAB_DIR), **kwargs)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    host, port = server.server_address
    return server, f"http://{host}:{port}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture fingerprint surface")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--longrun-verify", action="store_true", help="Record this invocation as a Phase 3.5 longrun verification pass.")
    args = parser.parse_args()
    raw_dir = RAW_ROOT / args.run_id
    raw_dir.mkdir(parents=True, exist_ok=True)
    server, base_url = start_server()
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto(base_url + "/", wait_until="networkidle")
            surface = page.evaluate(
                """async () => {
                  const canvas = document.createElement('canvas');
                  canvas.width = 64; canvas.height = 24;
                  const ctx = canvas.getContext('2d');
                  ctx.fillText('surface', 3, 16);
                  let webgl = {};
                  try {
                    const gl = canvas.getContext('webgl');
                    const dbg = gl && gl.getExtension('WEBGL_debug_renderer_info');
                    webgl = dbg ? { vendor: gl.getParameter(dbg.UNMASKED_VENDOR_WEBGL), renderer: gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) } : {};
                  } catch (e) { webgl = { error: String(e) }; }
                  let permission = 'not_run';
                  try { permission = (await navigator.permissions.query({ name: 'notifications' })).state; } catch (e) { permission = 'unavailable'; }
                  return {
                    navigator: {
                      webdriver: navigator.webdriver,
                      userAgent: navigator.userAgent,
                      platform: navigator.platform,
                      languages: navigator.languages,
                      plugins: Array.from(navigator.plugins || []).map(p => p.name),
                      hardwareConcurrency: navigator.hardwareConcurrency,
                      deviceMemory: navigator.deviceMemory || null
                    },
                    screen: { width: screen.width, height: screen.height, colorDepth: screen.colorDepth },
                    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                    locale: Intl.DateTimeFormat().resolvedOptions().locale,
                    canvasDataUrlLength: canvas.toDataURL().length,
                    webgl,
                    permissions: { notifications: permission },
                    webrtcAvailable: typeof RTCPeerConnection !== 'undefined',
                    clientHintsAvailable: Boolean(navigator.userAgentData),
                    storage: { localStorage: typeof localStorage !== 'undefined', sessionStorage: typeof sessionStorage !== 'undefined' }
                  };
                }"""
            )
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    report = {
        "run_id": args.run_id,
        "browser_profile_id": "playwright-default-isolated-context",
        "runtime_type": "playwright-chromium",
        "surface_values": surface,
        "surface_hash": sha256_json(surface),
        "drift_from_baseline": "baseline_created",
        "observed_signals": {
            "webdriver_exposed": surface["navigator"].get("webdriver") is True,
            "client_hints_available": surface.get("clientHintsAvailable"),
            "webrtc_available": surface.get("webrtcAvailable"),
        },
        "derived_risk": ["automation_related_anomaly_observed"] if surface["navigator"].get("webdriver") else [],
        "assumed": [],
        "unverified": ["TLS/JA3/JA4 not measured by local browser script"],
        "block_reason": "not_blocked_localhost_observation",
        "allowed_action": ["observation_only", "profile_isolation", "authorized_lab_regression", "memory_only"],
        "forbidden_action": ["webdriver_hide", "fingerprint_spoof", "proxy_rotation_evasion", "clearance_cookie_reuse", "waf_bypass", "risk_token_reuse", "unauthorized_challenge_processing"],
    }
    path = raw_dir / "fingerprint-surface-report.json"
    write_json(path, report)
    print(json.dumps({"status": "PASS", "run_id": args.run_id, "surface_hash": report["surface_hash"], "report_path": str(path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
