#!/usr/bin/env python3
"""Capture the localhost JS runtime fixture source and script id."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "public-range-labs" / "realistic-captcha-risk-lab" / "runtime-signature.js"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    raw = SCRIPT.read_bytes()
    out = REPO_ROOT / "public-range-evidence" / "raw" / "realistic-captcha-risk-lab" / args.run_id / "js-runtime-capture.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"run_id": args.run_id, "script_id": "runtime-signature-fnv1a-v1", "script_path": str(SCRIPT), "sha256": hashlib.sha256(raw).hexdigest()}, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "capture_path": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

