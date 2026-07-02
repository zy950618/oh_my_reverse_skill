#!/usr/bin/env python3
"""Decide candidate/verified/stable capability promotion from range evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load(path: Path) -> dict[str, Any]:
    return read_json(path) if path.is_file() else {}


def evidence_files() -> list[Path]:
    root = ROOT / "public-range-evidence"
    if not root.is_dir():
        return []
    return sorted(path for path in root.rglob("*.json") if not {"raw", "longrun"} & {part.lower() for part in path.parts})


def status_of(payload: dict[str, Any]) -> str:
    return str(payload.get("capability_status") or payload.get("decision", {}).get("skills_participation") or "")


def count_status(paths: list[Path], status: str, exclude_run_id: str | None = None) -> int:
    total = 0
    for path in paths:
        try:
            payload = read_json(path)
        except Exception:
            continue
        if exclude_run_id and payload.get("run_id") == exclude_run_id:
            continue
        if status_of(payload) == status:
            total += 1
    return total


def compatible_lab_decision(run_id: str) -> tuple[dict[str, Any], list[str], list[str], list[dict[str, Any]]]:
    evidence = load(ROOT / "public-range-evidence" / "local-gocaptcha-compatible-lab" / f"{run_id}.json")
    leakage = load(ROOT / "public-range-evidence" / "raw" / "captcha-leakage-audit" / run_id / "leakage-audit.json")
    blackbox = load(ROOT / "public-range-evidence" / "raw" / "captcha-blackbox-gate" / run_id / "blackbox-gate.json")
    action = evidence.get("action_replay") if isinstance(evidence.get("action_replay"), dict) else {}
    metrics = action.get("metrics") if isinstance(action.get("metrics"), dict) else {}
    summary = metrics.get("gocaptcha_action_replay_summary") if isinstance(metrics.get("gocaptcha_action_replay_summary"), dict) else {}
    threshold_pass = metrics.get("threshold_pass") is True
    candidate_checks = {
        "evidence_present": bool(evidence),
        "target_corrected_to_compatible_lab": evidence.get("target", {}).get("id") == "local-gocaptcha-compatible-lab" if isinstance(evidence.get("target"), dict) else False,
        "not_real_gocaptcha_claim": metrics.get("target_authenticity", {}).get("uses_real_gocaptcha_component") is False if isinstance(metrics.get("target_authenticity"), dict) else False,
        "action_replay_records_present": int(metrics.get("total_records") or 0) > 0,
        "leakage_audit_pass": leakage.get("status") == "PASS",
        "blackbox_gate_pass": blackbox.get("status") == "PASS",
        "scope_contract_in_scope": evidence.get("scope_decision", {}).get("in_scope") is True if isinstance(evidence.get("scope_decision"), dict) else False,
    }
    candidate = all(candidate_checks.values())
    verified_checks = dict(candidate_checks)
    verified_checks.update({
        "multi_difficulty_threshold_pass": threshold_pass,
        "all_kind_summaries_present": all(kind in summary for kind in ("slide", "click", "rotate", "drag_drop")),
    })
    verified = all(verified_checks.values())
    stable = False
    promoted_candidate = ["local-gocaptcha-compatible-lab"] if candidate and not verified else []
    promoted_verified = ["local-gocaptcha-compatible-lab"] if verified else []
    why_promoted = []
    why_not_promoted: list[dict[str, Any]] = []
    if candidate:
        why_promoted.append("local-gocaptcha-compatible-lab has complete single-run/multi-sample evidence, leakage PASS, and blackbox PASS; promotion is candidate only unless thresholds and repeat runs pass.")
    else:
        why_not_promoted.append({"capability": "local-gocaptcha-compatible-lab", "missing": [key for key, value in candidate_checks.items() if not value]})
    if not verified:
        why_not_promoted.append({"capability": "local-gocaptcha-compatible-lab:verified", "missing": [key for key, value in verified_checks.items() if not value]})
    decision = {
        "checks": candidate_checks,
        "verified_checks": verified_checks,
        "decision": "positive_verified" if verified else ("positive_candidate" if candidate else "not_promoted"),
        "capability_status": "positive_verified" if verified else ("positive_candidate" if candidate else "memory_only"),
        "summary": summary,
        "stable_positive": stable,
    }
    return decision, promoted_candidate, promoted_verified, why_not_promoted if not candidate or not verified else []


def real_public_range_decision(run_id: str) -> tuple[dict[str, Any], list[str], list[str], list[dict[str, Any]], list[str]]:
    promoted_candidate: list[str] = []
    promoted_verified: list[str] = []
    why_not: list[dict[str, Any]] = []
    blocked_public_ranges: list[str] = []
    decisions: dict[str, Any] = {}
    family_level_capabilities: dict[str, Any] = {}
    for target, path in (
        ("opencaptchaworld", ROOT / "public-range-evidence" / "opencaptchaworld" / f"{run_id}.json"),
        ("gocaptcha-official", ROOT / "public-range-evidence" / "gocaptcha-official" / f"{run_id}.json"),
    ):
        evidence = load(path)
        leakage = load(ROOT / "public-range-evidence" / "raw" / "captcha-leakage-audit" / run_id / "leakage-audit.json")
        blackbox = load(ROOT / "public-range-evidence" / "raw" / "captcha-blackbox-gate" / run_id / "blackbox-gate.json")
        action = evidence.get("action_replay") if isinstance(evidence.get("action_replay"), dict) else {}
        metrics = action.get("metrics") if isinstance(action.get("metrics"), dict) else {}
        family_metrics = metrics.get("families") if isinstance(metrics.get("families"), dict) else {}
        family_level_capabilities[target] = {}
        for family, item in family_metrics.items():
            if not isinstance(item, dict):
                continue
            samples = int(item.get("sample_count") or 0)
            success_rate = float(item.get("success_rate") or 0)
            declared = item.get("capability_status")
            if declared in {"positive_candidate", "training_needed", "negative_eval_only", "memory_only", "positive_verified", "stable_positive", "prohibited", "unverified"}:
                status = declared
            elif samples <= 0:
                status = "unverified"
            elif success_rate >= 0.8:
                status = "positive_candidate"
            elif success_rate > 0:
                status = "training_needed"
            else:
                status = "negative_eval_only" if target == "gocaptcha-official" else "training_needed"
            family_level_capabilities[target][family] = {
                "status": status,
                "evidence": str(path),
                "sample_count": samples,
                "success_rate": success_rate,
                "p95_error": item.get("p95_error"),
                "capability_level": item.get("capability_level") or status,
                "why": item.get("why") or "per-family decision; target-level aggregate must not hide family failures",
            }
        candidate_checks = {
            "evidence_present": bool(evidence),
            "official_or_public_repo_confirmed": evidence.get("official_repo_confirmed") is True,
            "real_execution_pass": evidence.get("execution_status") == "REAL_EXECUTION_PASS",
            "browser_opened": evidence.get("browser_opened") is True,
            "action_replay_success_present": int(metrics.get("total_success") or 0) > 0,
            "records_present": bool(metrics.get("records_path")),
            "leakage_audit_pass": leakage.get("status") == "PASS",
            "blackbox_gate_pass": blackbox.get("status") == "PASS",
            "scope_contract_in_scope": evidence.get("scope_decision", {}).get("in_scope") is True if isinstance(evidence.get("scope_decision"), dict) else False,
        }
        verified_checks = dict(candidate_checks)
        verified_checks.update({
            "three_families_attempted": len([item for item in family_metrics.values() if isinstance(item, dict) and int(item.get("sample_count") or 0) >= 20]) >= 3,
            "threshold_pass": metrics.get("threshold_pass") is True,
            "visual_threshold_pass": metrics.get("visual_threshold_pass") is True if target == "opencaptchaworld" else True,
            "all_declared_families_min_rate": all(
                (float(item.get("success_rate") or 0) >= 0.5)
                for item in family_metrics.values()
                if isinstance(item, dict) and int(item.get("sample_count") or 0) > 0
            ) if target == "gocaptcha-official" else True,
            "failure_cases_present": bool(evidence.get("failure_cases_path")),
        })
        candidate = all(candidate_checks.values())
        verified = all(verified_checks.values())
        family_candidates = [
            f"{target}:{family}"
            for family, item in family_level_capabilities[target].items()
            if isinstance(item, dict) and item.get("status") == "positive_candidate"
        ]
        family_verified = [
            f"{target}:{family}"
            for family, item in family_level_capabilities[target].items()
            if isinstance(item, dict) and item.get("status") == "positive_verified"
        ]
        if candidate and family_candidates:
            promoted_candidate.extend(family_candidates)
        else:
            blocked_public_ranges.append(target)
            why_not.append({"capability": f"{target}:candidate", "missing": [key for key, value in candidate_checks.items() if not value]})
        if verified and family_verified:
            promoted_verified.extend(family_verified)
        else:
            why_not.append({"capability": f"{target}:verified", "missing": [key for key, value in verified_checks.items() if not value]})
        decisions[target] = {
            "checks": candidate_checks,
            "verified_checks": verified_checks,
            "decision": "family_scoped_positive_verified" if verified and family_verified else ("family_scoped_positive_candidate" if candidate and family_candidates else "not_promoted"),
            "capability_status": "positive_verified" if verified and family_verified else ("positive_candidate" if candidate and family_candidates else status_of(evidence) or "memory_only"),
            "metrics": metrics,
            "family_level_capabilities": family_level_capabilities[target],
        }
    decisions["family_level_capabilities"] = family_level_capabilities
    return decisions, promoted_candidate, promoted_verified, why_not, blocked_public_ranges


def vendor_compatible_decision(run_id: str) -> tuple[dict[str, Any], list[str], list[str], list[dict[str, Any]]]:
    decisions: dict[str, Any] = {}
    promoted_candidate: list[str] = []
    promoted_verified: list[str] = []
    why_not: list[dict[str, Any]] = []
    realism = load(ROOT / "public-range-evidence" / "raw" / "challenge-realism-audit" / run_id / "challenge-realism-audit.json")
    realism_by_target = {
        str(item.get("target")): item
        for item in realism.get("targets", [])
        if isinstance(item, dict)
    }
    for target in ("shumei-compatible-lab", "aliyun-compatible-lab"):
        path = ROOT / "public-range-evidence" / target / f"{run_id}.json"
        evidence = load(path)
        leakage = load(ROOT / "public-range-evidence" / "raw" / "captcha-leakage-audit" / run_id / "leakage-audit.json")
        blackbox = load(ROOT / "public-range-evidence" / "raw" / "captcha-blackbox-gate" / run_id / "blackbox-gate.json")
        action = evidence.get("action_replay") if isinstance(evidence.get("action_replay"), dict) else {}
        metrics = action.get("metrics") if isinstance(action.get("metrics"), dict) else {}
        family_metrics = metrics.get("families") if isinstance(metrics.get("families"), dict) else {}
        candidate_checks = {
            "evidence_present": bool(evidence),
            "compatible_lab_label": evidence.get("compatible_lab") is True,
            "not_official_vendor": evidence.get("official_vendor") is False,
            "not_generalizable_to_vendor_production": evidence.get("not_generalizable_to_vendor_production") is True,
            "real_execution_pass": evidence.get("execution_status") == "REAL_EXECUTION_PASS",
            "action_replay_success_present": int(metrics.get("total_success") or 0) > 0,
            "leakage_audit_pass": leakage.get("status") == "PASS",
            "blackbox_gate_pass": blackbox.get("status") == "PASS",
            "realism_audit_pass": realism_by_target.get(target, {}).get("status") == "PASS",
            "scope_contract_in_scope": evidence.get("scope_decision", {}).get("in_scope") is True if isinstance(evidence.get("scope_decision"), dict) else False,
        }
        candidate = all(candidate_checks.values())
        family_capabilities: dict[str, Any] = {}
        for family, item in family_metrics.items():
            if not isinstance(item, dict):
                continue
            status = item.get("capability_status") or ("positive_candidate" if float(item.get("success_rate") or 0) >= 0.8 else "training_needed")
            family_capabilities[family] = {"status": status, "sample_count": item.get("sample_count"), "success_rate": item.get("success_rate"), "evidence": str(path)}
            if candidate and status == "positive_candidate":
                promoted_candidate.append(f"{target}:{family}")
        if not candidate:
            why_not.append({"capability": f"{target}:candidate", "missing": [key for key, value in candidate_checks.items() if not value]})
        decisions[target] = {"checks": candidate_checks, "decision": "family_scoped_positive_candidate" if candidate else "not_promoted", "family_level_capabilities": family_capabilities}
    return decisions, promoted_candidate, promoted_verified, why_not


def shield_lab_decision(run_id: str) -> tuple[dict[str, Any], list[str], list[str], list[dict[str, Any]]]:
    target = "five-second-shield-lab"
    path = ROOT / "public-range-evidence" / target / f"{run_id}.json"
    evidence = load(path)
    realism = load(ROOT / "public-range-evidence" / "raw" / "challenge-realism-audit" / run_id / "challenge-realism-audit.json")
    realism_by_target = {
        str(item.get("target")): item
        for item in realism.get("targets", [])
        if isinstance(item, dict)
    }
    bda = evidence.get("business_data_assertions") if isinstance(evidence.get("business_data_assertions"), dict) else {}
    js = evidence.get("js_runtime_parity") if isinstance(evidence.get("js_runtime_parity"), dict) else {}
    candidate_checks = {
        "evidence_present": bool(evidence),
        "real_execution_pass": evidence.get("execution_status") == "REAL_EXECUTION_PASS",
        "control_flow_pass": evidence.get("control_flow_status") == "CONTROL_FLOW_PASS",
        "business_data_pass": evidence.get("business_data_status") == "DATA_ASSERTION_PASS",
        "js_runtime_parity_pass": js.get("status") == "pass",
        "negative_eval_present": bool(evidence.get("negative_evals")),
        "concurrency_ladder_present": bool(evidence.get("concurrency_ladder")),
        "business_data_assertions_pass": bda.get("status") == "pass",
        "realism_audit_pass": realism_by_target.get(target, {}).get("status") == "PASS",
        "scope_contract_in_scope": evidence.get("scope_decision", {}).get("in_scope") is True if isinstance(evidence.get("scope_decision"), dict) else False,
        "not_generalizable": evidence.get("capability_status_detail", {}).get("not_generalizable_to_third_party") is True if isinstance(evidence.get("capability_status_detail"), dict) else False,
    }
    verified_checks = dict(candidate_checks)
    verified_checks["repeat_or_longrun_regression"] = False
    candidate = all(candidate_checks.values())
    verified = all(verified_checks.values())
    why_not = []
    if not candidate:
        why_not.append({"capability": f"{target}:candidate", "missing": [key for key, value in candidate_checks.items() if not value]})
    if not verified:
        why_not.append({"capability": f"{target}:verified", "missing": [key for key, value in verified_checks.items() if not value]})
    return {
        "checks": candidate_checks,
        "verified_checks": verified_checks,
        "decision": "positive_verified" if verified else ("positive_candidate" if candidate else "not_promoted"),
        "capability_status": "positive_verified" if verified else ("positive_candidate" if candidate else "memory_only"),
        "evidence_path": str(path),
    }, ([target] if candidate and not verified else []), ([target] if verified else []), why_not


def high_fidelity_decision() -> tuple[dict[str, Any], list[str], list[dict[str, Any]]]:
    path = ROOT / "public-range-evidence" / "high-fidelity-risk-lab" / "run-20260630-022227-high-fidelity-risk-lab.json"
    evidence = load(path)
    checks = {
        "evidence_present": bool(evidence),
        "scope_in_scope": evidence.get("scope_decision", {}).get("in_scope") is True if isinstance(evidence.get("scope_decision"), dict) else False,
        "real_execution_pass": evidence.get("execution_status") == "REAL_EXECUTION_PASS",
        "control_flow_pass": evidence.get("control_flow_status") == "CONTROL_FLOW_PASS",
        "business_data_pass": evidence.get("business_data_status") == "DATA_ASSERTION_PASS",
        "negative_eval_present": bool(evidence.get("negative_evals")),
        "concurrency_ladder_present": bool(evidence.get("concurrency_ladder")),
        "direct_repeat_present": bool(evidence.get("direct_interface_repeat")),
        "not_generalizable": evidence.get("capability_status_detail", {}).get("not_generalizable_to_third_party") is True if isinstance(evidence.get("capability_status_detail"), dict) else False,
    }
    verified = all(checks.values())
    why_not = []
    if not verified:
        why_not.append({"capability": "high-fidelity-risk-lab:verified", "missing": [key for key, value in checks.items() if not value]})
    return {
        "checks": checks,
        "decision": "positive_verified" if verified else "not_promoted",
        "capability_status": "positive_verified" if verified else "memory_only",
        "evidence_path": str(path),
    }, (["high-fidelity-risk-lab"] if verified else []), why_not


def fingerprint_decisions(run_id: str) -> tuple[list[str], list[dict[str, Any]]]:
    promoted = []
    why_not = []
    for target in ("sannysoft", "creepjs", "browserleaks", "incolumitas"):
        path = ROOT / "public-range-evidence" / "fingerprint-diagnostics" / f"{run_id}-{target}.json"
        evidence = load(path)
        if status_of(evidence) == "positive_candidate":
            promoted.append(f"fingerprint-diagnostics:{target}")
        else:
            why_not.append({"capability": f"fingerprint-diagnostics:{target}", "missing": ["repeat/profile diagnostics candidate evidence"]})
    return promoted, why_not


def main() -> int:
    parser = argparse.ArgumentParser(description="Run capability promotion gate")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    run_id = args.run_id

    compatible, compat_candidates, compat_verified, compat_not = compatible_lab_decision(run_id)
    real_public, public_candidates, public_verified, public_not, blocked_public_ranges = real_public_range_decision(run_id)
    vendor_compatible, vendor_candidates, vendor_verified, vendor_not = vendor_compatible_decision(run_id)
    shield_lab, shield_candidates, shield_verified, shield_not = shield_lab_decision(run_id)
    high_fidelity, high_verified, high_not = high_fidelity_decision()
    fingerprint_candidates, fingerprint_not = fingerprint_decisions(run_id)
    all_paths = evidence_files()
    previous_candidate_count = count_status(all_paths, "positive_candidate", exclude_run_id=run_id)
    previous_verified_count = count_status(all_paths, "positive_verified", exclude_run_id=run_id)
    previous_stable_count = count_status(all_paths, "stable_positive", exclude_run_id=run_id)
    promoted_to_candidate = compat_candidates + public_candidates + vendor_candidates + shield_candidates + fingerprint_candidates
    promoted_to_verified = compat_verified + public_verified + vendor_verified + shield_verified + high_verified
    promoted_to_stable: list[str] = []
    delta = {
        "run_id": run_id,
        "previous_candidate_count": previous_candidate_count,
        "previous_verified_positive_count": previous_verified_count,
        "previous_stable_positive_count": previous_stable_count,
        "new_candidate_count": count_status(all_paths, "positive_candidate"),
        "new_verified_positive_count": count_status(all_paths, "positive_verified"),
        "new_stable_positive_count": count_status(all_paths, "stable_positive"),
        "promoted_to_candidate": promoted_to_candidate,
        "promoted_to_verified": promoted_to_verified,
        "promoted_to_stable": promoted_to_stable,
        "regressed_capabilities": [],
        "blocked_public_ranges": blocked_public_ranges,
        "why_promoted": [
            {"capability": item, "reason": "candidate evidence complete but not stable"} for item in promoted_to_candidate
        ] + [
            {"capability": item, "reason": "verified local-scope evidence gates passed"} for item in promoted_to_verified
        ],
        "why_not_promoted": compat_not + public_not + vendor_not + shield_not + high_not + fingerprint_not,
    }
    decision = {
        "run_id": run_id,
        "local_gocaptcha_compatible_lab": compatible,
        "real_public_ranges": real_public,
        "vendor_compatible_labs": vendor_compatible,
        "five_second_shield_lab": shield_lab,
        "high_fidelity_risk_lab": high_fidelity,
        "fingerprint_diagnostics": {
            "decision": "positive_candidate" if fingerprint_candidates else "memory_only",
            "promoted_to_candidate": fingerprint_candidates,
            "not_evasion_positive": True,
        },
        "capability_delta": delta,
    }
    out_dir = ROOT / "public-range-evidence" / "raw" / "capability-promotion" / run_id
    write_json(out_dir / "promotion-decision.json", decision)
    write_json(out_dir / "capability_delta.json", delta)
    write_json(ROOT / "public-range-evidence" / "longrun" / "phase3-6" / run_id / "capability-decision.json", decision)
    print(json.dumps({
        "status": "PASS",
        "run_id": run_id,
        "decision_path": str(out_dir / "promotion-decision.json"),
        "capability_delta_path": str(out_dir / "capability_delta.json"),
        "promoted_to_candidate": promoted_to_candidate,
        "promoted_to_verified": promoted_to_verified,
        "promoted_to_stable": promoted_to_stable,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
