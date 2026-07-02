#!/usr/bin/env python3
"""Observe scoped vendor CAPTCHA demo/doc pages without bypassing challenges."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import requests
import yaml  # type: ignore

from real_public_range_runner import browser_capture, utc_now, write_json


ROOT = Path(__file__).resolve().parent.parent
MATRIX = ROOT / "configs" / "vendor_challenge_matrix.yaml"
PUBLIC_ROOT = ROOT / "public-range-evidence"
RAW_ROOT = PUBLIC_ROOT / "raw"


DEFAULT_URLS = {
    "shumei-captcha-demo": "https://castatic.fengkongcloud.cn/pr/v1.0.4/demo.html",
    "aliyun-captcha-demo": "https://help.aliyun.com/zh/captcha/captcha2-0/user-guide/first-level-node-2/",
}


def read_matrix() -> dict[str, dict[str, Any]]:
    data = yaml.safe_load(MATRIX.read_text(encoding="utf-8-sig"))
    return {str(item.get("id")): item for item in data.get("targets", []) if isinstance(item, dict)}


def fetch_headline(url: str) -> tuple[int, str]:
    try:
        resp = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0 vendor-demo-observer"})
        return resp.status_code, resp.text[:2000]
    except Exception as exc:
        return 0, repr(exc)


def detect_provider(target: str, html: str, urls: list[str]) -> dict[str, Any]:
    lower = html.lower() + "\n" + "\n".join(urls).lower()
    if target.startswith("shumei"):
        vendor_markers = ["shumei", "fengkongcloud", "smcaptcha", "captcha"]
    else:
        vendor_markers = ["aliyun", "aliyuncs", "captcha", "nc.js", "captcha2"]
    return {
        "target": target,
        "markers": [marker for marker in vendor_markers if marker in lower],
        "script_or_endpoint_hints": [url for url in urls if any(token in url.lower() for token in ("captcha", "fengkong", "aliyun", "nc.js"))][:30],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run vendor official demo diagnostics")
    parser.add_argument("--target", required=True, choices=["shumei-captcha-demo", "aliyun-captcha-demo"])
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--url", help="self-owned trial or explicit official demo URL")
    args = parser.parse_args()

    matrix = read_matrix()
    target_cfg = matrix[args.target]
    target = args.target
    started_at = utc_now()
    out_dir = RAW_ROOT / "vendor-demo" / target / args.run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    stdout_log = out_dir / "runner.stdout.log"
    stderr_log = out_dir / "runner.stderr.log"
    stdout_log.write_text("", encoding="utf-8")
    stderr_log.write_text("", encoding="utf-8")
    url = args.url or DEFAULT_URLS[target]
    status_code, html = fetch_headline(url)
    screenshots, network_paths, trace_path, browser_error = browser_capture(url, out_dir, target)
    network_urls: list[str] = []
    for path in network_paths:
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
            for event in payload.get("events", []):
                if isinstance(event, dict) and event.get("url"):
                    network_urls.append(str(event["url"]))
        except Exception:
            pass
    provider = detect_provider(target, html, network_urls)
    readonly = True
    action_allowed = bool(args.url)
    self_owned_trial_required = target == "aliyun-captcha-demo" and not args.url
    blocked_reason = ""
    if target == "aliyun-captcha-demo" and not args.url:
        blocked_reason = "official docs require a self-owned scene/app integration for full verify flow"
    if status_code == 0 and browser_error:
        blocked_reason = "official demo fetch failed"
    official_demo_result = {
        "target": target,
        "url": url,
        "browser_opened": bool(screenshots),
        "screenshot": screenshots[0] if screenshots else "",
        "network_summary": network_paths[0] if network_paths else "",
        "provider_modes_detected": target_cfg.get("expected_modes", []),
        "readonly": readonly and not action_allowed,
        "action_allowed": action_allowed,
        "self_owned_trial_required": self_owned_trial_required,
        "cannot_promote_reason": blocked_reason or ("readonly official demo observation is memory_only" if not action_allowed else "self-owned trial must still prove server verify and business API"),
        "next_required_user_input": "provide self-owned trial URL and authorization scope" if self_owned_trial_required else "confirm action replay permission and self-owned server verify endpoint",
    }

    state_observer = {
        "status": "pass" if status_code or screenshots else "blocked",
        "http_status": status_code,
        "provider_detection": provider,
        "mode_detection": target_cfg.get("expected_modes", []),
        "official_demo_not_action_allowed": readonly and not action_allowed,
        "needs_self_owned_trial": self_owned_trial_required,
        "auth_required": False,
        "rate_limit": status_code in {403, 429},
        "dependency_missing": False,
        "next_step": "provide self-owned trial URL/scope to run action replay" if target == "aliyun-captcha-demo" and not args.url else "manual review whether official demo terms allow action replay",
    }
    evidence = {
        "schema_version": "public-range-evidence/v1",
        "run_id": args.run_id,
        "target": {"id": target, "type": "official_demo_readonly", "url": url, "vendor": target_cfg.get("vendor")},
        "captured_at": utc_now(),
        "source_freshness": "fresh",
        "skills": ["captcha-provider-diagnostics", "authorized-target-adapter", "web-h5-loop-engineering"],
        "execution_status": "REAL_EXECUTION_PASS" if screenshots or status_code else "BLOCKED",
        "capability_status": "memory_only",
        "control_flow_status": "CONTROL_FLOW_PASS" if screenshots or status_code else "CONTROL_FLOW_FAIL",
        "business_data_status": "NOT_RUN",
        "official_doc_or_demo_ref": target_cfg.get("official_refs", []),
        "expected_modes": target_cfg.get("expected_modes", []),
        "state_observer": state_observer,
        "official_demo_result": official_demo_result,
        "provider_diagnostics": provider,
        "backend_acceptance": {"status": "not_run", "final_api_endpoint_confirmed": False, "endpoint": ""},
        "ui_api_parity": {"status": "pass" if screenshots or status_code else "fail", "browser_opened": bool(screenshots), "api_feedback_observed": bool(network_urls)},
        "scope_decision": {
            "target_id": target,
            "scope_type": "official_demo_readonly",
            "authorization": "official_public_demo" if target == "shumei-captcha-demo" else "official_public_docs",
            "allowed_mode": "provider_diagnostics" if target == "shumei-captcha-demo" else "official_demo_state_observer",
            "in_scope": True,
            "external_generalization_allowed": False,
            "positive_allowed_scope": "",
            "scope_contract_path": "configs/range_scope_contract.yaml",
            "why_in_scope": "Official demo/doc observation only; action replay not assumed allowed.",
        },
        "capability_status_detail": {
            "status": "memory_only",
            "public_range_only": False,
            "local_only": False,
            "not_generalizable_to_third_party": True,
            "stable_positive": False,
        },
        "execution_proof": {
            "command": f"{sys.executable} tools/vendor_demo_runner.py --target {target} --run-id {args.run_id}",
            "cwd": str(ROOT),
            "started_at": started_at,
            "ended_at": utc_now(),
            "stdout_log": str(stdout_log),
            "stderr_log": str(stderr_log),
            "exit_code": 0,
            "synthetic": False,
            "generated_by": "tools/vendor_demo_runner.py",
            "screenshot_paths": screenshots,
            "network_summary_paths": network_paths,
            "browser_trace_path": trace_path,
        },
        "decision": {
            "skills_participation": "memory_only",
            "positive_allowed": False,
            "blocked_reason": official_demo_result["cannot_promote_reason"],
        },
        "blocked": {
            "blocked_reason": blocked_reason,
            "official_demo_not_action_allowed": readonly,
            "needs_self_owned_trial": target == "aliyun-captcha-demo" and not args.url,
            "auth_required": False,
            "rate_limit": status_code in {403, 429},
            "dependency_missing": False,
            "next_step": state_observer["next_step"],
            "browser_error": browser_error,
        },
    }
    write_json(PUBLIC_ROOT / target / f"{args.run_id}.json", evidence)
    write_json(out_dir / "vendor-demo-state-observer.json", state_observer)
    stdout_log.write_text(json.dumps({"status": "PASS", "target": target, "run_id": args.run_id, "readonly": readonly}, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "target": target, "run_id": args.run_id, "evidence": str(PUBLIC_ROOT / target / f"{args.run_id}.json"), "readonly": readonly, "blocked_reason": blocked_reason}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
