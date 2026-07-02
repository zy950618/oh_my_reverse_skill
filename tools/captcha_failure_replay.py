#!/usr/bin/env python3
"""Summarize failure replay before/after from local model results and action replay evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from captcha_flywheel_common import DATASET_ROOT, PUBLIC_ROOT, read_json, write_json, utc_now


def replay_from_public(run_id: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    targets = ["aliyun-compatible-lab", "shumei-compatible-lab", "gocaptcha-official", "opencaptchaworld"]
    for target in targets:
        path = PUBLIC_ROOT / target / f"{run_id}.json"
        if not path.is_file():
            continue
        data = read_json(path)
        families = data.get("action_replay", {}).get("metrics", {}).get("families", {})
        if isinstance(families, dict):
            for family, item in families.items():
                rows.append({
                    "family": f"{target}:{family}",
                    "after_success_rate": item.get("success_rate"),
                    "failure_remaining": item.get("failure_count"),
                    "promotion_decision": item.get("capability_status", data.get("capability_status")),
                })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay failure summary for CAPTCHA model flywheel")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    registry = read_json(DATASET_ROOT / "models" / args.run_id / "model_registry.json")
    before_after = []
    for model in registry.get("models", []):
        result = read_json(Path(model["training_result_path"]))["model_training_result"]
        before_after.append({
            "family": ",".join(model.get("families", [])),
            "before_success_rate": result["baseline_metrics"].get("success_rate"),
            "after_success_rate": result["trained_metrics"].get("success_rate"),
            "delta": result["delta"],
            "threshold_met": result["trained_metrics"].get("success_rate", 0) >= 0.8,
            "failure_remaining": result["failure_after"],
            "promotion_decision": "training_improved_waiting_action_replay" if result["delta"] > 0 else "training_needed",
        })
    public_replay = replay_from_public(args.run_id)
    report = {
        "run_id": args.run_id,
        "created_at": utc_now(),
        "before_after_action_replay": before_after,
        "public_action_replay_observed": public_replay,
        "decision": "model_failure_replay_improved" if any(item["delta"] > 0 for item in before_after) else "training_needed",
    }
    out = DATASET_ROOT / "failures" / args.run_id / "failure_replay.json"
    write_json(out, report)
    print(json.dumps({"status": "PASS", "run_id": args.run_id, "failure_replay": str(out), "improved": report["decision"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
