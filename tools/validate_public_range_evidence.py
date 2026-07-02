#!/usr/bin/env python3
"""Validate sanitized public range evidence.

This gate is intentionally stricter for positive skill growth than for
negative/boundary evidence. A public target can teach a failure mode without
being allowed to improve positive skill scores.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


POSITIVE_STATUSES = {"positive_allowed", "positive_candidate", "positive_verified", "stable_positive"}
PARTICIPATION = POSITIVE_STATUSES | {"negative_eval_only", "memory_only", "prohibited", "unverified"}
CAPABILITY_STATUS = PARTICIPATION | {"unverified"}
CONTROL_FLOW_STATUSES = {"CONTROL_FLOW_PASS", "CONTROL_FLOW_FAIL", "NOT_RUN"}
BUSINESS_DATA_STATUSES = {"DATA_ASSERTION_PASS", "DATA_ASSERTION_FAIL", "NOT_RUN"}
NON_BUSINESS_POSITIVE_SCOPES = {
    "local_open_source_range_positive",
    "local_compatible_lab_candidate",
    "local_compatible_lab_verified",
    "local_compatible_lab_stable",
    "local_vendor_compatible_positive_candidate",
    "public_range_solver_positive",
    "local_runtime_parity_positive",
    "local_fingerprint_diagnostics_positive",
    "public_fingerprint_diagnostics_positive",
}
INTERNAL_ARTIFACT_PARTS = {
    "_archive",
    "fixtures",
    "replay",
    "reports",
    "manifests",
    "samples",
    "model",
    "inference",
    "eval",
    "mock_server",
    "fastapi_adapter",
    "sdk_examples",
    "tests",
}
DEDICATED_LAB_ROOTS = {
    "airline-lab-order-flow",
    "captcha-model-lab",
    "fingerprint-risk-lab",
    "pure-api-lab",
    "real-site-observation-pack",
}


def parse_dt(raw: object) -> datetime | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    value = raw.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def is_pass(section: object) -> bool:
    return isinstance(section, dict) and str(section.get("status", "")).lower() == "pass"


def is_2xx(value: object) -> bool:
    return isinstance(value, int) and 200 <= value < 300


def non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def non_empty_pointers(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, str) and item.startswith("/") for item in value
    )


def interface_call_errors(call: object, label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(call, dict):
        return [f"{label} is required"]
    if not is_pass(call):
        errors.append(f"{label}.status must be pass")
    if call.get("browser_dependency") is not False:
        errors.append(f"{label}.browser_dependency must be false")
    for key in ("uses_browser_profile", "uses_live_storage", "uses_manual_cookie_or_token"):
        if call.get(key) is not False:
            errors.append(f"{label}.{key} must be false")
    if not is_2xx(call.get("observed_status")):
        errors.append(f"{label}.observed_status must be 2xx")
    content_type = str(call.get("content_type", "")).lower()
    json_type = str(call.get("json_type", "")).lower()
    if "json" not in content_type and json_type not in {"dict", "list"}:
        errors.append(f"{label} must return JSON business data")
    if not non_empty_pointers(call.get("json_pointers")):
        errors.append(f"{label}.json_pointers must be non-empty JSON Pointers")
    return errors


def sign_or_token_errors(payload: dict[str, Any]) -> list[str]:
    sign = payload.get("sign_or_token")
    if not isinstance(sign, dict) or sign.get("required") is not True:
        return []
    errors: list[str] = []
    mode = sign.get("generation_mode")
    if mode not in {"v8_env", "js_runtime", "node_vm", "wasm_crypto", "native_crypto", "adapter"}:
        errors.append("sign_or_token.generation_mode must be non-browser reproducible")
    if sign.get("browser_captured_replay") is not False:
        errors.append("sign_or_token.browser_captured_replay must be false")
    if not is_pass(sign.get("validation")):
        errors.append("sign_or_token.validation.status must be pass")
    return errors


def concurrency_errors(payload: dict[str, Any]) -> list[str]:
    decision = payload.get("decision")
    if not isinstance(decision, dict) or decision.get("concurrency_positive") is not True:
        return []
    ladder = payload.get("concurrency_ladder")
    if not isinstance(ladder, dict):
        return ["concurrency_ladder is required when concurrency_positive=true"]
    errors: list[str] = []
    for worker in ("worker_1", "worker_2", "worker_5", "worker_10"):
        item = ladder.get(worker)
        if not isinstance(item, dict) or item.get("status") != "pass":
            errors.append(f"concurrency_ladder.{worker}.status must be pass")
            continue
        if item.get("session_cache_token_isolated") is not True:
            errors.append(f"concurrency_ladder.{worker}.session_cache_token_isolated must be true")
        if item.get("backend_acceptance") is not True:
            errors.append(f"concurrency_ladder.{worker}.backend_acceptance must be true")
        if "failure_rate" not in item:
            errors.append(f"concurrency_ladder.{worker}.failure_rate is required")
        if not non_empty_string(item.get("stop_condition")):
            errors.append(f"concurrency_ladder.{worker}.stop_condition is required")
    return errors


def business_data_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("business_data_status") != "DATA_ASSERTION_PASS":
        errors.append("business_data_status must be DATA_ASSERTION_PASS for positive_allowed")
    bda = payload.get("business_data_assertions")
    if not isinstance(bda, dict):
        return errors + ["business_data_assertions is required for positive_allowed"]
    if bda.get("status") != "pass":
        errors.append("business_data_assertions.status must be pass")
    if not non_empty_string(bda.get("server_ledger_path")):
        errors.append("business_data_assertions.server_ledger_path is required")
    positives = bda.get("positive_assertions")
    if not isinstance(positives, list) or not positives:
        errors.append("business_data_assertions.positive_assertions must be non-empty")
    else:
        for index, item in enumerate(positives):
            if not isinstance(item, dict) or item.get("status") != "pass":
                errors.append(f"business_data_assertions.positive_assertions[{index}].status must be pass")
    negatives = bda.get("negative_assertions")
    if not isinstance(negatives, list) or not negatives:
        errors.append("business_data_assertions.negative_assertions must be non-empty")
    else:
        for index, item in enumerate(negatives):
            if not isinstance(item, dict) or item.get("status") != "pass":
                errors.append(f"business_data_assertions.negative_assertions[{index}].status must be pass")
                continue
            if item.get("expected_ledger_delta") != 0 or item.get("actual_ledger_delta") != 0:
                errors.append(f"business_data_assertions.negative_assertions[{index}] must prove ledger_delta=0")
    concurrency = bda.get("concurrency_assertions")
    if isinstance(payload.get("decision"), dict) and payload["decision"].get("concurrency_positive") is True:
        if not isinstance(concurrency, dict):
            errors.append("business_data_assertions.concurrency_assertions is required when concurrency_positive=true")
        else:
            for worker in ("worker_1", "worker_2", "worker_5", "worker_10"):
                item = concurrency.get(worker)
                if not isinstance(item, dict) or item.get("status") != "pass":
                    errors.append(f"business_data_assertions.concurrency_assertions.{worker}.status must be pass")
                    continue
                if item.get("expected_success_count") != item.get("actual_success_count"):
                    errors.append(f"business_data_assertions.concurrency_assertions.{worker} success count mismatch")
                if item.get("expected_ledger_delta") != item.get("actual_ledger_delta"):
                    errors.append(f"business_data_assertions.concurrency_assertions.{worker} ledger delta mismatch")
                for key in ("duplicate_order_count", "cross_worker_pollution_count", "wrong_owner_count", "orphan_order_count"):
                    if item.get(key) != 0:
                        errors.append(f"business_data_assertions.concurrency_assertions.{worker}.{key} must be 0")
    final = bda.get("final_decision")
    if not isinstance(final, dict) or final.get("data_assertion_pass") is not True:
        errors.append("business_data_assertions.final_decision.data_assertion_pass must be true")
    return errors


def positive_scope(payload: dict[str, Any]) -> str:
    scope = payload.get("scope_decision")
    if isinstance(scope, dict):
        value = scope.get("positive_allowed_scope")
        if isinstance(value, str):
            return value
    detail = payload.get("capability_status_detail")
    if isinstance(detail, dict):
        value = detail.get("scope_limited_positive")
        if isinstance(value, str):
            return value
    return ""


def scope_limited_positive_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    scope = payload.get("scope_decision")
    detail = payload.get("capability_status_detail")
    if not isinstance(scope, dict):
        errors.append("positive evidence requires scope_decision")
        return errors
    if scope.get("in_scope") is not True:
        errors.append("scope_decision.in_scope must be true")
    if scope.get("external_generalization_allowed") is not False:
        errors.append("scope_decision.external_generalization_allowed must be false")
    if not non_empty_string(scope.get("positive_allowed_scope")):
        errors.append("scope_decision.positive_allowed_scope is required")
    if not isinstance(detail, dict):
        errors.append("positive evidence requires capability_status_detail")
        return errors
    if detail.get("not_generalizable_to_third_party") is not True:
        errors.append("capability_status_detail.not_generalizable_to_third_party must be true")
    if detail.get("status") not in POSITIVE_STATUSES:
        errors.append(f"capability_status_detail.status must be one of {sorted(POSITIVE_STATUSES)}")
    return errors


def non_business_positive_errors(payload: dict[str, Any]) -> list[str]:
    errors = scope_limited_positive_errors(payload)
    scope = positive_scope(payload)
    if scope in {"local_fingerprint_diagnostics_positive", "public_fingerprint_diagnostics_positive"}:
        if not payload.get("fingerprint_surface_report"):
            errors.append("fingerprint diagnostics positive requires fingerprint_surface_report")
        consistency = payload.get("profile_consistency")
        if not isinstance(consistency, dict) or int(consistency.get("repeat_count") or 0) < 3 or int(consistency.get("profile_count") or 0) < 2:
            errors.append("fingerprint diagnostics positive requires repeat>=3 and profiles>=2")
        return errors
    action = payload.get("action_replay")
    leakage = payload.get("leakage_audit")
    blackbox = payload.get("blackbox_gate")
    ui = payload.get("ui_api_parity")
    if not is_pass(action):
        errors.append("scope-limited solver positive requires action_replay.status=pass")
    if not is_pass(leakage):
        errors.append("scope-limited solver positive requires leakage_audit.status=pass")
    if scope in {"local_compatible_lab_candidate", "local_compatible_lab_verified", "local_compatible_lab_stable", "local_open_source_range_positive", "public_range_solver_positive"} and not is_pass(blackbox):
        errors.append("scope-limited solver positive requires blackbox_gate.status=pass")
    if ui is not None and not is_pass(ui):
        errors.append("ui_api_parity.status must be pass when UI parity is claimed")
    return errors


def hard_gate_errors(payload: dict[str, Any], max_age_days: int) -> list[str]:
    errors: list[str] = []
    captured_at = parse_dt(payload.get("captured_at"))
    now = datetime.now(timezone.utc)
    backend = payload.get("backend_acceptance")
    ui = payload.get("ui_api_parity")

    if payload.get("source_freshness") != "fresh":
        errors.append("source_freshness must be fresh")
    if payload.get("control_flow_status") != "CONTROL_FLOW_PASS":
        errors.append("control_flow_status must be CONTROL_FLOW_PASS for positive_allowed")
    if captured_at is None:
        errors.append("captured_at must be a valid ISO datetime")
    elif captured_at < now - timedelta(days=max_age_days):
        errors.append(f"captured_at is older than {max_age_days} days")
    scope = positive_scope(payload)
    if scope in NON_BUSINESS_POSITIVE_SCOPES:
        errors.extend(non_business_positive_errors(payload))
    elif not is_pass(backend):
        errors.append("backend_acceptance.status must be pass")
    if scope not in NON_BUSINESS_POSITIVE_SCOPES and isinstance(backend, dict):
        if backend.get("final_api_endpoint_confirmed") is not True:
            errors.append("backend_acceptance.final_api_endpoint_confirmed must be true")
        if not is_2xx(backend.get("observed_status")):
            errors.append("backend_acceptance.observed_status must be 2xx")
        if not non_empty_string(backend.get("endpoint")):
            errors.append("backend_acceptance.endpoint is required")
        if not non_empty_pointers(backend.get("json_pointers")):
            errors.append("backend_acceptance.json_pointers must be non-empty JSON Pointers")
        errors.extend(interface_call_errors(backend.get("direct_interface_call"), "backend_acceptance.direct_interface_call"))
        errors.extend(interface_call_errors(backend.get("repeat_direct_interface_call"), "backend_acceptance.repeat_direct_interface_call"))
    if ui is not None and not is_pass(ui):
        errors.append("ui_api_parity.status must be pass when UI parity is claimed")
    errors.extend(sign_or_token_errors(payload))
    errors.extend(concurrency_errors(payload))
    if scope not in NON_BUSINESS_POSITIVE_SCOPES:
        errors.extend(scope_limited_positive_errors(payload))
        errors.extend(business_data_errors(payload))
    return errors


def validate_file(path: Path, max_age_days: int) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {
            "path": str(path),
            "status": "FAIL",
            "skills_participation": None,
            "positive": False,
            "failures": [f"cannot parse JSON: {exc!r}"],
            "warnings": [],
        }

    decision = payload.get("decision")
    if not isinstance(decision, dict):
        failures.append("decision object is required")
        decision = {}

    participation = decision.get("skills_participation")
    if participation not in PARTICIPATION:
        failures.append(f"decision.skills_participation must be one of {sorted(PARTICIPATION)}")
    capability_status = payload.get("capability_status", participation)
    if capability_status not in CAPABILITY_STATUS:
        failures.append(f"capability_status must be one of {sorted(CAPABILITY_STATUS)}")
    if participation in PARTICIPATION and capability_status != participation:
        failures.append("capability_status must match decision.skills_participation")

    if payload.get("schema_version") != "public-range-evidence/v1":
        failures.append("schema_version must be public-range-evidence/v1")
    control_flow_status = payload.get("control_flow_status", "NOT_RUN")
    if control_flow_status not in CONTROL_FLOW_STATUSES:
        failures.append(f"control_flow_status must be one of {sorted(CONTROL_FLOW_STATUSES)}")
    business_data_status = payload.get("business_data_status", "NOT_RUN")
    if business_data_status not in BUSINESS_DATA_STATUSES:
        failures.append(f"business_data_status must be one of {sorted(BUSINESS_DATA_STATUSES)}")
    if not isinstance(payload.get("target"), dict) or not non_empty_string(payload["target"].get("url")):
        failures.append("target.url is required")
    if not isinstance(payload.get("skills"), list) or not payload["skills"]:
        failures.append("skills must name at least one participating skill")

    positive = capability_status in POSITIVE_STATUSES
    if positive:
        if decision.get("positive_allowed") is not True and capability_status in {"positive_allowed", "positive_verified", "stable_positive"}:
            failures.append("verified/stable positive participation requires decision.positive_allowed=true")
        failures.extend(hard_gate_errors(payload, max_age_days=max_age_days))
    elif participation in {"negative_eval_only", "memory_only", "prohibited"}:
        if decision.get("positive_allowed") is True:
            failures.append(f"{participation} evidence cannot set positive_allowed=true")
        blocked_reason = decision.get("blocked_reason")
        if participation == "negative_eval_only" and not non_empty_string(blocked_reason):
            failures.append("negative_eval_only evidence requires decision.blocked_reason")
        if not payload.get("backend_acceptance") and not payload.get("ui_api_parity"):
            failures.append("boundary evidence still needs backend_acceptance or ui_api_parity observation")
        if payload.get("repeat_verified") is not True:
            warnings.append("repeat verification is not complete; correctly blocked from positive scoring")

    status = "PASS" if not failures else "FAIL"
    return {
        "path": str(path),
        "status": status,
        "skills_participation": participation,
        "capability_status": capability_status,
        "positive": positive and status == "PASS",
        "failures": failures,
        "warnings": warnings,
    }


def evidence_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(
        path for path in root.rglob("*.json")
        if not {"raw", "longrun"} & {part.lower() for part in path.parts}
        and path.relative_to(root).parts[0].lower() not in DEDICATED_LAB_ROOTS
        and not INTERNAL_ARTIFACT_PARTS & {part.lower() for part in path.relative_to(root).parts[:-1]}
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate public range evidence hard gates")
    parser.add_argument("evidence_root_arg", nargs="?", help="public range evidence root, for compatibility with documented usage")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--evidence-root", default="public-range-evidence")
    parser.add_argument("--max-age-days", type=int, default=30)
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    root = repo_root / (args.evidence_root_arg or args.evidence_root)
    files = evidence_files(root)
    results = [validate_file(path, args.max_age_days) for path in files]
    failures = [item for item in results if item["status"] != "PASS"]
    positive_count = sum(1 for item in results if item.get("positive"))

    global_failures: list[str] = []
    if not files:
        global_failures.append(f"no public range evidence files under {root}")
    if positive_count == 0:
        global_failures.append("no candidate/verified/stable public range evidence passed hard gates")

    payload = {
        "tool": "validate_public_range_evidence",
        "status": "PASS" if not failures and not global_failures else "FAIL",
        "evidence_root": str(root),
        "total_files": len(files),
        "total_positive_count": positive_count,
        "positive_allowed_count": sum(1 for item in results if item.get("capability_status") == "positive_allowed" and item.get("status") == "PASS"),
        "positive_candidate_count": sum(1 for item in results if item.get("capability_status") == "positive_candidate" and item.get("status") == "PASS"),
        "positive_verified_count": sum(1 for item in results if item.get("capability_status") == "positive_verified" and item.get("status") == "PASS"),
        "stable_positive_count": sum(1 for item in results if item.get("capability_status") == "stable_positive" and item.get("status") == "PASS"),
        "negative_eval_count": sum(1 for item in results if item.get("skills_participation") == "negative_eval_only"),
        "global_failures": global_failures,
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
