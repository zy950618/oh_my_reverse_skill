#!/usr/bin/env python3
"""Run repeated Airline Lab stress rounds with bytecode disabled."""
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
    ["public-range-evidence\\airline-lab-order-flow\\replay\\replay.py"],
    ["public-range-evidence\\airline-lab-order-flow\\tests\\run_order_flow_tests.py"],
    ["tools\\validate_pure_api_delivery.py", "public-range-evidence/airline-lab-order-flow"],
    ["public-range-evidence\\airline-lab-order-flow\\tests\\run_negative_case_checks.py"],
]


def run_command(repo_root: Path, args: list[str]) -> dict[str, Any]:
    command = [sys.executable, *args]
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    start = time.perf_counter()
    completed = subprocess.run(command, cwd=repo_root, env=env, capture_output=True, text=True, check=False)
    duration = round(time.perf_counter() - start, 3)
    return {
        "command": " ".join(args),
        "exit_code": completed.returncode,
        "duration_seconds": duration,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "stdout_tail": completed.stdout.strip().splitlines()[-20:],
        "stderr_tail": completed.stderr.strip().splitlines()[-20:],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--report", type=Path, default=Path(__file__).resolve().parents[1] / "repeat_reports" / "airline_repeat_stress_report.json")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    rounds: list[dict[str, Any]] = []
    for index in range(1, args.rounds + 1):
        command_results = [run_command(repo_root, command) for command in COMMANDS]
        rounds.append(
            {
                "round": index,
                "status": "PASS" if all(item["exit_code"] == 0 for item in command_results) else "FAIL",
                "commands": command_results,
            }
        )

    failed_rounds = [item for item in rounds if item["status"] != "PASS"]
    report = {
        "schema_version": "airline-lab-repeat-stress/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if not failed_rounds else "FAIL",
        "rounds_requested": args.rounds,
        "rounds_passed": args.rounds - len(failed_rounds),
        "rounds_failed": len(failed_rounds),
        "pythondontwritebytecode": "1",
        "live_site_calls_performed": False,
        "browser_dependency": False,
        "commands_per_round": [" ".join(command) for command in COMMANDS],
        "rounds": rounds,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "report": str(args.report), "rounds_passed": report["rounds_passed"], "rounds_failed": report["rounds_failed"]}, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
