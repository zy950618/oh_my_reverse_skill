#!/usr/bin/env python3
"""Validate real execution proof embedded in public-range evidence."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
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


EXECUTION_STATUSES = {"REAL_EXECUTION_PASS", "STRUCTURE_ONLY", "BLOCKED", "INVALID"}
POSITIVE_STATUSES = {"positive_allowed", "positive_candidate", "positive_verified", "stable_positive"}
CAPABILITY_STATUSES = POSITIVE_STATUSES | {"negative_eval_only", "memory_only", "prohibited", "unverified"}
CONTROL_FLOW_STATUSES = {"CONTROL_FLOW_PASS", "CONTROL_FLOW_FAIL", "NOT_RUN"}
BUSINESS_DATA_STATUSES = {"DATA_ASSERTION_PASS", "DATA_ASSERTION_FAIL", "NOT_RUN"}
PROTECTION_WORDS = ("captcha", "turnstile", "waf", "risk", "bot", "fingerprint", "gocaptcha")
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


def non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def resolve_existing_path(raw: object) -> Path | None:
    if not non_empty_string(raw):
        return None
    path = Path(str(raw))
    if path.is_file():
        return path

    normalized = str(raw).replace("\\", "/")
    marker = "public-range-evidence/"
    marker_index = normalized.find(marker)
    if marker_index == -1:
        return None

    relative = Path(*normalized[marker_index:].split("/"))
    current = REPO_ROOT / relative
    if current.is_file():
        return current

    archive_root = REPO_ROOT / "public-range-evidence" / "_archive"
    if not archive_root.is_dir():
        return None
    relative_suffix = "/".join(relative.parts)
    for candidate in archive_root.rglob(path.name):
        candidate_normalized = str(candidate).replace("\\", "/")
        if candidate_normalized.endswith(relative_suffix):
            return candidate
    return None


def path_exists(raw: object) -> bool:
    return resolve_existing_path(raw) is not None


def list_paths_exist(value: object) -> tuple[bool, list[str]]:
    if not isinstance(value, list):
        return False, []
    missing = [str(item) for item in value if non_empty_string(item) and resolve_existing_path(item) is None]
    present = [str(resolve_existing_path(item)) for item in value if resolve_existing_path(item) is not None]
    return not missing, present


def is_positive(payload: dict[str, Any]) -> bool:
    return capability_status(payload) in POSITIVE_STATUSES


def capability_status(payload: dict[str, Any]) -> str:
    top_level = payload.get("capability_status")
    if isinstance(top_level, str) and top_level in CAPABILITY_STATUSES:
        return top_level
    decision = payload.get("decision")
    if isinstance(decision, dict):
        participation = decision.get("skills_participation")
        if isinstance(participation, str) and participation in CAPABILITY_STATUSES:
            return participation
    return "unverified"


def has_final_business_acceptance(payload: dict[str, Any]) -> bool:
    backend = payload.get("backend_acceptance")
    if not isinstance(backend, dict):
        return False
    if backend.get("final_api_endpoint_confirmed") is not True:
        return False
    direct = backend.get("direct_interface_call")
    repeat = backend.get("repeat_direct_interface_call")
    return (
        isinstance(direct, dict)
        and isinstance(repeat, dict)
        and direct.get("status") == "pass"
        and repeat.get("status") == "pass"
        and direct.get("browser_dependency") is False
        and repeat.get("browser_dependency") is False
    )


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


def is_protection_related(path: Path, payload: dict[str, Any]) -> bool:
    text = " ".join([
        str(path).lower(),
        str(payload.get("target", {}).get("id", "")).lower() if isinstance(payload.get("target"), dict) else "",
        str(payload.get("target", {}).get("type", "")).lower() if isinstance(payload.get("target"), dict) else "",
        " ".join(str(item).lower() for item in payload.get("skills", []) if isinstance(item, str)),
    ])
    provider = payload.get("provider_flow")
    if isinstance(provider, dict):
        text += " " + str(provider.get("provider", "")).lower()
    return any(word in text for word in PROTECTION_WORDS)


def validate_proof(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    proof = payload.get("execution_proof")
    if not isinstance(proof, dict):
        return {
            "path": str(path),
            "status": "STRUCTURE_ONLY",
            "execution_status": "STRUCTURE_ONLY",
            "capability_status": capability_status(payload),
            "reason": "missing execution_proof",
            "real_execution": False,
            "failures": [],
            "warnings": ["evidence can be structurally valid but cannot count as real execution proof"],
        }

    failures: list[str] = []
    warnings: list[str] = []
    declared_execution_status = payload.get("execution_status")
    declared_capability_status = payload.get("capability_status")
    current_capability_status = capability_status(payload)
    if declared_execution_status is not None and declared_execution_status not in EXECUTION_STATUSES:
        failures.append("execution_status must be one of REAL_EXECUTION_PASS, STRUCTURE_ONLY, BLOCKED, INVALID")
    if declared_capability_status is not None and declared_capability_status not in CAPABILITY_STATUSES:
        failures.append(f"capability_status must be one of {sorted(CAPABILITY_STATUSES)}")
    control_flow_status = payload.get("control_flow_status", "NOT_RUN")
    business_data_status = payload.get("business_data_status", "NOT_RUN")
    if control_flow_status not in CONTROL_FLOW_STATUSES:
        failures.append("control_flow_status must be one of CONTROL_FLOW_PASS, CONTROL_FLOW_FAIL, NOT_RUN")
    if business_data_status not in BUSINESS_DATA_STATUSES:
        failures.append("business_data_status must be one of DATA_ASSERTION_PASS, DATA_ASSERTION_FAIL, NOT_RUN")
    for key in ("command", "cwd", "started_at", "ended_at", "stdout_log", "stderr_log", "generated_by"):
        if not non_empty_string(proof.get(key)):
            failures.append(f"execution_proof.{key} is required")
    if not isinstance(proof.get("exit_code"), int):
        failures.append("execution_proof.exit_code must be integer")
    if proof.get("synthetic") is not False:
        failures.append("execution_proof.synthetic must be false")

    if non_empty_string(proof.get("stdout_log")) and not path_exists(proof.get("stdout_log")):
        failures.append("execution_proof.stdout_log does not exist")
    if non_empty_string(proof.get("stderr_log")) and not path_exists(proof.get("stderr_log")):
        failures.append("execution_proof.stderr_log does not exist")

    screenshots_ok, screenshots = list_paths_exist(proof.get("screenshot_paths"))
    network_ok, network = list_paths_exist(proof.get("network_summary_paths"))
    if not screenshots_ok:
        failures.append("one or more execution_proof.screenshot_paths do not exist")
    if not network_ok:
        failures.append("one or more execution_proof.network_summary_paths do not exist")
    if not network:
        failures.append("at least one network_summary_path is required")
    if not screenshots:
        warnings.append("no screenshot path; acceptable only for non-browser direct evidence")

    trace_path = proof.get("browser_trace_path")
    if non_empty_string(trace_path) and not path_exists(trace_path):
        failures.append("execution_proof.browser_trace_path does not exist")

    positive = current_capability_status in POSITIVE_STATUSES
    if positive and not screenshots:
        failures.append("positive_allowed evidence requires screenshot proof")
    if positive and not network:
        failures.append("positive_allowed evidence requires network summary proof")
    if positive and proof.get("synthetic") is True:
        failures.append("synthetic=true cannot be positive_allowed")
    scope = positive_scope(payload)
    business_positive_required = scope not in NON_BUSINESS_POSITIVE_SCOPES
    if positive and business_positive_required and is_protection_related(path, payload) and not has_final_business_acceptance(payload):
        failures.append("CAPTCHA/WAF/risk evidence cannot be positive_allowed without final business API acceptance")
    if positive and business_positive_required and business_data_status != "DATA_ASSERTION_PASS":
        failures.append("positive_allowed evidence requires business_data_status=DATA_ASSERTION_PASS")

    if failures:
        execution_status = "INVALID"
    elif proof.get("exit_code") != 0:
        execution_status = "BLOCKED"
    else:
        execution_status = "REAL_EXECUTION_PASS"

    return {
        "path": str(path),
        "status": execution_status,
        "execution_status": execution_status,
        "capability_status": current_capability_status,
        "control_flow_status": control_flow_status,
        "business_data_status": business_data_status,
        "real_execution": execution_status == "REAL_EXECUTION_PASS",
        "target_id": payload.get("target", {}).get("id") if isinstance(payload.get("target"), dict) else None,
        "run_id": payload.get("run_id"),
        "skills_participation": payload.get("decision", {}).get("skills_participation") if isinstance(payload.get("decision"), dict) else None,
        "screenshot_count": len(screenshots),
        "network_summary_count": len(network),
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


def validate_file(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {
            "path": str(path),
            "status": "INVALID",
            "real_execution": False,
            "failures": [f"cannot parse JSON: {exc!r}"],
            "warnings": [],
        }
    if not isinstance(payload, dict):
        return {
            "path": str(path),
            "status": "INVALID",
            "real_execution": False,
            "failures": ["JSON payload must be object"],
            "warnings": [],
        }
    return validate_proof(path, payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate public-range real execution proof")
    parser.add_argument("evidence_root_arg", nargs="?", help="public range evidence root")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--evidence-root", default="public-range-evidence")
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    root = repo_root / (args.evidence_root_arg or args.evidence_root)
    results = [validate_file(path) for path in evidence_files(root)]
    execution_counts = {status: sum(1 for item in results if item.get("execution_status", item["status"]) == status) for status in EXECUTION_STATUSES}
    capability_counts = {status: sum(1 for item in results if item.get("capability_status") == status) for status in CAPABILITY_STATUSES}
    control_flow_counts = {status: sum(1 for item in results if item.get("control_flow_status", "NOT_RUN") == status) for status in CONTROL_FLOW_STATUSES}
    business_data_counts = {status: sum(1 for item in results if item.get("business_data_status", "NOT_RUN") == status) for status in BUSINESS_DATA_STATUSES}
    invalid = [item for item in results if item["status"] == "INVALID"]
    payload = {
        "tool": "validate_real_execution_proof",
        "status": "PASS" if not invalid else "FAIL",
        "evidence_root": str(root),
        "total_files": len(results),
        "real_execution_pass_count": execution_counts["REAL_EXECUTION_PASS"],
        "structure_only_count": execution_counts["STRUCTURE_ONLY"],
        "blocked_count": execution_counts["BLOCKED"],
        "invalid_count": execution_counts["INVALID"],
        "positive_allowed_count": capability_counts["positive_allowed"],
        "positive_candidate_count": capability_counts["positive_candidate"],
        "positive_verified_count": capability_counts["positive_verified"],
        "stable_positive_count": capability_counts["stable_positive"],
        "negative_eval_only_count": capability_counts["negative_eval_only"],
        "memory_only_count": capability_counts["memory_only"],
        "prohibited_count": capability_counts["prohibited"],
        "unverified_count": capability_counts["unverified"],
        "execution_counts": execution_counts,
        "capability_counts": capability_counts,
        "control_flow_counts": control_flow_counts,
        "business_data_counts": business_data_counts,
        "real_execution_targets": [
            {"target_id": item.get("target_id"), "run_id": item.get("run_id"), "path": item.get("path")}
            for item in results
            if item.get("real_execution")
        ],
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
