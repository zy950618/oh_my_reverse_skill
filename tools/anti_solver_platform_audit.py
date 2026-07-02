#!/usr/bin/env python3
"""Audit that a run did not use third-party CAPTCHA solving platforms."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from captcha_flywheel_common import DATASET_ROOT, PUBLIC_ROOT, ROOT, write_json, utc_now


PLATFORM_PATTERNS = [
    "2" + "captcha",
    "anti" + "captcha",
    "captcha" + ".guru",
    "remote_solver_api",
    "paid_human_solver_service",
    "provider_internal_token",
    "copied_browser_token",
    "copied_clearance_cookie",
]


def candidate_files(run_id: str) -> list[Path]:
    files: list[Path] = []
    for base in (
        DATASET_ROOT / "manifests" / run_id,
        DATASET_ROOT / "labels" / run_id,
        DATASET_ROOT / "models" / run_id,
        DATASET_ROOT / "predictions" / run_id,
        DATASET_ROOT / "failures" / run_id,
        PUBLIC_ROOT,
    ):
        if base.is_file():
            files.append(base)
        elif base.is_dir():
            files.extend(path for path in base.rglob("*") if path.suffix.lower() in {".json", ".jsonl", ".yaml", ".yml", ".py"})
    files.extend([
        ROOT / "tools" / "real_public_range_runner.py",
        ROOT / "tools" / "captcha_model_trainer.py",
        ROOT / "tools" / "captcha_failure_collector.py",
    ])
    return sorted(set(path for path in files if path.is_file()))


def scan_file(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    hits = []
    lower = text.lower()
    for pattern in PLATFORM_PATTERNS:
        if pattern.lower() in lower:
            hits.append({"path": str(path), "pattern": pattern, "reason": "forbidden solver platform/source marker"})
    if re.search(r"https?://[^\\s\"']+/(?:solve|captcha|in\\.php|res\\.php)", text, flags=re.I) and "public-range" not in str(path).lower():
        hits.append({"path": str(path), "pattern": "external_solver_like_upload", "reason": "possible base64 upload to unknown external solver"})
    return hits


def inspect_solver_source(path: Path) -> list[dict[str, Any]]:
    violations = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return violations
    stack = [payload]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            if item.get("third_party_solver_used") is True:
                violations.append({"path": str(path), "reason": "third_party_solver_used=true"})
            if item.get("external_api_used") is True and item.get("type") in {"remote_solver_api", "third_party_captcha_solving_platform"}:
                violations.append({"path": str(path), "reason": "external solver source used"})
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit anti solver platform policy")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    violations = []
    checked = 0
    for path in candidate_files(args.run_id):
        if path.name == "anti_solver_platform_audit.py":
            continue
        checked += 1
        if path.suffix.lower() == ".json":
            violations.extend(inspect_solver_source(path))
        else:
            violations.extend(scan_file(path))
    status = "PASS" if not violations else "INVALID"
    report = {
        "tool": "anti_solver_platform_audit",
        "run_id": args.run_id,
        "checked_at": utc_now(),
        "status": status,
        "checked_file_count": checked,
        "violations": violations,
        "capability_status": "prohibited" if violations else "audit_pass",
        "decision": "run cannot promote" if violations else "no third-party solver platform detected",
    }
    out = PUBLIC_ROOT / "raw" / "anti-solver-platform-audit" / args.run_id / "anti-solver-platform-audit.json"
    write_json(out, report)
    print(json.dumps({"status": status, "run_id": args.run_id, "report_path": str(out), "violation_count": len(violations)}, ensure_ascii=False, indent=2))
    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
