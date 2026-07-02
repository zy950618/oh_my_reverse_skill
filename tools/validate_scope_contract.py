#!/usr/bin/env python3
"""Validate range scope contracts and evidence scope decisions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
POSITIVE_PARTICIPATION = {"positive_allowed", "positive_candidate", "positive_verified", "stable_positive"}
LOCAL_POSITIVE_SCOPES = {
    "local_lab_positive",
    "local_lab_positive_verified",
    "local_runtime_parity_positive",
    "local_fingerprint_diagnostics_positive",
    "local_concurrency_business_positive",
    "local_open_source_range_positive",
    "local_compatible_lab_candidate",
    "local_compatible_lab_verified",
    "local_compatible_lab_stable",
    "local_vendor_compatible_positive_candidate",
    "local_waf_lab_positive_candidate",
    "local_waf_lab_positive_verified",
}
PUBLIC_POSITIVE_SCOPES = {
    "public_range_solver_positive",
    "public_fingerprint_diagnostics_positive",
}
AUTHORIZED_POSITIVE_SCOPES = {
    "authorized_target_positive",
    "authorized_concurrency_positive",
}
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


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception as exc:
        raise SystemExit(f"PyYAML is required: {exc}")
    data = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def contract_targets(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("id")): item for item in config.get("targets", []) if isinstance(item, dict)}


def host_matches(host: str, allowed: list[Any]) -> bool:
    if not allowed:
        return False
    host = host.lower()
    return host in {str(item).lower() for item in allowed}


def evidence_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(
        path for path in root.rglob("*.json")
        if not {"raw", "longrun"} & {part.lower() for part in path.parts}
        and path.relative_to(root).parts[0].lower() not in DEDICATED_LAB_ROOTS
        and not INTERNAL_ARTIFACT_PARTS & {part.lower() for part in path.relative_to(root).parts[:-1]}
    )


def scope_from_payload(payload: dict[str, Any]) -> str:
    decision = payload.get("scope_decision")
    if isinstance(decision, dict):
        return str(decision.get("positive_allowed_scope") or "")
    detail = payload.get("capability_status_detail")
    if isinstance(detail, dict):
        return str(detail.get("scope_limited_positive") or "")
    return ""


def participation(payload: dict[str, Any]) -> str:
    decision = payload.get("decision")
    return str(decision.get("skills_participation") if isinstance(decision, dict) else payload.get("capability_status", ""))


def validate_payload(path: Path, payload: dict[str, Any], targets: dict[str, dict[str, Any]], config_path: Path) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    if not isinstance(payload, dict):
        return {
            "path": str(path),
            "target_id": "",
            "status": "FAIL",
            "in_scope": False,
            "scope_type": None,
            "positive_allowed_scope": "",
            "failures": ["evidence JSON root must be an object"],
            "warnings": warnings,
        }
    target = payload.get("target") if isinstance(payload.get("target"), dict) else {}
    target_id = str(target.get("id") or payload.get("target_id") or "")
    target_contract = targets.get(target_id)
    url = str(target.get("url") or "")
    host = urlparse(url).hostname or str(target.get("host") or "")
    scope_decision = payload.get("scope_decision") if isinstance(payload.get("scope_decision"), dict) else None
    cap_detail = payload.get("capability_status_detail") if isinstance(payload.get("capability_status_detail"), dict) else None
    positive = participation(payload) in POSITIVE_PARTICIPATION or payload.get("capability_status") == "positive_allowed"

    if not target_contract:
        if positive:
            failures.append("positive evidence target must exist in scope contract")
        return {
            "path": str(path),
            "target_id": target_id,
            "status": "FAIL" if failures else "PASS",
            "in_scope": False,
            "scope_type": None,
            "positive_allowed_scope": "",
            "failures": failures,
            "warnings": warnings + ["target not in scope contract; automated challenge handling is not allowed"],
        }

    allowed_mode = ""
    if scope_decision:
        allowed_mode = str(scope_decision.get("allowed_mode") or "")
    elif isinstance(payload.get("action_replay"), dict):
        allowed_mode = "action_replay"
    elif target_id == "fingerprint-diagnostics":
        allowed_mode = "fingerprint_diagnostics"
    elif target_id == "realistic-captcha-risk-lab":
        allowed_mode = "js_runtime_parity"
    allowed_modes = [str(item) for item in target_contract.get("allowed_modes", [])]
    allowed_scopes = [str(item) for item in target_contract.get("positive_allowed_scope", [])]
    host_ok = host_matches(host, target_contract.get("allowed_hosts", [])) or target_contract.get("scope_type") == "authorized_target"
    mode_ok = not allowed_mode or allowed_mode in allowed_modes
    positive_scope = scope_from_payload(payload)
    positive_scope_ok = not positive or positive_scope in allowed_scopes

    if not host_ok:
        failures.append(f"host {host!r} is not in allowed_hosts for {target_id}")
    if not mode_ok:
        failures.append(f"allowed_mode {allowed_mode!r} is not allowed for {target_id}")
    if positive and not scope_decision:
        failures.append("positive_allowed evidence requires scope_decision")
    if positive and not cap_detail:
        failures.append("positive_allowed evidence requires capability_status_detail")
    if positive and not positive_scope_ok:
        failures.append(f"positive_allowed_scope {positive_scope!r} is not allowed for {target_id}")
    if positive:
        if scope_decision and scope_decision.get("external_generalization_allowed") is not False:
            failures.append("scope_decision.external_generalization_allowed must be false")
        if cap_detail and cap_detail.get("not_generalizable_to_third_party") is not True:
            failures.append("capability_status_detail.not_generalizable_to_third_party must be true")
        if positive_scope in LOCAL_POSITIVE_SCOPES and cap_detail and cap_detail.get("local_only") is not True:
            failures.append("local positive evidence must set capability_status_detail.local_only=true")
        if positive_scope in PUBLIC_POSITIVE_SCOPES and cap_detail and cap_detail.get("public_range_only") is not True:
            failures.append("public range positive evidence must set capability_status_detail.public_range_only=true")
        if positive_scope in AUTHORIZED_POSITIVE_SCOPES and cap_detail and cap_detail.get("authorized_only") is not True:
            failures.append("authorized positive evidence must set capability_status_detail.authorized_only=true")
        if positive_scope in PUBLIC_POSITIVE_SCOPES and scope_decision and scope_decision.get("why_in_scope", "").lower().find("third-party generalization") >= 0:
            failures.append("public range positive must not generalize to third-party sites")

    if scope_decision:
        if scope_decision.get("target_id") != target_id:
            failures.append("scope_decision.target_id must match target.id")
        if scope_decision.get("scope_type") != target_contract.get("scope_type"):
            failures.append("scope_decision.scope_type must match contract")
        if scope_decision.get("authorization") != target_contract.get("authorization"):
            failures.append("scope_decision.authorization must match contract")
        recorded_config = str(scope_decision.get("scope_contract_path", "")).replace("\\", "/")
        accepted_config_paths = {
            str(config_path).replace("\\", "/"),
            str(config_path.resolve()).replace("\\", "/"),
            str(config_path.resolve().relative_to(ROOT)).replace("\\", "/") if config_path.resolve().is_relative_to(ROOT) else "",
        }
        if recorded_config not in accepted_config_paths:
            warnings.append("scope_decision.scope_contract_path differs from validator config path")
        if scope_decision.get("in_scope") is True and (not host_ok or not mode_ok):
            failures.append("scope_decision.in_scope=true but host or mode does not match contract")
    elif positive:
        failures.append("missing scope_decision")

    return {
        "path": str(path),
        "target_id": target_id,
        "status": "PASS" if not failures else "FAIL",
        "in_scope": bool(host_ok and mode_ok),
        "scope_type": target_contract.get("scope_type"),
        "authorization": target_contract.get("authorization"),
        "allowed_mode": allowed_mode,
        "positive_allowed_scope": positive_scope,
        "failures": failures,
        "warnings": warnings,
    }


def validate_contract(config: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(config.get("targets", [])):
        if not isinstance(item, dict):
            failures.append(f"targets[{index}] must be object")
            continue
        target_id = item.get("id")
        if not target_id:
            failures.append(f"targets[{index}].id is required")
        elif target_id in seen:
            failures.append(f"duplicate target id {target_id}")
        seen.add(str(target_id))
        for key in ("scope_type", "authorization", "allowed_modes", "positive_allowed_scope", "forbidden_modes", "evidence_required"):
            if key not in item:
                failures.append(f"target {target_id} missing {key}")
        if item.get("scope_type") != "authorized_target" and not item.get("allowed_hosts"):
            failures.append(f"target {target_id} requires allowed_hosts")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate scope contract and evidence scope decisions")
    parser.add_argument("--config", required=True)
    parser.add_argument("--repo-root", default=str(ROOT))
    parser.add_argument("--evidence-root", default="public-range-evidence")
    args = parser.parse_args()
    repo_root = Path(args.repo_root)
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = repo_root / config_path
    config = read_yaml(config_path)
    targets = contract_targets(config)
    contract_failures = validate_contract(config)
    root = repo_root / args.evidence_root
    results = [validate_payload(path, read_json(path), targets, Path(args.config)) for path in evidence_files(root)]
    evidence_failures = [item for item in results if item["status"] != "PASS"]
    payload = {
        "tool": "validate_scope_contract",
        "status": "PASS" if not contract_failures and not evidence_failures else "FAIL",
        "config": str(config_path),
        "target_count": len(targets),
        "in_scope_targets": sorted({item["target_id"] for item in results if item.get("in_scope")}),
        "out_of_scope_targets": sorted({item["target_id"] for item in results if not item.get("in_scope")}),
        "contract_failures": contract_failures,
        "evidence_failure_count": len(evidence_failures),
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
