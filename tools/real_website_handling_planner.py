#!/usr/bin/env python3
"""Create a scope-aware handling plan for a real website or lab target."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from typing import Any


ROOT = Path(__file__).resolve().parent.parent


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def decide(scope: str, target_type: str) -> dict[str, Any]:
    observation_only = scope in {"unknown", "official_demo"}
    full_workflow = scope in {"localhost", "public_range", "self_owned", "authorized"}
    if scope == "official_demo":
        allowed = ["browser_open", "screenshot", "network_summary", "provider_mode_detection", "readonly_state_observation"]
        forbidden = ["action_replay_without_permission", "server_verify_claim", "business_api_positive_claim", "bypass_or_evasion"]
        auth_required = "action replay requires explicit official demo permission or self-owned trial"
        default_status = "memory_only"
    elif scope == "unknown":
        allowed = ["browser_open", "screenshot", "passive_network_summary", "provider_detection", "risk_signal_observation"]
        forbidden = ["captcha_solving", "waf_bypass", "fingerprint_spoof", "webdriver_hide", "clearance_reuse", "rate_limit_evasion", "credentialed_actions"]
        auth_required = "authorization required before interaction, replay, or business API validation"
        default_status = "memory_only"
    else:
        allowed = ["browser_open", "screenshot", "network_summary", "action_replay_if_in_scope", "server_verify", "business_api_assertions", "negative_eval", "concurrency_ladder"]
        forbidden = ["out_of_scope_hosts", "credential_reuse", "proxy_evasion", "fingerprint_spoof", "production_load_test_without_written_limit"]
        auth_required = "" if scope in {"localhost", "public_range"} else "written authorization and allowed_hosts required"
        default_status = "positive_candidate" if full_workflow and target_type != "fingerprint" else "memory_only"
    if target_type == "fingerprint":
        forbidden.extend(["fingerprint_evasion_positive_claim", "spoofing_or_webdriver_hide"])
        default_status = "memory_only" if scope in {"unknown", "official_demo"} else "positive_candidate_diagnostics_only"
    return {
        "scope_decision": "observation_only" if observation_only else "full_workflow_allowed_with_scope_controls",
        "allowed_actions": allowed,
        "forbidden_actions": sorted(set(forbidden)),
        "authorization_required": auth_required,
        "capability_status_default": default_status,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build scope-aware real website handling plan")
    parser.add_argument("--url", required=True)
    parser.add_argument("--declared-scope", "--scope", dest="declared_scope", required=True, choices=["localhost", "public_range", "official_demo", "self_owned", "authorized", "unknown"])
    parser.add_argument("--target-type", required=True, choices=["captcha", "waf", "fingerprint", "js_runtime", "business_api"])
    parser.add_argument("--run-id", default="")
    args = parser.parse_args()

    parsed = urlparse(args.url)
    host = parsed.netloc or parsed.path
    decision = decide(args.declared_scope, args.target_type)
    run_id = args.run_id or "manual-" + hashlib.sha256(f"{args.url}|{args.declared_scope}|{args.target_type}".encode()).hexdigest()[:12]
    provider_detection_plan = {
        "captcha": ["script and endpoint marker inventory", "official provider marker mapping", "no DOM answer read"],
        "waf": ["redirect chain", "cookie clearance names", "retry-after/rate-limit headers", "business endpoint closure"],
        "fingerprint": ["webdriver/canvas/webgl/webrtc/timezone/language/permissions/client-hints", "surface hash repeat", "no spoofing"],
        "js_runtime": ["Browser/Node/PageRuntime parity", "mutation inputs", "missing API contract"],
        "business_api": ["browser request discovery", "direct repeat", "business data assertions", "negative eval"],
    }[args.target_type]
    plan = {
        "schema_version": "real-website-handling-plan/v1",
        "run_id": run_id,
        "created_at": utc_now(),
        "url": args.url,
        "host": host,
        "declared_scope": args.declared_scope,
        "target_type": args.target_type,
        **decision,
        "provider_detection_plan": provider_detection_plan,
        "risk_detection_plan": ["status code and block page classification", "network summary", "server feedback", "scope drift check"],
        "evidence_required": ["screenshot", "network_summary", "trace_or_command_log", "execution_status", "capability_status", "scope_decision"],
        "stop_condition": ["host leaves declared scope", "403/429/503 rate-limit escalation", "auth wall appears without provided authorization", "business ledger mismatch", "human review required"],
        "human_in_loop": args.declared_scope in {"official_demo", "self_owned", "authorized", "unknown"},
        "official_api_fallback": args.target_type in {"captcha", "waf", "fingerprint"},
        "business_data_required": args.target_type in {"waf", "business_api", "captcha"},
        "blocked_authorization_required": bool(decision["authorization_required"]) and args.declared_scope in {"unknown", "official_demo", "self_owned", "authorized"},
        "bypass_guidance": "prohibited",
    }
    slug = hashlib.sha256(f"{args.url}|{args.declared_scope}|{args.target_type}".encode()).hexdigest()[:12]
    out = ROOT / "public-range-evidence" / "raw" / "real-website-handling-planner" / run_id / f"{slug}.json"
    write_json(out, plan)
    print(json.dumps({"status": "PASS", "run_id": run_id, "plan_path": str(out), "scope_decision": plan["scope_decision"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
