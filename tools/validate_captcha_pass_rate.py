#!/usr/bin/env python3
"""Validate CAPTCHA pass-rate metrics."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


DEFAULT_REPORT = Path("public-range-evidence/captcha-model-lab/manifests/pass_rate_report.json")


def fail(message: str) -> None:
    raise ValueError(message)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        fail("report root must be an object")
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


def require_count(data: dict, key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        fail(f"{key} must be a non-negative integer")
    return value


def validate_rate(attempts: int, passes: int, pass_rate: object, label: str) -> None:
    if attempts <= 0:
        fail(f"{label} attempts must be positive")
    if passes > attempts:
        fail(f"{label} passes cannot exceed attempts")
    if not isinstance(pass_rate, (int, float)) or isinstance(pass_rate, bool):
        fail(f"{label} pass_rate must be numeric")
    expected = passes / attempts
    if not math.isclose(float(pass_rate), expected, rel_tol=0.0, abs_tol=1e-9):
        fail(f"{label} pass_rate must equal passes / attempts")


def validate_report(path: Path) -> None:
    report = load_json(path)
    if report.get("manifest_type") != "captcha_pass_rate_report":
        fail("manifest_type must be captcha_pass_rate_report")
    for key in ("schema_version", "run_id"):
        if not report.get(key):
            fail(f"{key} is required")

    attempts = require_count(report, "attempts")
    passes = require_count(report, "passes")
    validate_rate(attempts, passes, report.get("pass_rate"), "overall")
    require_dict(report, "confidence_interval")

    bucket_attempts = 0
    bucket_passes = 0
    for index, bucket in enumerate(require_list(report, "buckets")):
        if not isinstance(bucket, dict):
            fail(f"buckets[{index}] must be an object")
        for key in ("provider", "challenge_type"):
            if not bucket.get(key):
                fail(f"buckets[{index}].{key} is required")
        b_attempts = require_count(bucket, "attempts")
        b_passes = require_count(bucket, "passes")
        validate_rate(b_attempts, b_passes, bucket.get("pass_rate"), f"buckets[{index}]")
        bucket_attempts += b_attempts
        bucket_passes += b_passes
    if bucket_attempts != attempts or bucket_passes != passes:
        fail("bucket totals must equal overall attempts and passes")

    require_list(report, "negative_controls")
    boundary = require_dict(report, "capability_boundary")
    if boundary.get("third_party_positive_claim") is not False:
        fail("capability_boundary.third_party_positive_claim must be false")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", nargs="?", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    try:
        validate_report(args.report)
    except Exception as exc:
        print(f"FAIL {args.report}: {exc}", file=sys.stderr)
        return 1
    print(f"PASS {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
