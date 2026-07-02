#!/usr/bin/env python3
"""Redact answer-shaped public range fields before solver input."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
FORBIDDEN_KEYS = {
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
    "avoid_area",
    "hold_time",
}
ALLOWED_KEYS = {
    "challenge_instance_id",
    "puzzle_id",
    "puzzle_type",
    "family",
    "prompt",
    "instruction",
    "input_type",
    "image_path",
    "reference_image",
    "option_images",
    "component_image",
    "background_image",
    "grid_size",
    "current_option_index",
    "allowed_action_schema",
}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def forbidden_keys(payload: dict[str, Any]) -> list[str]:
    return sorted(key for key in payload if key in FORBIDDEN_KEYS or key.startswith("correct_"))


def redact_payload(payload: dict[str, Any], family: str) -> tuple[dict[str, Any], dict[str, Any]]:
    leaked = forbidden_keys(payload)
    sanitized = {
        "challenge_instance_id": payload.get("puzzle_id"),
        "puzzle_id": payload.get("puzzle_id"),
        "puzzle_type": payload.get("puzzle_type") or family,
        "family": family,
        "prompt": payload.get("prompt"),
        "instruction": payload.get("prompt"),
        "input_type": payload.get("input_type"),
        "image_path": payload.get("image_path"),
        "reference_image": payload.get("reference_image"),
        "option_images": payload.get("option_images"),
        "component_image": payload.get("component_image"),
        "background_image": payload.get("background_image"),
        "grid_size": payload.get("grid_size"),
        "current_option_index": payload.get("current_option_index", 0),
        "allowed_action_schema": allowed_action_schema(payload.get("input_type"), family),
    }
    sanitized = {key: value for key, value in sanitized.items() if key in ALLOWED_KEYS and value is not None}
    audit = {
        "status": "pass",
        "family": family,
        "redacted_keys": leaked,
        "solver_received_raw_api_json": False,
        "solver_input_keys": sorted(sanitized),
        "forbidden_keys_present_after_redaction": forbidden_keys(sanitized),
    }
    if audit["forbidden_keys_present_after_redaction"]:
        audit["status"] = "invalid"
    return sanitized, audit


def allowed_action_schema(input_type: Any, family: str) -> dict[str, Any]:
    if input_type in {"image_matching", "connect_icon", "dart_count", "object_match"} or family in {"Connect_icon", "Image_Matching", "Coordinates"}:
        return {"type": "select_option_index", "index_base": 0}
    if input_type == "hold_button" or family == "Hold_Button":
        return {"type": "hold_seconds", "min": 0}
    if input_type == "click":
        return {"type": "click_xy"}
    return {"type": str(input_type or "unknown")}


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit stored solver input redaction for a public range run")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--target", choices=["opencaptchaworld", "shumei-compatible-lab", "aliyun-compatible-lab", "five-second-shield-lab"])
    args = parser.parse_args()
    targets = [args.target] if args.target else ["opencaptchaworld", "shumei-compatible-lab", "aliyun-compatible-lab", "five-second-shield-lab"]
    rows: list[dict[str, Any]] = []
    record_paths: list[str] = []
    for target in targets:
        raw_dir = ROOT / "public-range-evidence" / "raw" / target / args.run_id
        for records_path in list(raw_dir.glob("*action-replay-records.jsonl")) + list(raw_dir.glob("*action-records.jsonl")):
            record_paths.append(str(records_path))
            rows.extend(read_jsonl(records_path))
    failures = []
    redacted_rows = 0
    for index, row in enumerate(rows):
        audit = row.get("redaction_audit") if isinstance(row.get("redaction_audit"), dict) else {}
        redacted_rows += 1 if audit.get("status") == "pass" else 0
        requires_audit = row.get("target") == "opencaptchaworld" or bool(audit)
        if requires_audit and audit.get("solver_received_raw_api_json") is not False:
            failures.append({"row": index, "reason": "solver_received_raw_api_json must be false"})
        if requires_audit and audit.get("forbidden_keys_present_after_redaction"):
            failures.append({"row": index, "reason": "forbidden keys present after redaction", "keys": audit.get("forbidden_keys_present_after_redaction")})
        payload = row.get("solver_input_payload") if isinstance(row.get("solver_input_payload"), dict) else {}
        leaked = forbidden_keys(payload)
        if leaked:
            failures.append({"row": index, "reason": "solver input payload contains leaked answer fields", "keys": leaked})
    status = "PASS" if rows and not failures else "INVALID"
    report = {
        "tool": "solver_input_redactor",
        "run_id": args.run_id,
        "target": args.target or "all",
        "status": status,
        "records_path": record_paths,
        "checked_rows": len(rows),
        "redacted_rows": redacted_rows,
        "forbidden_keys": sorted(FORBIDDEN_KEYS),
        "allowed_keys": sorted(ALLOWED_KEYS),
        "failures": failures,
    }
    out = ROOT / "public-range-evidence" / "raw" / "solver-input-redaction-audit" / args.run_id / "solver-input-redaction-audit.json"
    write_json(out, report)
    print(json.dumps({"status": status, "run_id": args.run_id, "target": args.target, "report_path": str(out), "failure_count": len(failures)}, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
