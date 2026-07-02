#!/usr/bin/env python3
"""Validate business data assertions embedded in public-range evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
INTERNAL_ARTIFACT_PARTS = {
    "_archive",
    "fixtures",
    "replay",
    "reports",
    "manifests",
    "samples",
    "model",
    "inference",
    "eval",
    "mock_server",
    "fastapi_adapter",
    "sdk_examples",
    "tests",
}
DEDICATED_LAB_ROOTS = {
    "airline-lab-order-flow",
    "captcha-model-lab",
    "fingerprint-risk-lab",
    "pure-api-lab",
    "real-site-observation-pack",
}


RESULTS = {"BUSINESS_DATA_PASS", "BUSINESS_DATA_FAIL", "NOT_RUN", "INVALID"}
WORKERS = ("worker_1", "worker_2", "worker_5", "worker_10")
NON_BUSINESS_POSITIVE_SCOPES = {
    "local_open_source_range_positive",
    "local_compatible_lab_candidate",
    "local_compatible_lab_verified",
    "local_compatible_lab_stable",
    "local_vendor_compatible_positive_candidate",
    "public_range_solver_positive",
    "local_runtime_parity_positive",
    "local_fingerprint_diagnostics_positive",
    "public_fingerprint_diagnostics_positive",
}


def evidence_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(
        path for path in root.rglob("*.json")
        if not {"raw", "longrun"} & {part.lower() for part in path.parts}
        and path.relative_to(root).parts[0].lower() not in DEDICATED_LAB_ROOTS
        and not INTERNAL_ARTIFACT_PARTS & {part.lower() for part in path.relative_to(root).parts[:-1]}
    )


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def is_positive(payload: dict[str, Any]) -> bool:
    positive_statuses = {"positive_allowed", "positive_candidate", "positive_verified", "stable_positive"}
    return payload.get("capability_status") in positive_statuses or (
        isinstance(payload.get("decision"), dict)
        and payload["decision"].get("skills_participation") in positive_statuses
    )


def positive_scope(payload: dict[str, Any]) -> str:
    scope = payload.get("scope_decision")
    if isinstance(scope, dict):
        value = scope.get("positive_allowed_scope")
        if isinstance(value, str):
            return value
    detail = payload.get("capability_status_detail")
    if isinstance(detail, dict):
        value = detail.get("scope_limited_positive")
        if isinstance(value, str):
            return value
    return ""


def requires_business_data(payload: dict[str, Any]) -> bool:
    if not is_positive(payload):
        return False
    return positive_scope(payload) not in NON_BUSINESS_POSITIVE_SCOPES


def resolve_path(raw: object, evidence_path: Path) -> Path | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    path = Path(raw)
    if path.is_file():
        return path
    if not path.is_absolute():
        candidate = (evidence_path.parent / path).resolve()
        if candidate.is_file():
            return candidate
        return candidate

    normalized = raw.replace("\\", "/")
    marker = "public-range-evidence/"
    marker_index = normalized.find(marker)
    if marker_index == -1:
        return path

    relative = Path(*normalized[marker_index:].split("/"))
    current = REPO_ROOT / relative
    if current.is_file():
        return current

    archive_root = REPO_ROOT / "public-range-evidence" / "_archive"
    if archive_root.is_dir():
        relative_suffix = "/".join(relative.parts)
        for candidate in archive_root.rglob(path.name):
            candidate_normalized = str(candidate).replace("\\", "/")
            if candidate_normalized.endswith(relative_suffix):
                return candidate
    return current


def validate_assertions(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    positive = is_positive(payload)
    business_required = requires_business_data(payload)
    bda = payload.get("business_data_assertions")
    top_status = payload.get("business_data_status")
    if not isinstance(bda, dict):
        return {
            "path": str(path),
            "status": "BUSINESS_DATA_FAIL" if business_required else "NOT_RUN",
            "positive": positive,
            "business_required": business_required,
            "business_data_status": top_status or "NOT_RUN",
            "failures": ["positive_allowed business evidence requires business_data_assertions"] if business_required else [],
            "warnings": [] if business_required else ["business_data_assertions not required for this scope"],
        }

    failures: list[str] = []
    warnings: list[str] = []
    ledger_path = resolve_path(bda.get("server_ledger_path"), path)
    ledger: dict[str, Any] = {}
    if ledger_path is None or not ledger_path.is_file():
        failures.append("business_data_assertions.server_ledger_path must exist")
    else:
        try:
            loaded = read_json(ledger_path)
            if isinstance(loaded, dict):
                ledger = loaded
            else:
                failures.append("server ledger JSON must be object")
        except Exception as exc:
            failures.append(f"cannot parse server ledger: {exc!r}")

    positive_assertions = bda.get("positive_assertions")
    if not isinstance(positive_assertions, list) or not positive_assertions:
        failures.append("positive_assertions must be non-empty")
    else:
        for index, item in enumerate(positive_assertions):
            if not isinstance(item, dict) or item.get("status") != "pass":
                failures.append(f"positive_assertions[{index}].status must be pass")

    negative_assertions = bda.get("negative_assertions")
    if not isinstance(negative_assertions, list) or not negative_assertions:
        failures.append("negative_assertions must be non-empty")
    else:
        for index, item in enumerate(negative_assertions):
            if not isinstance(item, dict):
                failures.append(f"negative_assertions[{index}] must be object")
                continue
            if item.get("status") != "pass":
                failures.append(f"negative_assertions[{index}].status must be pass")
            if item.get("expected_ledger_delta") != 0 or item.get("actual_ledger_delta") != 0:
                failures.append(f"negative_assertions[{index}] must prove ledger_delta=0")

    concurrency = bda.get("concurrency_assertions")
    if not isinstance(concurrency, dict):
        failures.append("concurrency_assertions must be object")
    else:
        for worker in WORKERS:
            item = concurrency.get(worker)
            if not isinstance(item, dict):
                failures.append(f"concurrency_assertions.{worker} is required")
                continue
            if item.get("status") != "pass":
                failures.append(f"concurrency_assertions.{worker}.status must be pass")
            if item.get("expected_success_count") != item.get("actual_success_count"):
                failures.append(f"concurrency_assertions.{worker} success count mismatch")
            if item.get("expected_ledger_delta") != item.get("actual_ledger_delta"):
                failures.append(f"concurrency_assertions.{worker} ledger delta mismatch")
            for key in (
                "duplicate_order_count",
                "cross_worker_pollution_count",
                "wrong_owner_count",
                "orphan_order_count",
            ):
                if item.get(key) != 0:
                    failures.append(f"concurrency_assertions.{worker}.{key} must be 0")

    orders = ledger.get("orders") if isinstance(ledger, dict) else None
    if isinstance(orders, list):
        order_ids = [item.get("order_id") for item in orders if isinstance(item, dict)]
        if len(order_ids) != len(set(order_ids)):
            failures.append("server ledger order_id values must be unique")
        for index, order in enumerate(orders):
            if not isinstance(order, dict):
                failures.append(f"server ledger orders[{index}] must be object")
                continue
            if not order.get("order_id"):
                failures.append(f"server ledger orders[{index}] missing order_id")
            if not order.get("session_id"):
                failures.append(f"server ledger orders[{index}] missing session_id")
            if order.get("endpoint") == "POST /api/concurrency/business" and not order.get("worker_id"):
                failures.append(f"concurrency order {order.get('order_id')} missing worker_id")
    elif ledger:
        failures.append("server ledger must include orders list")

    final = bda.get("final_decision")
    if not isinstance(final, dict) or final.get("data_assertion_pass") is not True:
        failures.append("final_decision.data_assertion_pass must be true")

    if top_status and top_status != ("DATA_ASSERTION_PASS" if not failures else "DATA_ASSERTION_FAIL"):
        failures.append("top-level business_data_status does not match assertion result")

    status = "BUSINESS_DATA_PASS" if not failures else "BUSINESS_DATA_FAIL"
    return {
        "path": str(path),
        "status": status,
        "positive": positive,
        "business_required": business_required,
        "business_data_status": top_status or status,
        "server_ledger_path": str(ledger_path) if ledger_path else "",
        "positive_assertion_count": len(positive_assertions) if isinstance(positive_assertions, list) else 0,
        "negative_assertion_count": len(negative_assertions) if isinstance(negative_assertions, list) else 0,
        "failures": failures,
        "warnings": warnings,
    }


def validate_file(path: Path) -> dict[str, Any]:
    try:
        payload = read_json(path)
    except Exception as exc:
        return {
            "path": str(path),
            "status": "INVALID",
            "positive": False,
            "business_data_status": "INVALID",
            "failures": [f"cannot parse JSON: {exc!r}"],
            "warnings": [],
        }
    if not isinstance(payload, dict):
        return {
            "path": str(path),
            "status": "INVALID",
            "positive": False,
            "business_data_status": "INVALID",
            "failures": ["JSON payload must be object"],
            "warnings": [],
        }
    return validate_assertions(path, payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate business data assertions in public-range evidence")
    parser.add_argument("evidence_root_arg", nargs="?")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--evidence-root", default="public-range-evidence")
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    root = repo_root / (args.evidence_root_arg or args.evidence_root)
    results = [validate_file(path) for path in evidence_files(root)]
    invalid_or_fail = [item for item in results if item["status"] in {"INVALID", "BUSINESS_DATA_FAIL"}]
    positive_without_pass = [
        item for item in results
        if item.get("positive") and item.get("business_required") and item.get("status") != "BUSINESS_DATA_PASS"
    ]
    payload = {
        "tool": "validate_business_data_assertions",
        "status": "PASS" if not invalid_or_fail and not positive_without_pass else "FAIL",
        "evidence_root": str(root),
        "total_files": len(results),
        "business_data_pass_count": sum(1 for item in results if item["status"] == "BUSINESS_DATA_PASS"),
        "business_data_fail_count": sum(1 for item in results if item["status"] == "BUSINESS_DATA_FAIL"),
        "not_run_count": sum(1 for item in results if item["status"] == "NOT_RUN"),
        "invalid_count": sum(1 for item in results if item["status"] == "INVALID"),
        "positive_without_business_data_pass": positive_without_pass,
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
