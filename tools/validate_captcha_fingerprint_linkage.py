#!/usr/bin/env python3
"""Validate CAPTCHA/fingerprint linkage boundaries and real-site observation packs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


FORBIDDEN = {
    "captcha_bypass",
    "solver_token_reuse",
    "webdriver_hide",
    "fingerprint_spoof",
    "proxy_rotation_evasion",
    "clearance_cookie_reuse",
    "risk_token_reuse",
    "unauthorized_challenge_processing",
}

REQUIRED_BOUNDARIES = {
    "challenge_endpoint_success_is_not_business_success",
    "captcha_token_is_not_reused",
    "fingerprint_surface_is_not_spoofed",
    "final_business_api_required_for_positive",
    "repeat_verified_required_for_success_claim",
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


def validate_manifest(path: Path) -> list[str]:
    failures: list[str] = []
    manifest, errors = load_json(path)
    failures.extend(errors)
    if not manifest:
        return failures
    if manifest.get("schema_version") != "captcha-fingerprint-linkage/v1":
        failures.append("schema_version must be captcha-fingerprint-linkage/v1")
    if manifest.get("status") != "diagnostics_only":
        failures.append("status must be diagnostics_only")
    missing_forbidden = sorted(FORBIDDEN - set(manifest.get("forbidden_actions", [])))
    if missing_forbidden:
        failures.append(f"forbidden_actions missing {missing_forbidden}")
    missing_boundaries = sorted(REQUIRED_BOUNDARIES - set(manifest.get("required_boundaries", [])))
    if missing_boundaries:
        failures.append(f"required_boundaries missing {missing_boundaries}")
    boundary = manifest.get("capability_boundary")
    if not isinstance(boundary, dict) or boundary.get("positive_allowed") is not False:
        failures.append("capability_boundary.positive_allowed must be false")
    return failures


def validate_pack(path: Path) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    payload, errors = load_json(path)
    failures.extend(errors)
    if payload:
        if payload.get("schema_version") != "real-site-observation-pack/v1":
            failures.append("schema_version must be real-site-observation-pack/v1")
        if payload.get("pack_status") == "STRUCTURE_ONLY":
            failures.append("pack_status must be upgraded from STRUCTURE_ONLY")
        if payload.get("execution_status") not in {"LOCAL_FIXTURE_VALIDATED", "AUTHORIZED_LIVE_READY"}:
            failures.append("execution_status must be LOCAL_FIXTURE_VALIDATED or AUTHORIZED_LIVE_READY")
        if payload.get("live_capture_performed") is not False:
            failures.append("live_capture_performed must be false")
        if payload.get("business_data_status") != "NOT_RUN":
            failures.append("business_data_status must be NOT_RUN")
        if payload.get("capability_status") not in {"memory_only", "unverified"}:
            failures.append("capability_status must be memory_only or unverified")
        facts = payload.get("fact_labels")
        if not isinstance(facts, dict):
            failures.append("fact_labels object is required")
        else:
            if not isinstance(facts.get("unverified"), list) or not facts.get("unverified"):
                failures.append("packs must list unverified live facts")
        forbidden = set(payload.get("forbidden_actions", []))
        missing_forbidden = sorted(FORBIDDEN - forbidden)
        if missing_forbidden:
            failures.append(f"forbidden_actions missing {missing_forbidden}")
        if payload.get("positive_allowed") is True:
            failures.append("positive_allowed must not be true in structure-only packs")
        if not payload.get("planned_observation_surfaces"):
            warnings.append("planned_observation_surfaces is empty")
    return {
        "path": str(path),
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate CAPTCHA/fingerprint linkage lab and real-site packs")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--manifest", default="7-指纹风控层/_lab/captcha_fingerprint_linkage_manifest.json")
    parser.add_argument("--packs-root", default="public-range-evidence/real-site-observation-pack")
    args = parser.parse_args()
    repo_root = Path(args.repo_root)
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = repo_root / manifest_path
    packs_root = Path(args.packs_root)
    if not packs_root.is_absolute():
        packs_root = repo_root / packs_root
    failures = validate_manifest(manifest_path)
    fresh_root = repo_root / FRESH_EVIDENCE
    for name in ("captcha_linkage_report.json", "freshness_manifest.json", "validation_report.json"):
        if not (fresh_root / name).is_file():
            failures.append(f"fresh evidence missing: {FRESH_EVIDENCE}/{name}")
    if (fresh_root / "validation_report.json").is_file():
        report, errors = load_json(fresh_root / "validation_report.json")
        failures.extend(errors)
        if report.get("captcha_linkage_checked") is not True:
            failures.append("fresh validation captcha_linkage_checked must be true")
    pack_files = sorted(packs_root.glob("airlines/*/observation-pack.json")) if packs_root.is_dir() else []
    if not pack_files:
        failures.append(f"no observation-pack.json files under {packs_root}")
    pack_results = [validate_pack(path) for path in pack_files]
    failures.extend(
        f"{item['path']}: {failure}"
        for item in pack_results
        for failure in item["failures"]
    )
    payload = {
        "tool": "validate_captcha_fingerprint_linkage",
        "status": "PASS" if not failures else "FAIL",
        "manifest": str(manifest_path),
        "packs_root": str(packs_root),
        "pack_count": len(pack_files),
        "failures": failures,
        "pack_results": pack_results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
