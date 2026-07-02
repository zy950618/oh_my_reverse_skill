#!/usr/bin/env python3
"""Audit public range answer leakage and redaction enforcement."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
LEAK_KEYS = {
    "answer",
    "answers",
    "correct_answer",
    "correct_answer_info",
    "correct_option",
    "correct_option_index",
    "correct_patches",
    "correct_selections",
    "correct_angle",
    "expected",
    "solution",
    "solution_line",
    "sum",
    "target_index",
    "target_position",
    "hold_time",
}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            item = json.loads(line)
            if isinstance(item, dict):
                rows.append(item)
    return rows


def leaked_keys(payload: dict[str, Any]) -> list[str]:
    return sorted(key for key in payload if key in LEAK_KEYS or key.startswith("correct_"))


def update_evidence(run_id: str, status: str, report_path: Path) -> None:
    for target in ("opencaptchaworld", "gocaptcha-official", "shumei-compatible-lab", "aliyun-compatible-lab", "five-second-shield-lab"):
        path = ROOT / "public-range-evidence" / target / f"{run_id}.json"
        if not path.is_file():
            continue
        payload = read_json(path)
        payload["public_range_answer_leakage_audit"] = {"status": status.lower(), "path": str(report_path)}
        if status != "PASS" and payload.get("capability_status") in {"positive_candidate", "positive_verified", "stable_positive", "positive_allowed"}:
            payload["capability_status"] = "negative_eval_only"
            if isinstance(payload.get("decision"), dict):
                payload["decision"]["skills_participation"] = "negative_eval_only"
                payload["decision"]["positive_allowed"] = False
                payload["decision"]["blocked_reason"] = "public range answer leakage redaction failed"
        write_json(path, payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit public range answer leakage")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    run_id = args.run_id
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    checked_rows = 0
    leak_observations: list[dict[str, Any]] = []
    for target in ("opencaptchaworld", "gocaptcha-official", "shumei-compatible-lab", "aliyun-compatible-lab", "five-second-shield-lab"):
        raw_dir = ROOT / "public-range-evidence" / "raw" / target / run_id
        for records_path in list(raw_dir.glob("*action-replay-records.jsonl")) + list(raw_dir.glob("*action-records.jsonl")):
            for index, row in enumerate(read_jsonl(records_path)):
                checked_rows += 1
                public_fields = row.get("public_payload_answer_fields_present") or []
                if public_fields:
                    leak_observations.append({"target": target, "row": index, "fields": public_fields})
                solver_payload = row.get("solver_input_payload") if isinstance(row.get("solver_input_payload"), dict) else {}
                leaked = leaked_keys(solver_payload)
                if leaked:
                    failures.append({"target": target, "row": index, "reason": "solver input contains answer-shaped fields", "fields": leaked})
                audit = row.get("redaction_audit") if isinstance(row.get("redaction_audit"), dict) else {}
                if target == "opencaptchaworld":
                    if audit.get("status") != "pass":
                        failures.append({"target": target, "row": index, "reason": "missing or failed redaction_audit"})
                    if audit.get("solver_received_raw_api_json") is not False:
                        failures.append({"target": target, "row": index, "reason": "solver received raw API JSON"})
                elif public_fields:
                    warnings.append({"target": target, "row": index, "reason": "public answer fields observed on non-redacted target", "fields": public_fields})
    if checked_rows == 0:
        failures.append({"reason": "no public range action replay records found"})
    status = "PASS" if not failures else "INVALID"
    out = ROOT / "public-range-evidence" / "raw" / "public-range-answer-leakage-audit" / run_id / "public-range-answer-leakage-audit.json"
    report = {
        "tool": "public_range_answer_leakage_audit",
        "run_id": run_id,
        "status": status,
        "checked_rows": checked_rows,
        "leak_observation_count": len(leak_observations),
        "leak_observations": leak_observations[:120],
        "failures": failures,
        "warnings": warnings,
        "decision": {"run_invalid": bool(failures), "positive_allowed": False if failures else None},
    }
    write_json(out, report)
    update_evidence(run_id, status, out)
    print(json.dumps({"status": status, "run_id": run_id, "report_path": str(out), "checked_rows": checked_rows, "failure_count": len(failures)}, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
