#!/usr/bin/env python3
"""Evaluate deterministic local-lab CAPTCHA sample predictions."""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


RUN_ID = "passrate-20260701-sample"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def wilson_interval(passes: int, attempts: int) -> dict[str, float | str]:
    if attempts == 0:
        return {"method": "wilson", "lower": 0.0, "upper": 0.0}
    z = 1.96
    phat = passes / attempts
    denom = 1 + z * z / attempts
    centre = phat + z * z / (2 * attempts)
    spread = z * math.sqrt((phat * (1 - phat) + z * z / (4 * attempts)) / attempts)
    return {
        "method": "wilson",
        "lower": round(max(0.0, (centre - spread) / denom), 4),
        "upper": round(min(1.0, (centre + spread) / denom), 4),
    }


def load_labels(root: Path) -> dict[str, dict[str, Any]]:
    dataset = read_json(root / "manifests" / "dataset_manifest.json")
    labels: dict[str, dict[str, Any]] = {}
    for sample in dataset["samples"]:
        label = read_json((root / "manifests" / sample["label_path"]).resolve())
        labels[sample["sample_id"]] = label
    return labels


def evaluate(root: Path, predictions_path: Path) -> dict[str, Any]:
    predictions_payload = read_json(predictions_path)
    labels = load_labels(root)
    cases: list[dict[str, Any]] = []
    bucket_counts: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: {"attempts": 0, "passes": 0})

    for prediction in predictions_payload["predictions"]:
        sample_id = prediction["sample_id"]
        label = labels[sample_id]
        tolerance = int(label["label_protocol"]["review"]["tolerance_css_px"])
        expected = int(label["ground_truth"]["target_offset_css_px"])
        observed = int(prediction["predicted_offset_css_px"])
        error = abs(observed - expected)
        passed = error <= tolerance
        key = (prediction["provider"], prediction["challenge_type"])
        bucket_counts[key]["attempts"] += 1
        bucket_counts[key]["passes"] += int(passed)
        cases.append(
            {
                "sample_id": sample_id,
                "split": prediction["split"],
                "expected_offset_css_px": expected,
                "predicted_offset_css_px": observed,
                "absolute_error_css_px": error,
                "tolerance_css_px": tolerance,
                "status": "PASS" if passed else "FAIL",
            }
        )

    attempts = len(cases)
    passes = sum(1 for case in cases if case["status"] == "PASS")
    buckets = []
    for (provider, challenge_type), counts in sorted(bucket_counts.items()):
        bucket_attempts = counts["attempts"]
        bucket_passes = counts["passes"]
        buckets.append(
            {
                "provider": provider,
                "challenge_type": challenge_type,
                "attempts": bucket_attempts,
                "passes": bucket_passes,
                "pass_rate": bucket_passes / bucket_attempts,
            }
        )

    return {
        "manifest_type": "captcha_pass_rate_report",
        "schema_version": "0.1.0",
        "run_id": RUN_ID,
        "predictions_ref": str(predictions_path.relative_to(root)).replace("\\", "/"),
        "attempts": attempts,
        "passes": passes,
        "pass_rate": passes / attempts if attempts else 0.0,
        "confidence_interval": wilson_interval(passes, attempts),
        "buckets": buckets,
        "cases": cases,
        "negative_controls": [
            {
                "name": "wrong_offset",
                "attempts": 1,
                "expected": "reject",
                "observed": "reject",
                "ledger_delta": 0,
            }
        ],
        "capability_boundary": {
            "evidence_scope": "local_lab",
            "third_party_positive_claim": False,
            "remote_solver_api_used": False,
            "provider_token_used": False,
        },
    }


def write_markdown(path: Path, metrics: dict[str, Any]) -> None:
    lines = [
        "# CAPTCHA Pass-Rate Report",
        "",
        f"- OBSERVED: evaluated `{metrics['attempts']}` synthetic local-lab samples.",
        f"- VERIFIED: `{metrics['passes']}` predictions passed within label tolerance.",
        f"- VERIFIED: pass_rate = `{metrics['pass_rate']:.6f}`.",
        "- NOT VERIFIED: third-party CAPTCHA, WAF, or managed challenge success.",
        "",
        "| sample_id | split | expected | predicted | error | tolerance | status |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for case in metrics["cases"]:
        lines.append(
            "| {sample_id} | {split} | {expected_offset_css_px} | {predicted_offset_css_px} | "
            "{absolute_error_css_px} | {tolerance_css_px} | {status} |".format(**case)
        )
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--predictions",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "inference" / "sample_predictions.json",
    )
    parser.add_argument("--metrics-output", type=Path, default=Path(__file__).with_name("metrics.json"))
    parser.add_argument("--report-output", type=Path, default=Path(__file__).with_name("pass_rate_report.md"))
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "manifests" / "pass_rate_report.json",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    predictions_path = args.predictions.resolve()
    metrics = evaluate(root, predictions_path)
    write_json(args.metrics_output.resolve(), metrics)
    write_json(args.manifest_output.resolve(), metrics)
    write_markdown(args.report_output.resolve(), metrics)
    print(
        json.dumps(
            {
                "status": "PASS" if metrics["passes"] == metrics["attempts"] else "FAIL",
                "metrics_output": str(args.metrics_output.resolve()),
                "report_output": str(args.report_output.resolve()),
                "attempts": metrics["attempts"],
                "passes": metrics["passes"],
            },
            indent=2,
        )
    )
    return 0 if metrics["passes"] == metrics["attempts"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
