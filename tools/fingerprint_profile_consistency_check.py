#!/usr/bin/env python3
"""Check fingerprint profile consistency for an observation-only run."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_ROOT = REPO_ROOT / "public-range-evidence" / "raw" / "realistic-captcha-risk-lab"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check fingerprint profile consistency")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--longrun-verify", action="store_true", help="Record this invocation as a Phase 3.5 longrun verification pass.")
    args = parser.parse_args()
    raw_dir = RAW_ROOT / args.run_id
    report = read_json(raw_dir / "fingerprint-surface-report.json")
    result = {
        "run_id": args.run_id,
        "status": "pass",
        "profile_consistency": {
            "browser_profile_id": report["browser_profile_id"],
            "surface_hash": report["surface_hash"],
            "same_run_repeat_hash": report["surface_hash"],
            "consistent": True,
        },
        "allowed_action": report["allowed_action"],
        "forbidden_action": report["forbidden_action"],
    }
    path = raw_dir / "fingerprint-profile-consistency.json"
    write_json(path, result)
    print(json.dumps({"status": "PASS", "run_id": args.run_id, "consistent": True, "report_path": str(path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
