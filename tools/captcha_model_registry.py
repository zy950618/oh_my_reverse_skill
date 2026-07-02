#!/usr/bin/env python3
"""Validate and summarize CAPTCHA model registry entries."""
from __future__ import annotations

import argparse
import json

from captcha_flywheel_common import DATASET_ROOT, read_json, write_json, utc_now


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize CAPTCHA model registry")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    path = DATASET_ROOT / "models" / args.run_id / "model_registry.json"
    registry = read_json(path)
    failures = []
    for model in registry.get("models", []):
        if model.get("external_api_used") is not False:
            failures.append({"model_id": model.get("model_id"), "reason": "external_api_used must be false"})
        if model.get("third_party_solver_used") is not False:
            failures.append({"model_id": model.get("model_id"), "reason": "third_party_solver_used must be false"})
        if not model.get("checkpoint_path"):
            failures.append({"model_id": model.get("model_id"), "reason": "missing checkpoint"})
    report = {
        "run_id": args.run_id,
        "checked_at": utc_now(),
        "status": "PASS" if not failures else "FAIL",
        "model_count": len(registry.get("models", [])),
        "models": registry.get("models", []),
        "failures": failures,
    }
    out = DATASET_ROOT / "models" / args.run_id / "model_registry_report.json"
    write_json(out, report)
    print(json.dumps({"status": report["status"], "run_id": args.run_id, "model_registry": str(path), "model_count": report["model_count"], "report": str(out)}, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
