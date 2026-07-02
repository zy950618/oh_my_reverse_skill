#!/usr/bin/env python3
"""Validate a CAPTCHA model training report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_STAGES = {"dataset_audit", "label_audit", "train", "evaluate", "failure_review", "package"}
DEFAULT_REPORT = Path("public-range-evidence/captcha-model-lab/manifests/training_report.json")


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


def require_metric(metrics: dict, key: str) -> float:
    value = metrics.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        fail(f"metrics.{key} must be numeric")
    if not 0 <= float(value) <= 1 and key.endswith("accuracy"):
        fail(f"metrics.{key} must be between 0 and 1")
    return float(value)


def validate_report(path: Path) -> None:
    report = load_json(path)
    if report.get("manifest_type") != "captcha_training_report":
        fail("manifest_type must be captcha_training_report")
    for key in ("schema_version", "run_id", "dataset_id", "model_family"):
        if not report.get(key):
            fail(f"{key} is required")

    stages = set(require_list(report, "pipeline"))
    missing = REQUIRED_STAGES - stages
    if missing:
        fail(f"pipeline missing stages: {', '.join(sorted(missing))}")

    reproducibility = require_dict(report, "reproducibility")
    if not isinstance(reproducibility.get("seed"), int):
        fail("reproducibility.seed must be an integer")
    if not reproducibility.get("code_version"):
        fail("reproducibility.code_version is required")

    metrics = require_dict(report, "metrics")
    require_metric(metrics, "validation_accuracy")
    require_metric(metrics, "test_accuracy")
    if "mean_action_error_css_px" not in metrics:
        fail("metrics.mean_action_error_css_px is required")

    artifacts = require_list(report, "artifacts")
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict) or not artifact.get("role") or not artifact.get("path"):
            fail(f"artifacts[{index}] requires role and path")

    boundary = require_dict(report, "capability_boundary")
    if boundary.get("third_party_positive_claim") is not False:
        fail("capability_boundary.third_party_positive_claim must be false")
    if boundary.get("requires_business_api_repeat_verified") is not True:
        fail("capability_boundary.requires_business_api_repeat_verified must be true")


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
