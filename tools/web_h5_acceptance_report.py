#!/usr/bin/env python3
"""Create and validate Web/H5 crawler acceptance reports.

The report is an evidence contract for authorized Web/H5 crawler work:
clean-state retest, anti-flake, concurrency ladder, risk-control handling,
UI/API parity, fixture freshness, and quantitative metrics.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


REQUIRED_TOP = [
    "scope",
    "fresh_evidence",
    "clean_state_retest",
    "anti_flake",
    "concurrency_ladder",
    "session_cache_isolation",
    "risk_control",
    "data_acceptance",
    "fixtures_freshness",
    "metrics",
    "decision",
]
REQUIRED_FRESH = [
    "run_id",
    "capture_id",
    "captured_at",
    "browser_profile_id",
    "state_reset",
    "network_log_id",
    "script_hash",
    "auth_state",
    "source_freshness",
]
RETEST_GROUPS = ["clean_unverified", "verified", "repeat_verified"]
WORKERS = ["worker_1", "worker_2", "worker_5", "worker_10"]
RISK_KEYS = [
    "authorization_scope",
    "protected_business_api_acceptance",
    "failure_split",
    "backoff",
    "jitter",
    "session_retirement",
    "kill_switch",
    "human_review_boundary",
    "blocked_as_negative_eval",
]
DATA_KEYS = ["ui_api_parity", "json_pointers", "consistency_rate", "adapter_target"]
FRESHNESS_KEYS = ["strict_review_exit_code", "expired_count", "review_pending_count", "recent_report", "source_freshness"]
METRIC_KEYS = [
    "task_count",
    "success_browserless_verified",
    "concurrency_verified",
    "strict_review_pass_count",
    "flaky_count",
    "blocked_by_protection",
    "latest_replay_rate",
]
BAD_EVIDENCE_VALUES = {None, "", "unknown", "unverified", "missing", "stale", "blocked"}
SUCCESS_DECISIONS = {"success", "pass", "stable", "complete"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def report_template(args: argparse.Namespace) -> dict:
    return {
        "scope": {
            "domain": args.domain,
            "market": args.market,
            "locale": args.locale,
            "currency": args.currency,
            "stage": args.stage,
            "auth_state": args.auth_state,
            "target_api": args.target_api,
        },
        "fresh_evidence": {
            "run_id": "",
            "capture_id": "",
            "captured_at": now_iso(),
            "browser_profile_id": "",
            "state_reset": "",
            "network_log_id": "",
            "script_hash": "",
            "auth_state": args.auth_state,
            "source_freshness": "unknown",
        },
        "clean_state_retest": {
            "clean_unverified": {"status": "unverified", "request": "", "response": "", "state_delta": ""},
            "verified": {"status": "unverified", "request": "", "response": "", "state_delta": ""},
            "repeat_verified": {"status": "unverified", "request": "", "response": "", "state_delta": ""},
        },
        "anti_flake": {
            "same_scope_observations": [],
            "decision": "unverified",
        },
        "concurrency_ladder": {
            "worker_1": worker_template(),
            "worker_2": worker_template(),
            "worker_5": worker_template(),
            "worker_10": worker_template(),
        },
        "session_cache_isolation": {
            "browser_context": "isolated_by_default",
            "cookie_jar": "isolated_by_default",
            "local_storage": "isolated_by_default",
            "session_storage": "isolated_by_default",
            "token_cache": "isolated_by_default",
            "account_state": "isolated_by_default",
            "sharing_exception_evidence": "",
        },
        "risk_control": {
            "authorization_scope": "",
            "protected_business_api_acceptance": "",
            "failure_split": [],
            "backoff": "",
            "jitter": "",
            "session_retirement": "",
            "kill_switch": "",
            "human_review_boundary": "",
            "blocked_as_negative_eval": "",
            "not_allowed": "no bypass instructions, no fingerprint spoofing, no clearance cookie reuse",
        },
        "data_acceptance": {
            "ui_api_parity": "",
            "json_pointers": [],
            "consistency_rate": None,
            "adapter_target": "",
            "screenshot_or_dom_evidence": "",
        },
        "fixtures_freshness": {
            "strict_review_exit_code": None,
            "expired_count": None,
            "review_pending_count": None,
            "recent_report": False,
            "source_freshness": "unknown",
        },
        "metrics": {
            "task_count": 0,
            "success_browserless_verified": 0,
            "concurrency_verified": 0,
            "strict_review_pass_count": 0,
            "flaky_count": 0,
            "blocked_by_protection": 0,
            "latest_replay_rate": None,
        },
        "decision": {
            "status": "unverified",
            "can_claim_concurrency": False,
            "can_claim_stable": False,
            "remaining_gap": "",
        },
    }


def worker_template() -> dict:
    return {
        "status": "unverified",
        "total_requests": 0,
        "success_count": 0,
        "failure_count": 0,
        "status_403_429_503_rate": None,
        "p95_ms": None,
        "token_refresh_count": 0,
        "cookie_refresh_count": 0,
        "session_isolated": False,
        "backend_acceptance": False,
        "stop_condition": "",
    }


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def has_key(payload: dict, path: list[str]) -> bool:
    cur = payload
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return False
        cur = cur[key]
    return True


def non_empty(payload: dict, path: list[str]) -> bool:
    cur = payload
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return False
        cur = cur[key]
    return cur not in (None, "", [], {})


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


def validate_report(payload: dict, require_complete: bool = False) -> dict:
    failures: list[str] = []
    blockers: list[str] = []
    warnings: list[str] = []

    for key in REQUIRED_TOP:
        if key not in payload:
            failures.append(f"missing top-level key: {key}")

    for key in REQUIRED_FRESH:
        if not has_key(payload, ["fresh_evidence", key]):
            failures.append(f"missing fresh_evidence.{key}")
        elif require_complete and not non_empty(payload, ["fresh_evidence", key]):
            blockers.append(f"require_complete: fresh_evidence.{key} is empty")

    for group in RETEST_GROUPS:
        if not has_key(payload, ["clean_state_retest", group]):
            failures.append(f"missing clean_state_retest.{group}")
        elif require_complete and payload["clean_state_retest"][group].get("status") != "pass":
            blockers.append(f"require_complete: clean_state_retest.{group}.status must be pass")

    for worker in WORKERS:
        if not has_key(payload, ["concurrency_ladder", worker]):
            failures.append(f"missing concurrency_ladder.{worker}")
            continue
        if payload.get("decision", {}).get("can_claim_concurrency"):
            item = payload["concurrency_ladder"][worker]
            if item.get("status") != "pass":
                failures.append(f"{worker} is not pass but concurrency is claimed")
            if item.get("session_isolated") is not True:
                failures.append(f"{worker} lacks session isolation evidence")
            if item.get("backend_acceptance") is not True:
                failures.append(f"{worker} lacks backend acceptance evidence")

    for key in RISK_KEYS:
        if not has_key(payload, ["risk_control", key]):
            failures.append(f"missing risk_control.{key}")

    for key in DATA_KEYS:
        if not has_key(payload, ["data_acceptance", key]):
            failures.append(f"missing data_acceptance.{key}")

    for key in FRESHNESS_KEYS:
        if not has_key(payload, ["fixtures_freshness", key]):
            failures.append(f"missing fixtures_freshness.{key}")

    for key in METRIC_KEYS:
        if not has_key(payload, ["metrics", key]):
            failures.append(f"missing metrics.{key}")

    if payload.get("decision", {}).get("can_claim_stable"):
        if payload.get("anti_flake", {}).get("decision") != "stable":
            failures.append("stable is claimed but anti_flake.decision is not stable")
        if payload.get("fixtures_freshness", {}).get("source_freshness") != "fresh":
            failures.append("stable is claimed but fixtures are not fresh")

    if require_complete:
        fresh = payload.get("fresh_evidence", {})
        if fresh.get("source_freshness") != "fresh":
            blockers.append("require_complete: fresh_evidence.source_freshness must be fresh")

        if payload.get("anti_flake", {}).get("decision") != "stable":
            blockers.append("require_complete: anti_flake.decision must be stable")

        risk = payload.get("risk_control", {})
        if blankish(risk.get("authorization_scope")):
            blockers.append("require_complete: risk_control.authorization_scope is missing")
        if blankish(risk.get("protected_business_api_acceptance")):
            blockers.append("require_complete: risk_control.protected_business_api_acceptance is missing")

        data = payload.get("data_acceptance", {})
        if blankish(data.get("ui_api_parity")):
            blockers.append("require_complete: data_acceptance.ui_api_parity is missing")
        if blankish(data.get("json_pointers")):
            blockers.append("require_complete: data_acceptance.json_pointers is missing")

        freshness = payload.get("fixtures_freshness", {})
        if freshness.get("source_freshness") != "fresh":
            blockers.append("require_complete: fixtures_freshness.source_freshness must be fresh")
        if freshness.get("strict_review_exit_code") != 0:
            blockers.append("require_complete: fixtures_freshness.strict_review_exit_code must be 0")
        if freshness.get("expired_count") != 0:
            blockers.append("require_complete: fixtures_freshness.expired_count must be 0")
        if freshness.get("review_pending_count") != 0:
            blockers.append("require_complete: fixtures_freshness.review_pending_count must be 0")
        if freshness.get("recent_report") is not True:
            blockers.append("require_complete: fixtures_freshness.recent_report must be true")

        decision = payload.get("decision", {})
        if decision.get("status") not in SUCCESS_DECISIONS:
            blockers.append("require_complete: decision.status must be success/pass/stable/complete")
        if decision.get("can_claim_stable") is not True:
            blockers.append("require_complete: decision.can_claim_stable must be true")

    freshness = payload.get("fixtures_freshness", {})
    if freshness.get("expired_count") not in (None, 0):
        warnings.append(f"expired fixtures present: {freshness.get('expired_count')}")
    if freshness.get("review_pending_count") not in (None, 0):
        warnings.append(f"review_pending fixtures present: {freshness.get('review_pending_count')}")
    if freshness.get("strict_review_exit_code") not in (None, 0):
        warnings.append("strict fixture review has not passed")

    status = success_status(failures, blockers, require_complete)
    return {
        "tool": "web_h5_acceptance_report",
        "status": status,
        "failures": failures,
        "blockers": blockers,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create and validate Web/H5 crawler acceptance reports")
    sub = parser.add_subparsers(dest="command", required=True)

    tmpl = sub.add_parser("template", help="write an acceptance report template")
    tmpl.add_argument("--out", required=True)
    tmpl.add_argument("--domain", required=True)
    tmpl.add_argument("--market", default="")
    tmpl.add_argument("--locale", default="")
    tmpl.add_argument("--currency", default="")
    tmpl.add_argument("--stage", required=True)
    tmpl.add_argument("--auth-state", default="anonymous")
    tmpl.add_argument("--target-api", required=True)

    val = sub.add_parser("validate", help="validate an acceptance report")
    val.add_argument("--report", required=True)
    val.add_argument("--require-complete", action="store_true")

    args = parser.parse_args()
    if args.command == "template":
        path = Path(args.out)
        payload = report_template(args)
        write_json(path, payload)
        print(json.dumps({"tool": "web_h5_acceptance_report", "status": "CREATED", "report": str(path)}, ensure_ascii=False, indent=2))
        return 0

    result = validate_report(read_json(Path(args.report)), require_complete=args.require_complete)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"STRUCTURE_PASS", "SUCCESS_PASS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
