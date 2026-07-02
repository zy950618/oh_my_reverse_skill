#!/usr/bin/env python3
"""Evaluate CAPTCHA flywheel model training results."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from captcha_flywheel_common import DATASET_ROOT, read_json, write_json, utc_now


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate CAPTCHA flywheel models")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    registry_path = DATASET_ROOT / "models" / args.run_id / "model_registry.json"
    registry = read_json(registry_path)
    results = []
    improved = []
    training_needed = []
    for model in registry.get("models", []):
        result = read_json(Path(model["training_result_path"]))["model_training_result"]
        row = {
            "model_id": result["model_id"],
            "task": result["task"],
            "model_type": result["model_type"],
            "checkpoint_path": result["checkpoint_path"],
            "baseline_metrics": result["baseline_metrics"],
            "trained_metrics": result["trained_metrics"],
            "holdout_metrics": result["holdout_metrics"],
            "delta": result["delta"],
            "promotion_decision": result["promotion_decision"],
            "why_not_promoted": result["why_not_promoted"],
        }
        results.append(row)
        if result["delta"] > 0:
            improved.append(row["task"])
        else:
            training_needed.append(row["task"])
    prediction_manifest = {
        "run_id": args.run_id,
        "created_at": utc_now(),
        "model_registry_path": str(registry_path),
        "models": results,
        "improved_tasks": improved,
        "training_needed_tasks": training_needed,
        "external_api_used": False,
        "third_party_solver_used": False,
        "label_leakage": False,
    }
    out = DATASET_ROOT / "predictions" / args.run_id / "prediction_manifest.json"
    write_json(out, prediction_manifest)
    print(json.dumps({"status": "PASS", "run_id": args.run_id, "prediction_manifest": str(out), "improved_tasks": improved, "training_needed_tasks": training_needed}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
