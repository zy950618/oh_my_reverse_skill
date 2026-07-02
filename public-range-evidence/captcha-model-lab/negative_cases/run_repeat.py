#!/usr/bin/env python3
"""Run the CAPTCHA repeat and negative-case command set for 10 rounds."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
REPORT_DIR = ROOT / "repeat_reports"
COMMANDS = [
    ("inference", "python public-range-evidence\\captcha-model-lab\\inference\\sample_infer.py", [sys.executable, "public-range-evidence/captcha-model-lab/inference/sample_infer.py"]),
    ("pass_rate", "python public-range-evidence\\captcha-model-lab\\eval\\evaluate_pass_rate.py", [sys.executable, "public-range-evidence/captcha-model-lab/eval/evaluate_pass_rate.py"]),
    ("action_schema", "python tools\\validate_captcha_action_schema.py", [sys.executable, "tools/validate_captcha_action_schema.py"]),
    ("dataset", "python tools\\validate_captcha_dataset.py", [sys.executable, "tools/validate_captcha_dataset.py"]),
    ("training_report", "python tools\\validate_captcha_training_report.py", [sys.executable, "tools/validate_captcha_training_report.py"]),
    ("model_package", "python tools\\validate_captcha_model_package.py", [sys.executable, "tools/validate_captcha_model_package.py"]),
    ("pass_rate_manifest", "python tools\\validate_captcha_pass_rate.py", [sys.executable, "tools/validate_captcha_pass_rate.py"]),
    ("negative_cases", "python public-range-evidence\\captcha-model-lab\\negative_cases\\validate_negative_cases.py", [sys.executable, "public-range-evidence/captcha-model-lab/negative_cases/validate_negative_cases.py"]),
]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def run_command(command: list[str]) -> dict:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=REPO, env=env, text=True, capture_output=True)
    duration = time.perf_counter() - started
    return {
        "exit_code": completed.returncode,
        "duration_seconds": round(duration, 3),
        "stdout_tail": completed.stdout.strip()[-1200:],
        "stderr_tail": completed.stderr.strip()[-1200:],
        "status": "PASS" if completed.returncode == 0 else "FAIL",
    }


def round_summary(round_index: int, commands: list[dict]) -> dict:
    predictions = read_json(ROOT / "inference" / "sample_predictions.json")
    metrics = read_json(ROOT / "eval" / "metrics.json")
    negative = commands[-1]
    return {
        "round": round_index,
        "status": "PASS" if all(item["status"] == "PASS" for item in commands) else "FAIL",
        "prediction_count": len(predictions.get("predictions", [])),
        "prediction_statuses": sorted({item.get("prediction_status") for item in predictions.get("predictions", [])}),
        "passes": metrics.get("passes"),
        "attempts": metrics.get("attempts"),
        "pass_rate": metrics.get("pass_rate"),
        "negative_validator_status": negative["status"],
        "commands": commands,
    }


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    rounds = []
    for round_index in range(1, 11):
        command_results = []
        for name, display, command in COMMANDS:
            result = run_command(command)
            result["name"] = name
            result["command"] = display
            command_results.append(result)
        summary = round_summary(round_index, command_results)
        rounds.append(summary)
        (REPORT_DIR / f"round-{round_index:02d}.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    report = {
        "manifest_type": "captcha_repeat_report",
        "schema_version": "0.1.0",
        "rounds": rounds,
        "round_count": len(rounds),
        "passed_rounds": sum(1 for item in rounds if item["status"] == "PASS"),
        "failed_rounds": sum(1 for item in rounds if item["status"] != "PASS"),
        "pass_rates": [item["pass_rate"] for item in rounds],
        "prediction_counts": [item["prediction_count"] for item in rounds],
        "negative_validator_passed_rounds": sum(1 for item in rounds if item["negative_validator_status"] == "PASS"),
        "pythondontwritebytecode": "1",
        "status": "PASS" if all(item["status"] == "PASS" for item in rounds) else "FAIL",
    }
    output = REPORT_DIR / "captcha_repeat_rounds.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(output), "passed_rounds": report["passed_rounds"], "round_count": report["round_count"]}, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
