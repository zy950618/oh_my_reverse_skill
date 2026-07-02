#!/usr/bin/env python3
"""Validate that CAPTCHA solver runs used only image/instruction inputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
ALLOWED_SOURCES = {
    "challenge_screenshot",
    "challenge_image",
    "challenge_image_crop",
    "master_image",
    "thumb_image",
    "instruction_text",
    "allowed_actions_schema",
}
FORBIDDEN_FLAGS = {
    "label_read_for_prediction",
    "answer_read_for_prediction",
    "manifest_answer_read_for_prediction",
    "metadata_answer_read_for_prediction",
    "dom_read_for_prediction",
    "query_param_read_for_prediction",
    "server_expected_read_for_prediction",
    "action_replay_expected_read_for_prediction",
    "challenge_config_answer_read_for_prediction",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def audit_row(row: dict[str, Any], source: str) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    leakage = row.get("leakage_check") if isinstance(row.get("leakage_check"), dict) else row
    for flag in FORBIDDEN_FLAGS:
        if leakage.get(flag) not in {False, None}:
            failures.append({"source": source, "sample_id": row.get("sample_id"), "field": flag, "reason": "forbidden answer source used"})
    sources = set(leakage.get("solver_input_sources") or row.get("solver_input_sources") or [])
    unexpected = sorted(sources - ALLOWED_SOURCES)
    if unexpected:
        failures.append({"source": source, "sample_id": row.get("sample_id"), "field": "solver_input_sources", "reason": f"unexpected sources {unexpected}"})
    return failures


def update_evidence(run_id: str, status: str, report_path: Path) -> None:
    for path in (
        ROOT / "public-range-evidence" / "local-gocaptcha-compatible-lab" / f"{run_id}.json",
        ROOT / "public-range-evidence" / "gocaptcha-local" / f"{run_id}.json",
        ROOT / "public-range-evidence" / "gocaptcha-official" / f"{run_id}.json",
        ROOT / "public-range-evidence" / "opencaptchaworld" / f"{run_id}.json",
        ROOT / "public-range-evidence" / "shumei-compatible-lab" / f"{run_id}.json",
        ROOT / "public-range-evidence" / "aliyun-compatible-lab" / f"{run_id}.json",
        ROOT / "public-range-evidence" / "five-second-shield-lab" / f"{run_id}.json",
    ):
        if not path.is_file():
            continue
        payload = read_json(path)
        payload["blackbox_gate"] = {"status": status.lower(), "path": str(report_path)}
        action = payload.get("action_replay") if isinstance(payload.get("action_replay"), dict) else {}
        metrics = action.get("metrics") if isinstance(action.get("metrics"), dict) else {}
        records_path = metrics.get("records_path")
        if isinstance(records_path, str) and Path(records_path).is_file():
            rows = read_jsonl(Path(records_path))
            changed = False
            for row in rows:
                row["blackbox_gate"] = status.lower()
                changed = True
            if changed:
                Path(records_path).write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
        if status != "PASS" and payload.get("capability_status") in {"positive_candidate", "positive_verified", "stable_positive", "positive_allowed"}:
            payload["capability_status"] = "negative_eval_only"
            if isinstance(payload.get("decision"), dict):
                payload["decision"]["skills_participation"] = "negative_eval_only"
                payload["decision"]["positive_allowed"] = False
                payload["decision"]["blocked_reason"] = "blackbox solver gate failed; run invalid for positive capability"
        write_json(path, payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CAPTCHA image-only blackbox solver gate")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    run_id = args.run_id
    candidate_paths = [
        ROOT / "public-range-evidence" / "raw" / "local-gocaptcha-compatible-lab" / run_id / "gocaptcha-action-replay-records.jsonl",
        ROOT / "public-range-evidence" / "raw" / "gocaptcha-local" / run_id / "gocaptcha-action-replay-metrics.json",
        ROOT / "public-range-evidence" / "raw" / "gocaptcha-official" / run_id / "gocaptcha-official-action-replay-records.jsonl",
        ROOT / "public-range-evidence" / "raw" / "opencaptchaworld" / run_id / "opencaptchaworld-action-replay-records.jsonl",
        ROOT / "public-range-evidence" / "raw" / "shumei-compatible-lab" / run_id / "shumei-compatible-lab-action-replay-records.jsonl",
        ROOT / "public-range-evidence" / "raw" / "aliyun-compatible-lab" / run_id / "aliyun-compatible-lab-action-replay-records.jsonl",
        ROOT / "public-range-evidence" / "raw" / "five-second-shield-lab" / run_id / "five-second-shield-action-records.jsonl",
        ROOT / "public-range-evidence" / "raw" / "captcha-vision-lab" / run_id / "baseline-predictions.json",
        ROOT / "public-range-evidence" / "raw" / "captcha-vision-lab" / run_id / "trained-predictions.json",
    ]
    checked_rows = 0
    failures: list[dict[str, Any]] = []
    for path in candidate_paths:
        if not path.is_file():
            continue
        if path.suffix == ".jsonl":
            rows = read_jsonl(path)
        else:
            payload = read_json(path)
            metrics = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}
            if isinstance(metrics.get("challenges"), list):
                rows = metrics["challenges"]
            else:
                rows = payload.get("predictions") if isinstance(payload.get("predictions"), list) else [metrics or payload]
        checked_rows += len(rows)
        for row in rows:
            failures.extend(audit_row(row, str(path)))
    if checked_rows == 0:
        failures.append({"source": run_id, "reason": "no solver rows found for blackbox audit"})
    status = "PASS" if not failures else "INVALID"
    report = {
        "tool": "captcha_blackbox_solver_gate",
        "run_id": run_id,
        "status": status,
        "allowed_sources": sorted(ALLOWED_SOURCES),
        "forbidden_flags": sorted(FORBIDDEN_FLAGS),
        "checked_rows": checked_rows,
        "failures": failures,
        "decision": {
            "candidate_allowed": status == "PASS",
            "verified_allowed": status == "PASS",
            "stable_allowed": status == "PASS",
        },
    }
    out = ROOT / "public-range-evidence" / "raw" / "captcha-blackbox-gate" / run_id / "blackbox-gate.json"
    write_json(out, report)
    update_evidence(run_id, status, out)
    print(json.dumps({"status": status, "run_id": run_id, "report_path": str(out), "checked_rows": checked_rows, "failure_count": len(failures)}, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
