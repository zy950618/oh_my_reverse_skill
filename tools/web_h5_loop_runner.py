#!/usr/bin/env python3
"""Create and validate Web/H5 Loop Engineering execution ledgers.

This runner manages the evidence ledger for Executor / Verifier / Governor
handoffs. It does not browse sites, bypass protections, or replace the
verifier/governor checks recorded in the ledger.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


REQUIRED_SCOPE = ["market", "locale", "currency", "stage", "auth_state", "target_api"]
REQUIRED_ROLES = ["executor", "verifier", "governor"]
REQUIRED_VERIFICATION = [
    "fresh_evidence",
    "clean_state_retest",
    "anti_flake",
    "concurrency_ladder",
    "session_cache_isolation",
    "risk_control",
    "data_acceptance",
    "fixture_freshness",
]
REQUIRED_WORKERS = ["worker_1", "worker_2", "worker_5", "worker_10"]
COMPLETE_FRESH_FIELDS = [
    "run_id",
    "capture_id",
    "captured_at",
    "network_log_id",
    "script_hash",
    "browser_profile_id",
    "state_reset",
]
RETEST_GROUPS = ["clean_unverified", "verified", "repeat_verified"]
BAD_EVIDENCE_VALUES = {None, "", "unknown", "unverified", "missing", "stale", "blocked"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def template(args: argparse.Namespace) -> dict:
    loop_id = args.loop_id or f"loop-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}"
    return {
        "loop_id": loop_id,
        "created_at": now_iso(),
        "domain": args.domain,
        "scope": {
            "market": args.market,
            "locale": args.locale,
            "currency": args.currency,
            "stage": args.stage,
            "auth_state": args.auth_state,
            "target_api": args.target_api,
        },
        "max_iterations": args.max_iterations,
        "stop_conditions": [
            "verifier_passed_and_governor_passed",
            "max_iterations",
            "repeated_blocker",
            "human_review_required",
            "risk_or_scope_boundary",
        ],
        "human_review_conditions": [
            "payment_or_order",
            "login_or_pii",
            "captcha_or_waf_manual_challenge",
            "evidence_conflict",
            "production_impact",
        ],
        "roles": {
            "executor": {"owner": "", "responsibility": "capture/reproduce/implement"},
            "verifier": {"owner": "", "responsibility": "fresh capture/replay/diff/schema/concurrency"},
            "governor": {"owner": "", "responsibility": "fact level/scope/isolation/risk/cleanup"},
        },
        "iterations": [],
        "verification": {
            "fresh_evidence": {
                "run_id": "",
                "capture_id": "",
                "captured_at": "",
                "network_log_id": "",
                "script_hash": "",
                "browser_profile_id": "",
                "state_reset": "",
                "source_freshness": "unknown",
            },
            "clean_state_retest": {
                "clean_unverified": {"status": "unverified", "evidence": ""},
                "verified": {"status": "unverified", "evidence": ""},
                "repeat_verified": {"status": "unverified", "evidence": ""},
            },
            "anti_flake": {"observations": [], "decision": "unverified"},
            "concurrency_ladder": {
                "worker_1": {"status": "unverified"},
                "worker_2": {"status": "unverified"},
                "worker_5": {"status": "unverified"},
                "worker_10": {"status": "unverified"},
            },
            "session_cache_isolation": {
                "cookie_jar": "isolated_by_default",
                "storage": "isolated_by_default",
                "token_cache": "isolated_by_default",
                "account_state": "isolated_by_default",
            },
            "risk_control": {
                "authorization_scope": "",
                "protected_business_api_acceptance": "",
                "failure_split": [],
                "backoff": "",
                "kill_switch": "",
                "human_review_boundary": "",
                "blocked_as_negative_eval": "",
            },
            "data_acceptance": {
                "ui_api_parity": "",
                "json_pointers": [],
                "consistency_rate": None,
                "adapter_target": "",
            },
            "fixture_freshness": {
                "strict_review_exit_code": None,
                "expired_count": None,
                "review_pending_count": None,
                "recent_report": False,
                "source_freshness": "unknown",
            },
        },
        "metrics": {
            "task_count": 0,
            "iterations_total": 0,
            "success_browserless_verified": 0,
            "concurrency_verified": 0,
            "flaky_count": 0,
            "blocked_by_protection": 0,
            "strict_review_pass_count": 0,
            "latest_replay_rate": None,
        },
        "stop_ledger": {
            "stop_reason": "unverified",
            "evidence": "",
            "remaining_gap": "",
            "safe_next_step": "",
        },
        "cleanup_ledger": {
            "removed": [],
            "kept_as_evidence": [],
            "migrated_to_memory": [],
            "still_unverified": [],
        },
    }


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def missing_path(payload: dict, path: list[str]) -> bool:
    cur = payload
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return True
        cur = cur[key]
    return False


def blankish(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in BAD_EVIDENCE_VALUES
    if isinstance(value, (list, dict)):
        return not value
    return False


def success_status(failures: list[str], blockers: list[str], require_complete: bool) -> str:
    if failures:
        return "FAIL"
    if require_complete:
        return "BLOCKED" if blockers else "SUCCESS_PASS"
    return "STRUCTURE_PASS"


def validate_ledger(payload: dict, require_complete: bool = False) -> dict:
    failures: list[str] = []
    blockers: list[str] = []
    warnings: list[str] = []

    for key in ["loop_id", "domain", "scope", "max_iterations", "stop_conditions", "human_review_conditions", "roles", "verification", "metrics", "stop_ledger", "cleanup_ledger"]:
        if key not in payload:
            failures.append(f"missing top-level key: {key}")

    for key in REQUIRED_SCOPE:
        if missing_path(payload, ["scope", key]):
            failures.append(f"missing scope.{key}")

    for role in REQUIRED_ROLES:
        if missing_path(payload, ["roles", role]):
            failures.append(f"missing role: {role}")

    for section in REQUIRED_VERIFICATION:
        if missing_path(payload, ["verification", section]):
            failures.append(f"missing verification.{section}")

    for worker in REQUIRED_WORKERS:
        if missing_path(payload, ["verification", "concurrency_ladder", worker]):
            failures.append(f"missing concurrency_ladder.{worker}")

    if not payload.get("stop_conditions"):
        failures.append("stop_conditions must not be empty")
    if not payload.get("human_review_conditions"):
        failures.append("human_review_conditions must not be empty")

    if require_complete:
        verifier_pass = False
        governor_pass = False
        for item in payload.get("iterations") or []:
            verifier_pass = verifier_pass or item.get("verifier_result") == "pass"
            governor_pass = governor_pass or item.get("governor_result") in {"pass", "stop_complete"}
        if not verifier_pass:
            blockers.append("require_complete: no verifier pass iteration")
        if not governor_pass:
            blockers.append("require_complete: no governor pass/stop_complete iteration")

        fresh = payload.get("verification", {}).get("fresh_evidence", {})
        for key in COMPLETE_FRESH_FIELDS:
            if blankish(fresh.get(key)):
                blockers.append(f"require_complete: fresh_evidence.{key} is missing")
        if fresh.get("source_freshness") != "fresh":
            blockers.append("require_complete: fresh_evidence.source_freshness must be fresh")

        retest = payload.get("verification", {}).get("clean_state_retest", {})
        for group in RETEST_GROUPS:
            if retest.get(group, {}).get("status") != "pass":
                blockers.append(f"require_complete: clean_state_retest.{group}.status must be pass")

        if payload.get("verification", {}).get("anti_flake", {}).get("decision") != "stable":
            blockers.append("require_complete: anti_flake.decision must be stable")

        risk = payload.get("verification", {}).get("risk_control", {})
        if blankish(risk.get("protected_business_api_acceptance")):
            blockers.append("require_complete: risk_control.protected_business_api_acceptance is missing")

        data = payload.get("verification", {}).get("data_acceptance", {})
        if blankish(data.get("ui_api_parity")):
            blockers.append("require_complete: data_acceptance.ui_api_parity is missing")
        if blankish(data.get("json_pointers")):
            blockers.append("require_complete: data_acceptance.json_pointers is missing")

        freshness = payload.get("verification", {}).get("fixture_freshness", {})
        if freshness.get("source_freshness") != "fresh":
            blockers.append("require_complete: fixture_freshness.source_freshness must be fresh")
        if freshness.get("strict_review_exit_code") != 0:
            blockers.append("require_complete: fixture_freshness.strict_review_exit_code must be 0")
        if freshness.get("expired_count") != 0:
            blockers.append("require_complete: fixture_freshness.expired_count must be 0")
        if freshness.get("review_pending_count") != 0:
            blockers.append("require_complete: fixture_freshness.review_pending_count must be 0")
        if freshness.get("recent_report") is not True:
            blockers.append("require_complete: fixture_freshness.recent_report must be true")

    freshness = payload.get("verification", {}).get("fixture_freshness", {})
    if freshness.get("source_freshness") in {None, "", "unknown"}:
        warnings.append("fixture freshness is not proven")

    status = success_status(failures, blockers, require_complete)
    return {
        "tool": "web_h5_loop_runner",
        "status": status,
        "failures": failures,
        "blockers": blockers,
        "warnings": warnings,
    }


def add_iteration(args: argparse.Namespace) -> dict:
    path = Path(args.ledger)
    payload = read_json(path)
    iterations = payload.setdefault("iterations", [])
    iteration_no = args.iteration or (len(iterations) + 1)
    iterations.append({
        "iteration": iteration_no,
        "started_at": now_iso(),
        "executor_action": args.executor_action,
        "executor_evidence": args.executor_evidence,
        "verifier_checks": args.verifier_checks,
        "verifier_result": args.verifier_result,
        "governor_checks": args.governor_checks,
        "governor_result": args.governor_result,
        "learning": args.learning,
        "memory_updates": args.memory_updates,
        "next_action": args.next_action,
    })
    payload.setdefault("metrics", {})["iterations_total"] = len(iterations)
    write_json(path, payload)
    return {"tool": "web_h5_loop_runner", "status": "UPDATED", "ledger": str(path), "iterations_total": len(iterations)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Create and validate Web/H5 Loop execution ledgers")
    sub = parser.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser("init", help="write a new loop ledger")
    init_p.add_argument("--out", required=True, help="output ledger JSON path")
    init_p.add_argument("--loop-id")
    init_p.add_argument("--domain", required=True)
    init_p.add_argument("--market", default="")
    init_p.add_argument("--locale", default="")
    init_p.add_argument("--currency", default="")
    init_p.add_argument("--stage", required=True)
    init_p.add_argument("--auth-state", default="anonymous")
    init_p.add_argument("--target-api", required=True)
    init_p.add_argument("--max-iterations", type=int, default=6)

    record_p = sub.add_parser("record-iteration", help="append one iteration record")
    record_p.add_argument("--ledger", required=True)
    record_p.add_argument("--iteration", type=int)
    record_p.add_argument("--executor-action", required=True)
    record_p.add_argument("--executor-evidence", default="")
    record_p.add_argument("--verifier-checks", default="")
    record_p.add_argument("--verifier-result", choices=["pass", "fail", "blocked"], default="blocked")
    record_p.add_argument("--governor-checks", default="")
    record_p.add_argument("--governor-result", choices=["continue", "pass", "stop", "stop_complete", "human_review"], default="continue")
    record_p.add_argument("--learning", default="")
    record_p.add_argument("--memory-updates", default="")
    record_p.add_argument("--next-action", default="")

    validate_p = sub.add_parser("validate", help="validate a loop ledger")
    validate_p.add_argument("--ledger", required=True)
    validate_p.add_argument("--require-complete", action="store_true")

    args = parser.parse_args()

    if args.command == "init":
        path = Path(args.out)
        payload = template(args)
        write_json(path, payload)
        print(json.dumps({"tool": "web_h5_loop_runner", "status": "CREATED", "ledger": str(path), "loop_id": payload["loop_id"]}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "record-iteration":
        print(json.dumps(add_iteration(args), ensure_ascii=False, indent=2))
        return 0

    payload = read_json(Path(args.ledger))
    result = validate_ledger(payload, require_complete=args.require_complete)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"STRUCTURE_PASS", "SUCCESS_PASS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
