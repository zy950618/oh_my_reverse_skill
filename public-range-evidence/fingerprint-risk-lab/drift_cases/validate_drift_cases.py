#!/usr/bin/env python3
"""Validate local fingerprint drift and negative-case classification evidence."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_CASES = {
    "missing_webdriver_field",
    "inconsistent_user_agent_platform",
    "timezone_language_mismatch",
    "dirty_storage_leak",
    "reused_context_leak",
    "missing_canvas_surface",
    "missing_webgl_surface",
    "unknown_block_reason",
    "captcha_linkage_missing",
    "browser_vs_pure_api_diff_missing",
}

REQUIRED_FIELDS = {
    "id",
    "category",
    "input_surface",
    "observed_signal",
    "expected_classification",
    "expected_result",
    "safe_next_action",
}


def load_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # pragma: no cover - command-line evidence path
        return {}, [f"cannot parse JSON {path}: {exc!r}"]
    if not isinstance(payload, dict):
        return {}, [f"{path} must contain a JSON object"]
    return payload, []


def validate(path: Path) -> dict[str, Any]:
    failures: list[str] = []
    payload, errors = load_json(path)
    failures.extend(errors)
    if not payload:
        return result(path, failures, [], [])

    if payload.get("schema_version") != "fingerprint-drift-cases/v1":
        failures.append("schema_version must be fingerprint-drift-cases/v1")
    if payload.get("status") != "negative_and_drift_classification":
        failures.append("status must be negative_and_drift_classification")
    if payload.get("evidence_scope") != "local_lab":
        failures.append("evidence_scope must be local_lab")
    if payload.get("live_site_calls_performed") is not False:
        failures.append("live_site_calls_performed must be false")

    boundary = payload.get("capability_boundary")
    if not isinstance(boundary, dict):
        failures.append("capability_boundary object is required")
    else:
        if boundary.get("positive_allowed") is not False:
            failures.append("capability_boundary.positive_allowed must be false")
        if boundary.get("not_generalizable_to_third_party") is not True:
            failures.append("capability_boundary.not_generalizable_to_third_party must be true")
        if boundary.get("forbidden_actions_absent") is not True:
            failures.append("capability_boundary.forbidden_actions_absent must be true")

    listed_required = set(payload.get("required_cases", []))
    missing_required_list = sorted(REQUIRED_CASES - listed_required)
    if missing_required_list:
        failures.append(f"required_cases missing {missing_required_list}")

    cases = payload.get("cases")
    if not isinstance(cases, list):
        failures.append("cases must be a list")
        cases = []

    ids: list[str] = []
    rejected_cases: list[str] = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            failures.append(f"cases[{index}] must be an object")
            continue
        missing_fields = sorted(REQUIRED_FIELDS - set(case))
        if missing_fields:
            failures.append(f"{case.get('id', f'cases[{index}]')} missing fields {missing_fields}")
        case_id = case.get("id")
        if isinstance(case_id, str):
            ids.append(case_id)
        if case.get("expected_result") != "REJECTED":
            failures.append(f"{case_id} expected_result must be REJECTED")
        else:
            rejected_cases.append(str(case_id))
        for key in ("category", "input_surface", "observed_signal", "expected_classification", "safe_next_action"):
            if not isinstance(case.get(key), str) or not case.get(key):
                failures.append(f"{case_id} {key} must be a non-empty string")
        action = str(case.get("safe_next_action", "")).lower()
        if any(forbidden in action for forbidden in ("bypass", "spoof", "reuse_token", "clearance_cookie")):
            failures.append(f"{case_id} safe_next_action contains forbidden action language")

    duplicate_ids = sorted({case_id for case_id in ids if ids.count(case_id) > 1})
    if duplicate_ids:
        failures.append(f"duplicate case ids {duplicate_ids}")
    missing_cases = sorted(REQUIRED_CASES - set(ids))
    if missing_cases:
        failures.append(f"cases missing {missing_cases}")
    unexpected_cases = sorted(set(ids) - REQUIRED_CASES)
    if unexpected_cases:
        failures.append(f"unexpected cases {unexpected_cases}")

    classified_cases = sorted(ids)
    return result(path, failures, classified_cases, sorted(rejected_cases))


def result(path: Path, failures: list[str], classified_cases: list[str], rejected_cases: list[str]) -> dict[str, Any]:
    return {
        "tool": "validate_drift_cases",
        "status": "PASS" if not failures else "FAIL",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "case_file": str(path),
        "case_count": len(classified_cases),
        "classified_cases": classified_cases,
        "rejected_cases": rejected_cases,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate fingerprint drift/negative cases")
    parser.add_argument("--cases", default=str(Path(__file__).resolve().with_name("drift_cases.json")))
    parser.add_argument("--write-report", default="")
    args = parser.parse_args()
    payload = validate(Path(args.cases))
    if args.write_report:
        report_path = Path(args.write_report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
