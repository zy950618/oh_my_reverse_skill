#!/usr/bin/env python3
"""Check JS signature regression fixture parity status."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    path = ROOT / "public-range-evidence" / "raw" / "realistic-captcha-risk-lab" / args.run_id / "runtime-parity-report.json"
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    ok = data.get("parity_status") == "pass" and data.get("repeat_parity_status") == "pass"
    print(json.dumps({"status": "PASS" if ok else "FAIL", "run_id": args.run_id, "parity_status": data.get("parity_status"), "repeat_parity_status": data.get("repeat_parity_status")}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

