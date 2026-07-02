#!/usr/bin/env python3
"""Validate local-lab CAPTCHA negative cases.

The validator is intentionally local and deterministic. It checks that each
negative fixture is rejected for its declared reason and that the valid sample
prediction/pass-rate artifacts still describe a passing local synthetic set.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


REQUIRED_CASES = {
    "invalid_image_size",
    "missing_label",
    "bad_coordinate_out_of_bounds",
    "bad_slider_offset",
    "wrong_captcha_type",
    "low_confidence_prediction",
    "missing_model_artifact",
    "broken_package_manifest",
    "mobile_h5_dpr_mismatch",
}
REQUIRED_PACKAGE_KEYS = {
    "manifest_type",
    "schema_version",
    "model_package_id",
    "package_version",
    "dataset_ref",
    "training_report_ref",
    "pass_rate_report_ref",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def fail(message: str) -> None:
    raise ValueError(message)


def detect_reason(root: Path, case: dict[str, Any]) -> str:
    name = case.get("name")
    payload = case.get("payload")
    if not isinstance(payload, dict):
        fail(f"{name}: payload must be an object")

    if name == "invalid_image_size":
        size = payload.get("image_size_px", {})
        if int(size.get("width", 0)) <= 0 or int(size.get("height", 0)) <= 0:
            return "image_size_invalid"
    elif name == "missing_label":
        label_path = payload.get("label_path")
        if not label_path or not (root / "manifests" / str(label_path)).resolve().is_file():
            return "label_missing"
    elif name == "bad_coordinate_out_of_bounds":
        viewport = payload.get("viewport", {})
        action = payload.get("action", {})
        x = float(action.get("x", -1))
        y = float(action.get("y", -1))
        width = float(viewport.get("width", 0))
        height = float(viewport.get("height", 0))
        if x < 0 or y < 0 or x > width or y > height:
            return "coordinate_out_of_bounds"
    elif name == "bad_slider_offset":
        expected = int(payload.get("expected_offset_css_px", 0))
        predicted = int(payload.get("predicted_offset_css_px", 0))
        tolerance = int(payload.get("tolerance_css_px", 0))
        if abs(predicted - expected) > tolerance:
            return "slider_offset_out_of_tolerance"
    elif name == "wrong_captcha_type":
        supported = set(payload.get("supported_challenge_types", []))
        if payload.get("challenge_type") not in supported:
            return "unsupported_captcha_type"
    elif name == "low_confidence_prediction":
        if float(payload.get("confidence", 0)) < float(payload.get("minimum_confidence", 1)):
            return "confidence_below_threshold"
    elif name == "missing_model_artifact":
        item = payload.get("package_file", {})
        if not (root / "manifests" / str(item.get("path", ""))).resolve().is_file():
            return "model_artifact_missing"
    elif name == "broken_package_manifest":
        manifest = payload.get("manifest", {})
        missing = REQUIRED_PACKAGE_KEYS - set(manifest)
        declared_missing = set(payload.get("missing_required_keys", []))
        if missing and declared_missing <= missing:
            return "package_manifest_invalid"
    elif name == "mobile_h5_dpr_mismatch":
        viewport_dpr = float(payload.get("viewport", {}).get("device_pixel_ratio", 0))
        transform_dpr = float(payload.get("mobile_h5_transform", {}).get("device_pixel_ratio", 0))
        if not math.isclose(viewport_dpr, transform_dpr, rel_tol=0.0, abs_tol=1e-9):
            return "mobile_h5_dpr_mismatch"

    return "not_rejected"


def validate_valid_samples(root: Path) -> dict[str, Any]:
    dataset = read_json(root / "manifests" / "dataset_manifest.json")
    predictions = read_json(root / "inference" / "sample_predictions.json")
    metrics = read_json(root / "eval" / "metrics.json")
    package = read_json(root / "manifests" / "package_manifest.json")

    samples = dataset.get("samples", [])
    if len(samples) != 3:
        fail("valid dataset must contain exactly 3 sample fixtures")
    for sample in samples:
        for key in ("image_path", "label_path"):
            ref = (root / "manifests" / sample[key]).resolve()
            if not ref.is_file():
                fail(f"valid sample reference missing: {ref}")

    valid_predictions = predictions.get("predictions", [])
    if len(valid_predictions) != len(samples):
        fail("valid predictions count must match sample count")
    for prediction in valid_predictions:
        if prediction.get("prediction_status") != "ok":
            fail(f"{prediction.get('sample_id')}: prediction_status must be ok")
        if prediction.get("challenge_type") != "slider":
            fail(f"{prediction.get('sample_id')}: challenge_type must be slider")
        if float(prediction.get("confidence", 0)) < 0.8:
            fail(f"{prediction.get('sample_id')}: confidence must be >= 0.8")

    if metrics.get("attempts") != 3 or metrics.get("passes") != 3 or float(metrics.get("pass_rate", 0)) != 1.0:
        fail("valid pass-rate metrics must be 3/3 and pass_rate 1.0")

    for item in package.get("files", []):
        ref = (root / "manifests" / item["path"]).resolve()
        if not ref.is_file():
            fail(f"valid package file missing: {ref}")

    return {
        "sample_count": len(samples),
        "prediction_count": len(valid_predictions),
        "passes": metrics["passes"],
        "attempts": metrics["attempts"],
        "pass_rate": metrics["pass_rate"],
    }


def validate(root: Path, cases_path: Path) -> dict[str, Any]:
    manifest = read_json(cases_path)
    if manifest.get("manifest_type") != "captcha_negative_cases":
        fail("negative cases manifest_type must be captcha_negative_cases")
    boundary = manifest.get("capability_boundary", {})
    if boundary.get("third_party_positive_claim") is not False:
        fail("negative cases must not claim third-party CAPTCHA success")

    cases = manifest.get("cases")
    if not isinstance(cases, list):
        fail("cases must be a list")
    names = {case.get("name") for case in cases}
    missing = REQUIRED_CASES - names
    extra = names - REQUIRED_CASES
    if missing:
        fail(f"missing negative cases: {', '.join(sorted(missing))}")
    if extra:
        fail(f"unknown negative cases: {', '.join(sorted(str(item) for item in extra))}")

    detections = []
    for case in cases:
        expected = case.get("expected_reason")
        observed = detect_reason(root, case)
        if observed != expected:
            fail(f"{case.get('name')}: expected {expected}, observed {observed}")
        detections.append({"name": case["name"], "expected_reason": expected, "observed_reason": observed, "status": "PASS"})

    return {
        "status": "PASS",
        "valid_samples": validate_valid_samples(root),
        "negative_case_count": len(detections),
        "detections": detections,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--cases", type=Path, default=Path(__file__).with_name("cases.json"))
    args = parser.parse_args(argv)

    try:
        result = validate(args.root.resolve(), args.cases.resolve())
    except Exception as exc:
        print(json.dumps({"status": "FAIL", "reason": str(exc)}, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
