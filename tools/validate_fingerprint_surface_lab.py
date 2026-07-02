#!/usr/bin/env python3
"""Validate the fingerprint surface observation lab contract."""
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
    "unauthorized_challenge_processing",
}

REQUIRED_SURFACES = {
    "navigator.webdriver",
    "navigator.userAgent",
    "navigator.platform",
    "navigator.languages",
    "navigator.plugins",
    "hardwareConcurrency",
    "deviceMemory",
    "screen",
    "timezone",
    "locale",
    "canvas",
    "webgl",
    "audio",
    "fonts",
    "permissions",
    "webrtc",
    "clientHints",
    "networkTiming",
    "storageState",
}

REQUIRED_FILES = [
    "7-指纹风控层/references/fingerprint-surface-observation.md",
    "7-指纹风控层/evals/001-fingerprint-surface-observation-only.yaml",
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


def non_empty_list(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)


def validate(repo_root: Path, manifest_path: Path) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    manifest, errors = load_json(manifest_path)
    failures.extend(errors)
    if not manifest:
        return result(manifest_path, failures, warnings)

    if manifest.get("schema_version") != "fingerprint-surface-lab/v1":
        failures.append("schema_version must be fingerprint-surface-lab/v1")
    if manifest.get("status") != "observation_only":
        failures.append("status must be observation_only")
    if manifest.get("fact_policy") != "observed_derived_assumed_unverified_required":
        failures.append("fact_policy must require observed/derived/assumed/unverified labels")

    allowed = set(manifest.get("allowed_actions", []))
    forbidden = set(manifest.get("forbidden_actions", []))
    missing_forbidden = sorted(FORBIDDEN - forbidden)
    if missing_forbidden:
        failures.append(f"forbidden_actions missing {missing_forbidden}")
    overlap = sorted(allowed & forbidden)
    if overlap:
        failures.append(f"allowed_actions overlap forbidden_actions: {overlap}")

    surfaces = set(manifest.get("required_surfaces", []))
    missing_surfaces = sorted(REQUIRED_SURFACES - surfaces)
    if missing_surfaces:
        failures.append(f"required_surfaces missing {missing_surfaces}")

    evidence = manifest.get("evidence_requirements")
    if not isinstance(evidence, dict):
        failures.append("evidence_requirements object is required")
    else:
        for key in ("scope", "artifacts"):
            if not non_empty_list(evidence.get(key)):
                failures.append(f"evidence_requirements.{key} must be a non-empty string list")
        if int(evidence.get("minimum_repeat_count_for_consistency") or 0) < 3:
            failures.append("minimum_repeat_count_for_consistency must be >= 3")
        if int(evidence.get("minimum_profile_count_for_consistency") or 0) < 2:
            failures.append("minimum_profile_count_for_consistency must be >= 2")

    boundary = manifest.get("capability_boundary")
    if not isinstance(boundary, dict):
        failures.append("capability_boundary object is required")
    else:
        if boundary.get("positive_allowed") is not False:
            failures.append("capability_boundary.positive_allowed must be false")
        if boundary.get("not_generalizable_to_third_party") is not True:
            failures.append("capability_boundary.not_generalizable_to_third_party must be true")

    for relative in REQUIRED_FILES:
        path = repo_root / relative
        if not path.is_file():
            failures.append(f"required file missing: {relative}")
        else:
            text = path.read_text(encoding="utf-8-sig").lower()
            if "spoof" not in text or "evasion" not in text:
                warnings.append(f"{relative} does not explicitly mention spoof/evasion boundary")

    fresh_root = repo_root / FRESH_EVIDENCE
    for name in ("fingerprint_surface_report.json", "browser_vs_pure_api_diff.json", "freshness_manifest.json", "validation_report.json", "drift_policy.md"):
        if not (fresh_root / name).is_file():
            failures.append(f"fresh evidence missing: {FRESH_EVIDENCE}/{name}")
    if (fresh_root / "validation_report.json").is_file():
        report, errors = load_json(fresh_root / "validation_report.json")
        failures.extend(errors)
        for key in ("clean_context_observed", "polluted_context_observed", "reused_context_observed", "browser_vs_pure_api_diff_exists", "freshness_manifest_valid", "drift_policy_exists"):
            if report.get(key) is not True:
                failures.append(f"fresh validation {key} must be true")

    return result(manifest_path, failures, warnings)


def result(path: Path, failures: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "tool": "validate_fingerprint_surface_lab",
        "status": "PASS" if not failures else "FAIL",
        "manifest": str(path),
        "failures": failures,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate fingerprint surface lab manifest")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--manifest", default="7-指纹风控层/_lab/fingerprint_surface_lab_manifest.json")
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
