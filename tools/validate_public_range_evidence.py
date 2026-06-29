#!/usr/bin/env python3
"""Validate sanitized public range evidence.

This gate is intentionally stricter for positive skill growth than for
negative/boundary evidence. A public target can teach a failure mode without
being allowed to improve positive skill scores.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PARTICIPATION = {"positive_allowed", "negative_eval_only", "memory_only", "prohibited"}


def parse_dt(raw: object) -> datetime | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    value = raw.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def is_pass(section: object) -> bool:
    return isinstance(section, dict) and str(section.get("status", "")).lower() == "pass"


def is_2xx(value: object) -> bool:
    return isinstance(value, int) and 200 <= value < 300


def non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def non_empty_pointers(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, str) and item.startswith("/") for item in value
    )


def direct_interface_call_passes(backend: object) -> bool:
    if not isinstance(backend, dict):
        return False
    direct = backend.get("direct_interface_call")
    if not isinstance(direct, dict):
        return False
    if not is_pass(direct):
        return False
    if direct.get("browser_dependency") is not False:
        return False
    if not is_2xx(direct.get("observed_status")):
        return False
    if not non_empty_pointers(direct.get("json_pointers")):
        return False
    return True


def hard_gate_errors(payload: dict[str, Any], max_age_days: int) -> list[str]:
    errors: list[str] = []
    captured_at = parse_dt(payload.get("captured_at"))
    now = datetime.now(timezone.utc)
    backend = payload.get("backend_acceptance")
    ui = payload.get("ui_api_parity")

    if payload.get("source_freshness") != "fresh":
        errors.append("source_freshness must be fresh")
    if captured_at is None:
        errors.append("captured_at must be a valid ISO datetime")
    elif captured_at < now - timedelta(days=max_age_days):
        errors.append(f"captured_at is older than {max_age_days} days")
    if not is_pass(backend):
        errors.append("backend_acceptance.status must be pass")
    if isinstance(backend, dict):
        if not is_2xx(backend.get("observed_status")):
            errors.append("backend_acceptance.observed_status must be 2xx")
        if not non_empty_string(backend.get("endpoint")):
            errors.append("backend_acceptance.endpoint is required")
        if not non_empty_pointers(backend.get("json_pointers")):
            errors.append("backend_acceptance.json_pointers must be non-empty JSON Pointers")
        if not direct_interface_call_passes(backend):
            errors.append(
                "backend_acceptance.direct_interface_call must pass without browser dependency"
            )
    if not is_pass(ui):
        errors.append("ui_api_parity.status must be pass")
    if payload.get("repeat_verified") is not True:
        errors.append("repeat_verified must be true")
    repeat_attempts = payload.get("repeat_attempts")
    if not isinstance(repeat_attempts, list) or len(repeat_attempts) < 2:
        errors.append("repeat_attempts must contain clean and repeat evidence")
    return errors


def validate_file(path: Path, max_age_days: int) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {
            "path": str(path),
            "status": "FAIL",
            "skills_participation": None,
            "positive": False,
            "failures": [f"cannot parse JSON: {exc!r}"],
            "warnings": [],
        }

    decision = payload.get("decision")
    if not isinstance(decision, dict):
        failures.append("decision object is required")
        decision = {}

    participation = decision.get("skills_participation")
    if participation not in PARTICIPATION:
        failures.append(f"decision.skills_participation must be one of {sorted(PARTICIPATION)}")

    if payload.get("schema_version") != "public-range-evidence/v1":
        failures.append("schema_version must be public-range-evidence/v1")
    if not isinstance(payload.get("target"), dict) or not non_empty_string(payload["target"].get("url")):
        failures.append("target.url is required")
    if not isinstance(payload.get("skills"), list) or not payload["skills"]:
        failures.append("skills must name at least one participating skill")

    positive = participation == "positive_allowed"
    if positive:
        if decision.get("positive_allowed") is not True:
            failures.append("positive_allowed participation requires decision.positive_allowed=true")
        failures.extend(hard_gate_errors(payload, max_age_days=max_age_days))
    elif participation in {"negative_eval_only", "memory_only", "prohibited"}:
        if decision.get("positive_allowed") is True:
            failures.append(f"{participation} evidence cannot set positive_allowed=true")
        blocked_reason = decision.get("blocked_reason")
        if participation == "negative_eval_only" and not non_empty_string(blocked_reason):
            failures.append("negative_eval_only evidence requires decision.blocked_reason")
        if not payload.get("backend_acceptance") and not payload.get("ui_api_parity"):
            failures.append("boundary evidence still needs backend_acceptance or ui_api_parity observation")
        if payload.get("repeat_verified") is not True:
            warnings.append("repeat verification is not complete; correctly blocked from positive scoring")

    status = "PASS" if not failures else "FAIL"
    return {
        "path": str(path),
        "status": status,
        "skills_participation": participation,
        "positive": positive and status == "PASS",
        "failures": failures,
        "warnings": warnings,
    }


def evidence_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(
        path for path in root.rglob("*.json")
        if "raw" not in {part.lower() for part in path.parts}
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate public range evidence hard gates")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--evidence-root", default="public-range-evidence")
    parser.add_argument("--max-age-days", type=int, default=30)
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    root = repo_root / args.evidence_root
    files = evidence_files(root)
    results = [validate_file(path, args.max_age_days) for path in files]
    failures = [item for item in results if item["status"] != "PASS"]
    positive_count = sum(1 for item in results if item.get("positive"))

    global_failures: list[str] = []
    if not files:
        global_failures.append(f"no public range evidence files under {root}")
    if positive_count == 0:
        global_failures.append("no positive_allowed public range evidence passed hard gates")

    payload = {
        "tool": "validate_public_range_evidence",
        "status": "PASS" if not failures and not global_failures else "FAIL",
        "evidence_root": str(root),
        "total_files": len(files),
        "positive_allowed_count": positive_count,
        "negative_eval_count": sum(1 for item in results if item.get("skills_participation") == "negative_eval_only"),
        "global_failures": global_failures,
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
