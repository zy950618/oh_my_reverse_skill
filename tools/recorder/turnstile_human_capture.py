from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


DEFAULT_URL = "https://test.cap.guru/demo/cloud#cloud1"
DEFAULT_SITEKEY = "0x4AAAAAAAFgtad7pcAaTILY"
DEFAULT_TOKEN_TEXTAREA = f"f_textarea_{DEFAULT_SITEKEY}"


def now_local_iso() -> str:
    return dt.datetime.now(dt.datetime.now().astimezone().tzinfo).isoformat(timespec="seconds")


def safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("_")


def find_default_browser() -> str | None:
    candidates = [
        Path.home() / "AppData/Local/ms-playwright/chromium-1208/chrome-win64/chrome.exe",
        Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
        Path("C:/Program Files/Microsoft/Edge/Application/msedge.exe"),
        Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def read_dom_state(page: Any, token_textarea_id: str) -> dict[str, Any]:
    return page.evaluate(
        """(tokenTextAreaId) => {
            const turnstileField = document.querySelector('input[name="cf-turnstile-response"]');
            const siteTextArea = document.getElementById(tokenTextAreaId);
            const resultText = Array.from(document.querySelectorAll('body *'))
                .map((el) => el.innerText || '')
                .filter((text) => /RESULT:|status|success|fail/i.test(text))
                .slice(-10)
                .join('\\n')
                .slice(0, 2000);
            return {
                url: location.href,
                title: document.title,
                bodyText: document.body ? document.body.innerText.slice(0, 4000) : '',
                turnstileResponseLen: turnstileField && turnstileField.value ? turnstileField.value.length : 0,
                siteTextAreaLen: siteTextArea && siteTextArea.value ? siteTextArea.value.length : 0,
                resultText,
                cookiePresent: document.cookie ? true : false,
                localStorageKeys: Object.keys(localStorage || {}),
                sessionStorageKeys: Object.keys(sessionStorage || {}),
            };
        }""",
        token_textarea_id,
    )


def summarize_storage_state(storage_state: dict[str, Any]) -> dict[str, Any]:
    return {
        "cookies": [
            {
                "name": cookie.get("name"),
                "domain": cookie.get("domain"),
                "path": cookie.get("path"),
                "expires": cookie.get("expires"),
                "httpOnly": cookie.get("httpOnly"),
                "secure": cookie.get("secure"),
                "sameSite": cookie.get("sameSite"),
            }
            for cookie in storage_state.get("cookies", [])
        ],
        "origins": [
            {
                "origin": origin.get("origin"),
                "localStorageKeys": [item.get("name") for item in origin.get("localStorage", [])],
            }
            for origin in storage_state.get("origins", [])
        ],
    }


def parse_backend_status(body: str) -> str | None:
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return None
    status = data.get("status")
    return status if isinstance(status, str) else None


def capture(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    browser_executable = args.browser_executable or find_default_browser()
    if not browser_executable:
        raise SystemExit("No Chrome/Edge executable found. Pass --browser-executable.")

    profile_dir = Path(args.profile_dir) if args.profile_dir else Path(tempfile.mkdtemp(prefix="turnstile-human-"))
    profile_dir.mkdir(parents=True, exist_ok=True)

    capture_id = args.capture_id or f"{args.round}_{safe_name(now_local_iso())}"
    har_path = out_dir / f"{capture_id}.har"
    screenshot_path = out_dir / f"{capture_id}.png"
    summary_path = out_dir / f"{capture_id}.summary.json"

    if args.dry_run:
        print(
            json.dumps(
                {
                    "url": args.url,
                    "round": args.round,
                    "out_dir": str(out_dir),
                    "profile_dir": str(profile_dir),
                    "browser_executable": browser_executable,
                    "har": str(har_path),
                    "summary": str(summary_path),
                    "screenshot": str(screenshot_path),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    request_log: list[dict[str, Any]] = []
    response_log: list[dict[str, Any]] = []
    backend_responses: list[dict[str, Any]] = []
    console_log: list[dict[str, str]] = []

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            executable_path=browser_executable,
            headless=False,
            viewport={"width": 1365, "height": 900},
            record_har_path=str(har_path),
            record_har_content="omit",
        )
        page = context.pages[0] if context.pages else context.new_page()

        def on_request(req: Any) -> None:
            post_data = req.post_data
            request_log.append(
                {
                    "url": req.url,
                    "method": req.method,
                    "resourceType": req.resource_type,
                    "postData": f"[redacted:{len(post_data)} chars]" if post_data else None,
                }
            )

        def on_response(res: Any) -> None:
            rec = {
                "url": res.url,
                "status": res.status,
                "resourceType": res.request.resource_type,
                "contentType": res.headers.get("content-type"),
            }
            response_log.append(rec)
            if "/proverka.php" in res.url:
                body = ""
                try:
                    body = res.text()
                except Exception:
                    body = ""
                backend_responses.append({**rec, "body": body[:500], "jsonStatus": parse_backend_status(body)})

        page.on("request", on_request)
        page.on("response", on_response)
        page.on("console", lambda msg: console_log.append({"type": msg.type, "text": msg.text[:500]}))

        print(f"[capture] Opening visible browser: {args.url}")
        print("[capture] Complete only the visible Turnstile challenge. Do not perform out-of-scope actions.")
        print("[capture] Token values are not stored; only token lengths and backend status are recorded.")
        page.goto(args.url, wait_until="domcontentloaded", timeout=args.nav_timeout_ms)

        started = time.time()
        while time.time() - started < args.timeout_sec:
            state = read_dom_state(page, args.token_textarea_id)
            token_seen = bool(state["turnstileResponseLen"] or state["siteTextAreaLen"])
            if token_seen and args.auto_submit and not backend_responses:
                try:
                    page.locator("input.sendVerif").click(timeout=3000)
                except PlaywrightTimeoutError:
                    pass
            backend_success = any(item.get("jsonStatus") == args.expected_status for item in backend_responses)
            if backend_success or (token_seen and not args.require_backend_success):
                break
            time.sleep(args.poll_interval_sec)

        final_state = read_dom_state(page, args.token_textarea_id)
        storage_summary = summarize_storage_state(context.storage_state())
        page.screenshot(path=str(screenshot_path), full_page=True)
        context.close()

    backend_success = any(item.get("jsonStatus") == args.expected_status for item in backend_responses)
    summary = {
        "capture_id": capture_id,
        "captured_at": now_local_iso(),
        "round": args.round,
        "url": args.url,
        "browser_profile_id": str(profile_dir),
        "state_reset": "caller supplied profile_dir" if args.profile_dir else "new temporary profile directory",
        "auth_state": "anonymous_human_reviewed",
        "sitekey": args.sitekey,
        "token_textarea_id": args.token_textarea_id,
        "token_state": {
            "turnstileResponseLen": final_state["turnstileResponseLen"],
            "siteTextAreaLen": final_state["siteTextAreaLen"],
            "tokenValuesStored": False,
        },
        "backend_responses": backend_responses,
        "completion": {
            "token_seen": bool(final_state["turnstileResponseLen"] or final_state["siteTextAreaLen"]),
            "backend_success": backend_success,
            "expected_status": args.expected_status,
            "status": "verified" if backend_success else "blocked_or_incomplete",
        },
        "dom_state": final_state,
        "storage_summary": storage_summary,
        "requests": request_log,
        "responses": response_log,
        "console": console_log,
        "artifacts": {
            "har": str(har_path),
            "screenshot": str(screenshot_path),
            "summary": str(summary_path),
        },
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary["completion"], ensure_ascii=False, indent=2))
    print(f"[capture] wrote {summary_path}")
    return 0 if backend_success else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Visible-browser human-reviewed Turnstile capture. Records evidence; does not solve or bypass CAPTCHA."
    )
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--round", choices=["verified", "repeat_verified"], default="verified")
    parser.add_argument(
        "--out-dir",
        default="metrics/captures/test.cap.guru/cloud1/run_20260615T115700_test_cap_guru_cloud1/human_review",
    )
    parser.add_argument("--capture-id")
    parser.add_argument("--profile-dir")
    parser.add_argument("--browser-executable")
    parser.add_argument("--sitekey", default=DEFAULT_SITEKEY)
    parser.add_argument("--token-textarea-id", default=DEFAULT_TOKEN_TEXTAREA)
    parser.add_argument("--timeout-sec", type=int, default=180)
    parser.add_argument("--poll-interval-sec", type=float, default=1.0)
    parser.add_argument("--nav-timeout-ms", type=int, default=30000)
    parser.add_argument("--expected-status", default="success")
    parser.add_argument("--auto-submit", action="store_true", help="Click the page Verif button after a token appears.")
    parser.add_argument(
        "--require-backend-success",
        action="store_true",
        help="Wait for /proverka.php /status to match --expected-status, not just token presence.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    return capture(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
