#!/usr/bin/env python3
"""Validate browser context isolation contracts and local airline lab skeleton."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_ISOLATION = {
    "browser_context",
    "cookie_jar",
    "local_storage",
    "session_storage",
    "indexed_db",
    "service_worker",
    "token_cache",
    "fingerprint_surface_hash",
    "session_owner",
    "worker_owner",
}

REQUIRED_METRICS = {
    "request_count",
    "success_count",
    "failure_count",
    "failure_rate",
    "http_403",
    "http_429",
    "http_503",
    "p95_ms",
    "stop_condition",
    "kill_switch",
    "cross_worker_pollution_count",
}

REQUIRED_LAB_PATHS = [
    "mock_server",
    "fastapi_adapter",
    "fixtures",
    "replay",
    "reports",
    "sdk_examples",
    "validation_report.json",
    "cleanup.md",
]
FRESH_EVIDENCE = "public-range-evidence/fingerprint-risk-lab/fresh-evidence"


def load_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {}, [f"cannot parse JSON {path}: {exc!r}"]
    if not isinstance(payload, dict):
        return {}, [f"{path} must contain a JSON object"]
    return payload, []


def validate_manifest(path: Path) -> list[str]:
    failures: list[str] = []
    manifest, errors = load_json(path)
    failures.extend(errors)
    if not manifest:
        return failures
    if manifest.get("schema_version") != "browser-context-isolation/v1":
        failures.append("schema_version must be browser-context-isolation/v1")
    if manifest.get("status") != "isolation_contract":
        failures.append("status must be isolation_contract")
    if manifest.get("worker_ladder") != [1, 2, 5, 10]:
        failures.append("worker_ladder must be [1, 2, 5, 10]")
    missing_isolation = sorted(REQUIRED_ISOLATION - set(manifest.get("required_isolation", [])))
    if missing_isolation:
        failures.append(f"required_isolation missing {missing_isolation}")
    missing_metrics = sorted(REQUIRED_METRICS - set(manifest.get("required_metrics", [])))
    if missing_metrics:
        failures.append(f"required_metrics missing {missing_metrics}")
    boundary = manifest.get("capability_boundary")
    if not isinstance(boundary, dict):
        failures.append("capability_boundary object is required")
    else:
        if boundary.get("concurrency_positive_requires_business_ledger") is not True:
            failures.append("concurrency_positive_requires_business_ledger must be true")
        if boundary.get("not_generalizable_to_third_party") is not True:
            failures.append("not_generalizable_to_third_party must be true")
    return failures


def validate_airline_lab(root: Path) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    for relative in REQUIRED_LAB_PATHS:
        path = root / relative
        if not path.exists():
            failures.append(f"airline lab missing {relative}")
    report_path = root / "validation_report.json"
    if report_path.is_file():
        report, errors = load_json(report_path)
        failures.extend(errors)
        if report:
            if report.get("schema_version") != "airline-lab-order-flow/v1":
                failures.append("validation_report.schema_version must be airline-lab-order-flow/v1")
            if report.get("execution_status") != "STRUCTURE_ONLY":
                failures.append("validation_report.execution_status must be STRUCTURE_ONLY")
            if report.get("live_site_calls_performed") is not False:
                failures.append("validation_report.live_site_calls_performed must be false")
            if report.get("capability_status") not in {"memory_only", "unverified"}:
                failures.append("validation_report.capability_status must be memory_only or unverified")
    fixtures = sorted((root / "fixtures").glob("*.json")) if (root / "fixtures").is_dir() else []
    if not fixtures:
        warnings.append("no fixture JSON files found under airline lab fixtures")
    return failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate browser context isolation lab")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--manifest", default="7-指纹风控层/_lab/browser_context_isolation_manifest.json")
    parser.add_argument("--airline-lab", default="public-range-evidence/airline-lab-order-flow")
    args = parser.parse_args()
    repo_root = Path(args.repo_root)
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = repo_root / manifest_path
    airline_lab = Path(args.airline_lab)
    if not airline_lab.is_absolute():
        airline_lab = repo_root / airline_lab
    failures = validate_manifest(manifest_path)
    fresh_root = repo_root / FRESH_EVIDENCE
    for name in ("context_isolation_report.json", "freshness_manifest.json", "validation_report.json"):
        if not (fresh_root / name).is_file():
            failures.append(f"fresh evidence missing: {FRESH_EVIDENCE}/{name}")
    if (fresh_root / "validation_report.json").is_file():
        report, errors = load_json(fresh_root / "validation_report.json")
        failures.extend(errors)
        for key in ("clean_context_observed", "polluted_context_observed", "reused_context_observed", "context_isolation_checked"):
            if report.get(key) is not True:
                failures.append(f"fresh validation {key} must be true")
    lab_failures, warnings = validate_airline_lab(airline_lab)
    failures.extend(lab_failures)
    payload = {
        "tool": "validate_browser_context_isolation",
        "status": "PASS" if not failures else "FAIL",
        "manifest": str(manifest_path),
        "airline_lab": str(airline_lab),
        "failures": failures,
        "warnings": warnings,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
