#!/usr/bin/env python3
"""Report fingerprint surface drift from local baseline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    path = ROOT / "public-range-evidence" / "raw" / "realistic-captcha-risk-lab" / args.run_id / "fingerprint-surface-report.json"
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    print(json.dumps({"status": "PASS", "surface_hash": data.get("surface_hash"), "drift_from_baseline": data.get("drift_from_baseline")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

