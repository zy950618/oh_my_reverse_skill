#!/usr/bin/env python3
"""Summarize fingerprint-derived risk state for localhost observation."""
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
    out = {"status": "PASS", "derived_risk": data.get("derived_risk", []), "block_reason": data.get("block_reason"), "allowed_action": data.get("allowed_action", []), "forbidden_action": data.get("forbidden_action", [])}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
