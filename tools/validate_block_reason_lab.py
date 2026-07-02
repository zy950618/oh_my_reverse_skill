#!/usr/bin/env python3
"""Validate the fingerprint block-reason diagnostics lab contract."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


FORBIDDEN = {
    "webdriver_hide",
    "fingerprint_spoof",
    "proxy_rotation_evasion",
    "clearance_cookie_reuse",
    "risk_token_reuse",
    "waf_bypass",
    "captcha_bypass",
    "rate_limit_evasion",
}

REQUIRED_INPUTS = {
    "authorization_scope",
    "target_class",
    "status_code",
    "response_class",
    "request_context",
    "session_context",
    "surface_report_ref",
    "fact_labels",
}

REQUIRED_REASONS = {
    "blocked_by_scope",
    "blocked_by_auth",
    "blocked_by_stale_state",
    "blocked_by_fingerprint_signal",
    "blocked_by_rate_limit",
    "blocked_by_business_rule",
    "unknown",
}
FRESH_EVIDENCE = "public-range-evidence/fingerprint-risk-lab/fresh-evidence"


def load_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {}, [f"cannot parse JSON {path}: {exc!r}"]
    if not isinstance(payload, dict):
        return {}, [f"{path} must contain a JSON object"]
    return payload, []


def validate(repo_root: Path, manifest_path: Path) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    manifest, errors = load_json(manifest_path)
    failures.extend(errors)
    if manifest:
        if manifest.get("schema_version") != "block-reason-lab/v1":
            failures.append("schema_version must be block-reason-lab/v1")
        if manifest.get("status") != "diagnostics_only":
            failures.append("status must be diagnostics_only")
        if manifest.get("fact_policy") != "separate_observed_from_derived":
            failures.append("fact_policy must be separate_observed_from_derived")
        forbidden = set(manifest.get("forbidden_actions", []))
        allowed = set(manifest.get("allowed_next_actions", []))
        missing_forbidden = sorted(FORBIDDEN - forbidden)
        if missing_forbidden:
            failures.append(f"forbidden_actions missing {missing_forbidden}")
        overlap = sorted(forbidden & allowed)
        if overlap:
            failures.append(f"allowed_next_actions overlap forbidden_actions: {overlap}")
        missing_inputs = sorted(REQUIRED_INPUTS - set(manifest.get("required_inputs", [])))
        if missing_inputs:
            failures.append(f"required_inputs missing {missing_inputs}")
        missing_reasons = sorted(REQUIRED_REASONS - set(manifest.get("allowed_block_reasons", [])))
        if missing_reasons:
            failures.append(f"allowed_block_reasons missing {missing_reasons}")
        output = set(manifest.get("required_output", []))
        for key in ("diagnostic_ledger", "attribution_level", "evidence_refs", "safe_next_action"):
            if key not in output:
                failures.append(f"required_output missing {key}")
        boundary = manifest.get("capability_boundary")
        if not isinstance(boundary, dict) or boundary.get("positive_allowed") is not False:
            failures.append("capability_boundary.positive_allowed must be false")

    for relative in (
        "7-指纹风控层/references/block-reason-diagnostics.md",
        "7-指纹风控层/evals/002-block-reason-attribution-boundary.yaml",
    ):
        path = repo_root / relative
        if not path.is_file():
            failures.append(f"required file missing: {relative}")
            continue
        text = path.read_text(encoding="utf-8-sig").lower()
        if "safe_next_action" not in text and "safe next action" not in text:
            warnings.append(f"{relative} should mention safe next action")

    fresh_root = repo_root / FRESH_EVIDENCE
    for name in ("block_reason_report.json", "freshness_manifest.json", "validation_report.json", "drift_policy.md"):
        if not (fresh_root / name).is_file():
            failures.append(f"fresh evidence missing: {FRESH_EVIDENCE}/{name}")
    if (fresh_root / "validation_report.json").is_file():
        report, errors = load_json(fresh_root / "validation_report.json")
        failures.extend(errors)
        if report.get("block_reason_classified") is not True:
            failures.append("fresh validation block_reason_classified must be true")

    return {
        "tool": "validate_block_reason_lab",
        "status": "PASS" if not failures else "FAIL",
        "manifest": str(manifest_path),
        "failures": failures,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate block reason diagnostics lab manifest")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--manifest", default="7-指纹风控层/_lab/block_reason_lab_manifest.json")
    args = parser.parse_args()
    repo_root = Path(args.repo_root)
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = repo_root / manifest_path
    payload = validate(repo_root, manifest_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
