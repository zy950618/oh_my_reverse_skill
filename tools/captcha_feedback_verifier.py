#!/usr/bin/env python3
"""Verify CAPTCHA benchmark failure feedback exists for a run."""
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
    count = sum(len(v) for v in data.get("failure_cases", {}).values())
    print(json.dumps({"status": "PASS" if count >= 10 else "FAIL", "failure_count": count, "failure_cases_path": str(path)}, indent=2))
    return 0 if count >= 10 else 1
if __name__ == "__main__":
    raise SystemExit(main())

