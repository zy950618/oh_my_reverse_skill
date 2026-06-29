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


def interface_call_errors(call: object, label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(call, dict):
        return [f"{label} is required"]
    if not is_pass(call):
        errors.append(f"{label}.status must be pass")
    if call.get("browser_dependency") is not False:
        errors.append(f"{label}.browser_dependency must be false")
    for key in ("uses_browser_profile", "uses_live_storage", "uses_manual_cookie_or_token"):
        if call.get(key) is not False:
            errors.append(f"{label}.{key} must be false")
    if not is_2xx(call.get("observed_status")):
        errors.append(f"{label}.observed_status must be 2xx")
    content_type = str(call.get("content_type", "")).lower()
    json_type = str(call.get("json_type", "")).lower()
    if "json" not in content_type and json_type not in {"dict", "list"}:
        errors.append(f"{label} must return JSON business data")
    if not non_empty_pointers(call.get("json_pointers")):
        errors.append(f"{label}.json_pointers must be non-empty JSON Pointers")
    return errors


def sign_or_token_errors(payload: dict[str, Any]) -> list[str]:
    sign = payload.get("sign_or_token")
    if not isinstance(sign, dict) or sign.get("required") is not True:
        return []
    errors: list[str] = []
    mode = sign.get("generation_mode")
    if mode not in {"v8_env", "js_runtime", "node_vm", "wasm_crypto", "native_crypto", "adapter"}:
        errors.append("sign_or_token.generation_mode must be non-browser reproducible")
    if sign.get("browser_captured_replay") is not False:
        errors.append("sign_or_token.browser_captured_replay must be false")
    if not is_pass(sign.get("validation")):
        errors.append("sign_or_token.validation.status must be pass")
    return errors


def concurrency_errors(payload: dict[str, Any]) -> list[str]:
    decision = payload.get("decision")
    if not isinstance(decision, dict) or decision.get("concurrency_positive") is not True:
        return []
    ladder = payload.get("concurrency_ladder")
    if not isinstance(ladder, dict):
        return ["concurrency_ladder is required when concurrency_positive=true"]
    errors: list[str] = []
    for worker in ("worker_1", "worker_2", "worker_5", "worker_10"):
        item = ladder.get(worker)
        if not isinstance(item, dict) or item.get("status") != "pass":
            errors.append(f"concurrency_ladder.{worker}.status must be pass")
            continue
        if item.get("session_cache_token_isolated") is not True:
            errors.append(f"concurrency_ladder.{worker}.session_cache_token_isolated must be true")
        if item.get("backend_acceptance") is not True:
            errors.append(f"concurrency_ladder.{worker}.backend_acceptance must be true")
        if "failure_rate" not in item:
            errors.append(f"concurrency_ladder.{worker}.failure_rate is required")
        if not non_empty_string(item.get("stop_condition")):
            errors.append(f"concurrency_ladder.{worker}.stop_condition is required")
    return errors


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
        if backend.get("final_api_endpoint_confirmed") is not True:
            errors.append("backend_acceptance.final_api_endpoint_confirmed must be true")
        if not is_2xx(backend.get("observed_status")):
            errors.append("backend_acceptance.observed_status must be 2xx")
        if not non_empty_string(backend.get("endpoint")):
            errors.append("backend_acceptance.endpoint is required")
        if not non_empty_pointers(backend.get("json_pointers")):
            errors.append("backend_acceptance.json_pointers must be non-empty JSON Pointers")
        errors.extend(interface_call_errors(backend.get("direct_interface_call"), "backend_acceptance.direct_interface_call"))
        errors.extend(interface_call_errors(backend.get("repeat_direct_interface_call"), "backend_acceptance.repeat_direct_interface_call"))
    if ui is not None and not is_pass(ui):
        errors.append("ui_api_parity.status must be pass when UI parity is claimed")
    errors.extend(sign_or_token_errors(payload))
    errors.extend(concurrency_errors(payload))
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
