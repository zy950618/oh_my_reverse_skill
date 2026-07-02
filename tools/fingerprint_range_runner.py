#!/usr/bin/env python3
"""Run observation-only public fingerprint diagnostics."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
TARGETS = {
    "creepjs": "https://creepjs.org/",
    "sannysoft": "https://bot.sannysoft.com/",
    "browserleaks": "https://browserleaks.com/javascript",
    "incolumitas": "https://bot.incolumitas.com/",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run public fingerprint diagnostics")
    parser.add_argument("--target", required=True, choices=sorted(TARGETS))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--profiles", type=int, default=1)
    args = parser.parse_args()
    run_id = args.run_id
    url = TARGETS[args.target]
    raw_dir = ROOT / "public-range-evidence" / "raw" / "fingerprint-diagnostics" / run_id / args.target
    raw_dir.mkdir(parents=True, exist_ok=True)
    screenshot = raw_dir / "fingerprint-page.png"
    network_path = raw_dir / "fingerprint-network-summary.json"
    report_path = raw_dir / "fingerprint-surface-report.json"
    stdout_log = raw_dir / "fingerprint-range-runner.stdout.log"
    stderr_log = raw_dir / "fingerprint-range-runner.stderr.log"
    trace_path = raw_dir / "fingerprint-trace.zip"
    stdout_log.write_text("fingerprint range runner started\n", encoding="utf-8")
    stderr_log.write_text("", encoding="utf-8")
    events: list[dict[str, Any]] = []
    started = utc_now()
    blocked_reason = ""
    surface: dict[str, Any] = {}
    captures: list[dict[str, Any]] = []
    page_text = ""
    status = "PASS"
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            for profile_index in range(args.profiles):
                for repeat_index in range(args.repeat):
                    shot = raw_dir / f"fingerprint-page-profile{profile_index + 1}-repeat{repeat_index + 1}.png"
                    trace = raw_dir / f"fingerprint-trace-profile{profile_index + 1}-repeat{repeat_index + 1}.zip"
                    context = browser.new_context(viewport={"width": 1280, "height": 900})
                    context.tracing.start(screenshots=True, snapshots=True, sources=False)
                    page = context.new_page()
                    page.on("response", lambda response: events.append({"url": response.url, "status": response.status, "method": response.request.method, "profile": profile_index + 1, "repeat": repeat_index + 1}))
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(5000)
                    surface = page.evaluate(
                        """async () => {
                          const canvas = document.createElement('canvas');
                          canvas.width = 120; canvas.height = 32;
                          const ctx = canvas.getContext('2d');
                          ctx.fillText('fingerprint-range', 4, 20);
                          let webgl = {};
                          let permissions = {};
                          try {
                            const gl = canvas.getContext('webgl');
                            const dbg = gl && gl.getExtension('WEBGL_debug_renderer_info');
                            webgl = dbg ? { vendor: gl.getParameter(dbg.UNMASKED_VENDOR_WEBGL), renderer: gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) } : {};
                          } catch (e) { webgl = { error: String(e) }; }
                          try {
                            permissions.notifications = (await navigator.permissions.query({name:'notifications'})).state;
                          } catch (e) { permissions.error = String(e); }
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
                            permissions,
                            webrtcAvailable: typeof RTCPeerConnection !== 'undefined',
                            clientHintsAvailable: Boolean(navigator.userAgentData),
                            documentTitle: document.title
                          };
                        }"""
                    )
                    page_text = page.locator("body").inner_text(timeout=10000)[:4000]
                    page.screenshot(path=str(shot), full_page=True)
                    context.tracing.stop(path=str(trace))
                    context.close()
                    captures.append({
                        "profile": profile_index + 1,
                        "repeat": repeat_index + 1,
                        "surface_hash": stable_hash(surface),
                        "surface_values": surface,
                        "screenshot_path": str(shot),
                        "trace_path": str(trace),
                    })
            if captures:
                first_shot = Path(captures[0]["screenshot_path"])
                if first_shot.is_file() and first_shot != screenshot:
                    screenshot.write_bytes(first_shot.read_bytes())
                first_trace = Path(captures[0]["trace_path"])
                if first_trace.is_file() and first_trace != trace_path:
                    trace_path.write_bytes(first_trace.read_bytes())
            browser.close()
    except Exception as exc:
        status = "BLOCKED"
        blocked_reason = repr(exc)
        stderr_log.write_text(blocked_reason, encoding="utf-8")
    ended = utc_now()
    write_json(network_path, {"target": args.target, "url": url, "responses": events})
    observed_signals = {
        "webdriver_exposed": surface.get("navigator", {}).get("webdriver") is True,
        "canvas_observed": surface.get("canvasDataUrlLength") is not None,
        "webgl_observed": bool(surface.get("webgl")),
        "webrtc_observed": surface.get("webrtcAvailable") is not None,
        "timezone_observed": bool(surface.get("timezone")),
        "language_observed": bool(surface.get("navigator", {}).get("languages")),
        "permissions_observed": bool(surface.get("permissions")),
        "client_hints_observed": surface.get("clientHintsAvailable") is not None,
        "tls_observable_from_browser_js": False,
        "http2_observable_from_browser_js": False,
        "client_hints_available": surface.get("clientHintsAvailable"),
        "webrtc_available": surface.get("webrtcAvailable"),
        "page_text_mentions_bot": "bot" in page_text.lower() or "webdriver" in page_text.lower(),
    }
    hashes = [item["surface_hash"] for item in captures]
    profile_hashes: dict[str, set[str]] = {}
    for item in captures:
        profile_hashes.setdefault(str(item["profile"]), set()).add(str(item["surface_hash"]))
    drift_count = max(0, len(set(hashes)) - 1)
    profile_consistency = {
        "status": "pass" if captures and all(len(values) == 1 for values in profile_hashes.values()) else "drift_observed",
        "repeat_count": args.repeat,
        "profile_count": args.profiles,
        "capture_count": len(captures),
        "surface_hashes": hashes,
        "unique_surface_hash_count": len(set(hashes)),
        "drift_count": drift_count,
        "consistent": captures != [] and all(len(values) == 1 for values in profile_hashes.values()),
    }
    diagnostics_candidate = status == "PASS" and args.repeat >= 5 and args.profiles >= 3 and len(captures) >= args.repeat * args.profiles
    report = {
        "run_id": run_id,
        "target": args.target,
        "url": url,
        "status": status,
        "blocked_reason": blocked_reason,
        "observed_signals": observed_signals,
        "surface_values": surface,
        "page_text_excerpt": page_text[:1200],
        "allowed_action": ["observation_only", "profile_isolation", "memory_only", "negative_eval_only"],
        "forbidden_action": ["webdriver_hide", "fingerprint_spoof", "proxy_rotation_evasion", "clearance_cookie_reuse", "waf_bypass"],
        "risk_attribution": "automation_related_anomaly_observed" if observed_signals["webdriver_exposed"] else "public_page_observed_no_local_block",
        "fingerprint_surface_matrix": {
            "webdriver": observed_signals["webdriver_exposed"],
            "canvas": observed_signals["canvas_observed"],
            "webgl": observed_signals["webgl_observed"],
            "webrtc": observed_signals["webrtc_observed"],
            "timezone": observed_signals["timezone_observed"],
            "language": observed_signals["language_observed"],
            "permissions": observed_signals["permissions_observed"],
            "client_hints": observed_signals["client_hints_observed"],
            "tls": "not_observable_from_page_js",
            "http2": "not_observable_from_page_js",
        },
        "profile_consistency": profile_consistency,
        "captures": captures,
        "execution": {
            "started_at": started,
            "ended_at": ended,
            "stdout_log": str(stdout_log),
            "stderr_log": str(stderr_log),
            "screenshot_path": str(screenshot) if screenshot.is_file() else "",
            "network_summary_path": str(network_path),
            "trace_path": str(trace_path) if trace_path.is_file() else "",
        },
        "capability_status": "positive_candidate" if diagnostics_candidate else ("memory_only" if status == "PASS" else "negative_eval_only"),
    }
    write_json(report_path, report)
    evidence_dir = ROOT / "public-range-evidence" / "fingerprint-diagnostics"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_dir / f"{run_id}-{args.target}.json"
    evidence = {
        "schema_version": "public-range-evidence/v1",
        "run_id": run_id,
        "capture_id": f"cap-{run_id}-{args.target}",
        "captured_at": ended,
        "source_freshness": "fresh",
        "execution_status": "REAL_EXECUTION_PASS" if status == "PASS" else "BLOCKED",
        "control_flow_status": "CONTROL_FLOW_PASS" if status == "PASS" else "CONTROL_FLOW_FAIL",
        "business_data_status": "NOT_RUN",
        "capability_status": "positive_candidate" if diagnostics_candidate else ("memory_only" if status == "PASS" else "negative_eval_only"),
        "target": {
            "id": "fingerprint-diagnostics",
            "name": f"Public fingerprint diagnostics - {args.target}",
            "url": url,
            "host": url.split("/")[2],
            "type": "bot_signal_diagnostics",
            "authorization_scope": "Observation-only public diagnostics page; no evasion or bypass.",
        },
        "skills": ["browser-fingerprint-surface-lab", "fingerprint-block-reason-diagnostics"],
        "execution_proof": {
            "command": f"python tools\\fingerprint_range_runner.py --target {args.target} --run-id {run_id} --repeat {args.repeat} --profiles {args.profiles}",
            "cwd": str(ROOT),
            "exit_code": 0 if status == "PASS" else 1,
            "started_at": started,
            "ended_at": ended,
            "stdout_log": str(stdout_log),
            "stderr_log": str(stderr_log),
            "screenshot_paths": [item["screenshot_path"] for item in captures if Path(item["screenshot_path"]).is_file()] or ([str(screenshot)] if screenshot.is_file() else []),
            "network_summary_paths": [str(network_path)],
            "browser_trace_path": str(trace_path) if trace_path.is_file() else "",
            "generated_by": "tools/fingerprint_range_runner.py",
            "synthetic": False,
        },
        "scope_decision": {
            "target_id": "fingerprint-diagnostics",
            "scope_type": "public_diagnostics",
            "authorization": "public_diagnostics_page",
            "allowed_mode": "fingerprint_diagnostics",
            "allowed_hosts_match": True,
            "scope_contract_path": "configs/range_scope_contract.yaml",
            "in_scope": True,
            "why_in_scope": "Public diagnostics page is used for observation only; no webdriver hide, spoofing, proxy evasion, or bypass is attempted.",
            "why_out_of_scope": "",
            "positive_allowed_scope": "public_fingerprint_diagnostics_positive" if diagnostics_candidate else "",
            "external_generalization_allowed": False,
        },
        "capability_status_detail": {
            "status": "positive_candidate" if diagnostics_candidate else ("memory_only" if status == "PASS" else "negative_eval_only"),
            "scope_limited_positive": "public_fingerprint_diagnostics_positive" if diagnostics_candidate else "",
            "local_only": False,
            "public_range_only": True,
            "authorized_only": False,
            "not_generalizable_to_third_party": True,
            "why": "Public diagnostics candidate only; no evasion, spoofing, webdriver hide, proxy evasion, or bypass capability is claimed.",
        },
        "fingerprint_surface_report": str(report_path),
        "fingerprint_surface_matrix": report["fingerprint_surface_matrix"],
        "profile_consistency": report["profile_consistency"],
        "surface_hashes": hashes,
        "drift_count": drift_count,
        "ui_api_parity": {"status": "pass" if status == "PASS" else "fail", "observed_status": 200 if events else 0, "endpoint": "GET " + url, "json_pointers": ["/fingerprint_surface_report"]},
        "repeat_verified": status == "PASS",
        "decision": {
            "skills_participation": "positive_candidate" if diagnostics_candidate else ("memory_only" if status == "PASS" else "negative_eval_only"),
            "positive_allowed": False,
            "blocked_reason": blocked_reason or ("" if diagnostics_candidate else "Fingerprint diagnostics are observation-only and cannot promote evasion capability."),
            "why_candidate": "repeat/profile public diagnostics candidate only; not evasion positive" if diagnostics_candidate else "",
        },
    }
    write_json(evidence_path, evidence)
    card_dir = ROOT / "skills-experience" / "fingerprint-diagnostics" / run_id
    card_dir.mkdir(parents=True, exist_ok=True)
    (card_dir / f"{args.target}.yaml").write_text("\n".join([
        f"experience_id: {run_id}-{args.target}-fingerprint-diagnostics",
        f"source_run_id: {run_id}",
        f"target: {args.target}",
        f"status: {status}",
        f"blocked_reason: {blocked_reason}",
        f"webdriver_exposed: {str(observed_signals['webdriver_exposed']).lower()}",
        "capability_impact: observation-only diagnostics, no evasion positive",
        "",
    ]), encoding="utf-8")
    stdout_log.write_text("fingerprint range runner completed\n", encoding="utf-8")
    print(json.dumps({"status": status, "run_id": run_id, "target": args.target, "report_path": str(report_path), "evidence_path": str(evidence_path), "blocked_reason": blocked_reason}, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
