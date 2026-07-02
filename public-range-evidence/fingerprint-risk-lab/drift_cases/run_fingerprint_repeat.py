#!/usr/bin/env python3
"""Run repeated local fingerprint validators and write a repeat evidence report."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


COMMANDS = [
    ["tools\\validate_fingerprint_surface_lab.py"],
    ["tools\\validate_block_reason_lab.py"],
    ["tools\\validate_browser_context_isolation.py"],
    ["tools\\validate_captcha_fingerprint_linkage.py"],
    ["public-range-evidence\\fingerprint-risk-lab\\drift_cases\\validate_drift_cases.py"],
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_command(root: Path, command: list[str]) -> dict[str, Any]:
    started = time.perf_counter()
    completed = subprocess.run(
        [sys.executable, *command],
        cwd=root,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        text=True,
        capture_output=True,
        check=False,
    )
    duration = round(time.perf_counter() - started, 3)
    return {
        "command": "python " + " ".join(command),
        "exit_code": completed.returncode,
        "duration_seconds": duration,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run repeated fingerprint lab validators")
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument(
        "--output",
        default="public-range-evidence/fingerprint-risk-lab/repeat_reports/fingerprint_repeat_rounds.json",
    )
    args = parser.parse_args()
    root = repo_root()
    rounds: list[dict[str, Any]] = []
    for round_number in range(1, args.rounds + 1):
        command_results = [run_command(root, command) for command in COMMANDS]
        rounds.append(
            {
                "round": round_number,
                "status": "PASS" if all(item["exit_code"] == 0 for item in command_results) else "FAIL",
                "commands": command_results,
            }
        )

    passed = sum(1 for item in rounds if item["status"] == "PASS")
    payload = {
        "schema_version": "fingerprint-repeat-report/v1",
        "status": "PASS" if passed == args.rounds else "FAIL",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "rounds_requested": args.rounds,
        "rounds_passed": passed,
        "rounds_failed": args.rounds - passed,
        "pythondontwritebytecode": "1",
        "commands_per_round": ["python " + " ".join(command) for command in COMMANDS],
        "rounds": rounds,
    }
    output_path = root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
