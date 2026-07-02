#!/usr/bin/env python3
"""Summarize next active-learning targets from failure cases."""
from __future__ import annotations
import argparse, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    path = ROOT / "public-range-evidence" / "raw" / "captcha-vision-lab" / args.run_id / "failure-cases.json"
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    counts = {k: len(v) for k, v in data.get("failure_cases", {}).items()}
    print(json.dumps({"status": "PASS", "next_training_targets": counts, "recommendation": "prioritize text segmentation and slider hard distractor rejection"}, indent=2))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
