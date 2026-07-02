#!/usr/bin/env python3
"""Evaluate the latest local CAPTCHA benchmark for a run id."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Report CAPTCHA model/baseline eval metrics")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    model_eval_path = REPO_ROOT / "public-range-evidence" / "raw" / "captcha-model-training" / args.run_id / "model-eval.json"
    if model_eval_path.is_file():
        model_eval = json.loads(model_eval_path.read_text(encoding="utf-8-sig"))
        metrics_path = Path(model_eval["trained_benchmark_metrics_path"])
        data = json.loads(metrics_path.read_text(encoding="utf-8-sig"))
        payload = {
            "tool": "captcha_model_eval",
            "status": "PASS",
            "run_id": args.run_id,
            "model_type": model_eval.get("model_type"),
            "trained": model_eval.get("trained"),
            "checkpoint_path": model_eval.get("checkpoint_path"),
            "dataset_manifest_path": model_eval.get("dataset_manifest_path"),
            "split_manifest_path": model_eval.get("split_manifest_path"),
            "model_config_path": model_eval.get("model_config_path"),
            "training_log_path": model_eval.get("training_log_path"),
            "validation_metrics": model_eval.get("validation_metrics"),
            "test_metrics": model_eval.get("test_metrics"),
            "baseline_comparison": model_eval.get("baseline_comparison"),
            "model_status": model_eval.get("status"),
            "metrics_path": str(metrics_path),
            "metrics": data.get("metrics", {}),
            "per_difficulty_metrics": data.get("per_difficulty_metrics", {}),
            "leakage_check": data.get("leakage_check", {}),
            "failure_case_counts": data.get("failure_case_counts", {}),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    path = REPO_ROOT / "public-range-evidence" / "raw" / "captcha-vision-lab" / args.run_id / "benchmark-metrics.json"
    if not path.is_file():
        raise SystemExit(f"missing benchmark metrics: {path}")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    payload = {
        "tool": "captcha_model_eval",
        "status": "PASS",
        "run_id": args.run_id,
        "model_type": "baseline_solver",
        "metrics_path": str(path),
        "metrics": data.get("metrics", {}),
        "per_difficulty_metrics": data.get("per_difficulty_metrics", {}),
        "leakage_check": data.get("leakage_check", {}),
        "failure_case_counts": data.get("failure_case_counts", {}),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
