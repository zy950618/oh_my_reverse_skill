#!/usr/bin/env python3
"""Validate a CAPTCHA model package manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_PROHIBITED_CLAIMS = {
    "third_party_captcha_bypass",
    "managed_challenge_auto_pass",
    "provider_success_without_business_repeat_verified",
}
DEFAULT_MANIFEST = Path("public-range-evidence/captcha-model-lab/manifests/package_manifest.json")


def fail(message: str) -> None:
    raise ValueError(message)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        fail("manifest root must be an object")
    return data


def require_dict(data: dict, key: str) -> dict:
    value = data.get(key)
    if not isinstance(value, dict):
        fail(f"{key} must be an object")
    return value


def require_list(data: dict, key: str) -> list:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        fail(f"{key} must be a non-empty list")
    return value


def resolve(base: Path, relative: str) -> Path:
    return (base.parent / relative).resolve()


def validate_manifest(path: Path) -> None:
    manifest = load_json(path)
    if manifest.get("manifest_type") != "captcha_model_package":
        fail("manifest_type must be captcha_model_package")
    for key in (
        "schema_version",
        "model_package_id",
        "package_version",
        "dataset_ref",
        "training_report_ref",
        "pass_rate_report_ref",
    ):
        if not manifest.get(key):
            fail(f"{key} is required")
    for ref_key in ("dataset_ref", "training_report_ref", "pass_rate_report_ref"):
        ref_path = resolve(path, manifest[ref_key])
        if not ref_path.is_file():
            fail(f"{ref_key} does not exist: {ref_path}")

    files = require_list(manifest, "files")
    for index, item in enumerate(files):
        if not isinstance(item, dict) or not item.get("role") or not item.get("path"):
            fail(f"files[{index}] requires role and path")
        file_path = resolve(path, item["path"])
        if not file_path.is_file():
            fail(f"files[{index}].path does not exist: {file_path}")

    contract = require_dict(manifest, "inference_contract")
    for key in ("input", "output", "error_modes"):
        if key not in contract:
            fail(f"inference_contract.{key} is required")
    if contract["output"] != "captcha_action_schema@0.1.0":
        fail("inference_contract.output must be captcha_action_schema@0.1.0")
    if not isinstance(contract["error_modes"], list) or not contract["error_modes"]:
        fail("inference_contract.error_modes must be a non-empty list")

    allowed_use = set(require_list(manifest, "allowed_use"))
    if not allowed_use <= {"local_lab", "owned_authorized_target"}:
        fail("allowed_use contains unsupported scope")
    prohibited_claims = set(require_list(manifest, "prohibited_claims"))
    missing = REQUIRED_PROHIBITED_CLAIMS - prohibited_claims
    if missing:
        fail(f"prohibited_claims missing: {', '.join(sorted(missing))}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args(argv)
    try:
        validate_manifest(args.manifest)
    except Exception as exc:
        print(f"FAIL {args.manifest}: {exc}", file=sys.stderr)
        return 1
    print(f"PASS {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
