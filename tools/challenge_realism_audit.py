#!/usr/bin/env python3
"""Audit challenge realism so clean compatible labs cannot be over-promoted."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DIFFICULTIES = {"easy", "medium", "hard", "adversarial"}
EXPECTED_FAMILIES = {
    "shumei-compatible-lab": {"slide", "select", "icon_select", "seq_select", "spatial_select", "no_sense"},
    "aliyun-compatible-lab": {"slider", "puzzle", "image_restore", "spatial_reasoning", "one_click", "no_trace"},
}
STATE_MACHINE_ONLY = {"no_trace", "one_click", "no_sense"}


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


def vendor_target_audit(run_id: str, target: str) -> dict[str, Any]:
    evidence_path = ROOT / "public-range-evidence" / target / f"{run_id}.json"
    if not evidence_path.is_file():
        return {"target": target, "status": "NOT_RUN", "failures": [f"missing evidence {evidence_path}"]}
    evidence = read_json(evidence_path)
    metrics = evidence.get("action_replay", {}).get("metrics", {})
    records_path = Path(str(metrics.get("records_path") or ""))
    rows = read_jsonl(records_path)
    failures: list[str] = []
    warnings: list[str] = []
    invalid_reasons: list[str] = []
    missing_family: list[str] = []
    missing_difficulty: list[dict[str, Any]] = []
    too_clean_metrics: list[dict[str, Any]] = []
    fixed_answer_risk = False
    geometry_fixed_risk = False
    missing_state_binding: list[str] = []
    official_generalization_risk = bool(evidence.get("official_vendor")) or evidence.get("not_generalizable_to_vendor_production") is not True
    families = metrics.get("families") if isinstance(metrics.get("families"), dict) else {}
    if not families:
        invalid_reasons.append("missing per-family metrics")
    expected = EXPECTED_FAMILIES.get(target, set())
    missing_family = sorted(expected - set(families))
    if missing_family:
        invalid_reasons.append(f"missing family metrics: {','.join(missing_family)}")
    if official_generalization_risk:
        invalid_reasons.append("compatible lab is written as official vendor or missing non-generalization flag")
    all_too_clean = True
    for family, item in families.items():
        if not isinstance(item, dict):
            invalid_reasons.append(f"{family}: metrics must be object")
            continue
        diff = item.get("per_difficulty_metrics")
        if not isinstance(diff, dict) or set(diff) < DIFFICULTIES:
            missing_difficulty.append({"family": family, "present": sorted(diff) if isinstance(diff, dict) else []})
            invalid_reasons.append(f"{family}: missing easy/medium/hard/adversarial metrics")
            continue
        for name in ("easy", "medium", "hard"):
            if int(diff.get(name, {}).get("sample_count") or 0) < 100:
                invalid_reasons.append(f"{family}:{name}: sample_count < 100")
        if int(diff.get("adversarial", {}).get("sample_count") or 0) < 50:
            invalid_reasons.append(f"{family}:adversarial: sample_count < 50")
        if int(item.get("failure_count") or 0) > 0 or float(item.get("p95_error") or 0) > 0:
            all_too_clean = False
        if family not in STATE_MACHINE_ONLY and int(item.get("failure_count") or 0) == 0 and float(item.get("p95_error") or 0) == 0:
            too_clean_metrics.append({"family": family, "success_rate": item.get("success_rate"), "p95_error": item.get("p95_error")})
    if all_too_clean:
        warnings.append("all positive families are 100/100 with p95=0; realism_status=TOO_EASY")
    if not evidence.get("failure_cases_path") or not Path(str(evidence.get("failure_cases_path"))).is_file():
        invalid_reasons.append("missing failure cases")
    if not rows:
        invalid_reasons.append("missing action records")
    else:
        dprs = {str(row.get("device_pixel_ratio")) for row in rows}
        offsets = {json.dumps(row.get("canvas_offset"), sort_keys=True) for row in rows}
        viewports = {json.dumps(row.get("viewport"), sort_keys=True) for row in rows}
        predictions = {json.dumps(row.get("prediction"), sort_keys=True) for row in rows if row.get("family") not in STATE_MACHINE_ONLY}
        timings = [row.get("action_timing_ms") for row in rows if isinstance(row.get("action_timing_ms"), (int, float))]
        hard_rows = [row for row in rows if row.get("difficulty") == "hard"]
        adversarial_rows = [row for row in rows if row.get("difficulty") == "adversarial"]
        if len(dprs) < 2:
            geometry_fixed_risk = True
            invalid_reasons.append("missing randomized DPR")
        if len(offsets) < 2:
            geometry_fixed_risk = True
            invalid_reasons.append("missing randomized canvas offset")
        if len(viewports) < 2:
            geometry_fixed_risk = True
            invalid_reasons.append("missing randomized viewport")
        if len(predictions) < 3:
            fixed_answer_risk = True
            invalid_reasons.append("prediction space is too fixed")
        if not timings:
            invalid_reasons.append("missing action timing")
        if not hard_rows or not adversarial_rows:
            invalid_reasons.append("missing hard/adversarial rows")
        if not any(row.get("transform_pipeline") for row in rows):
            invalid_reasons.append("missing transform_pipeline")
        if not any(row.get("noise_profile") for row in rows):
            invalid_reasons.append("missing noise_profile")
        if any(row.get("answer_source") != "server_hidden_not_returned" for row in rows):
            invalid_reasons.append("answer_source must remain server_hidden_not_returned")
        for family in expected & STATE_MACHINE_ONLY:
            family_rows = [row for row in rows if row.get("family") == family]
            if not family_rows:
                continue
            if not any(isinstance(row.get("server_state"), dict) and row["server_state"].get("challenge_instance_binding") for row in family_rows):
                missing_state_binding.append(family)
            if family in {"no_trace", "no_sense"} and not any(isinstance(row.get("server_state"), dict) and row["server_state"].get("second_challenge_possible") for row in family_rows):
                missing_state_binding.append(f"{family}:second_challenge")
        if missing_state_binding:
            invalid_reasons.append(f"missing state binding: {','.join(missing_state_binding)}")
    status = "INVALID" if invalid_reasons else ("TOO_EASY" if all_too_clean or too_clean_metrics else "PASS")
    return {
        "target": target,
        "status": status,
        "realism_audit": {
            "status": status,
            "too_clean_metrics": too_clean_metrics,
            "fixed_answer_risk": fixed_answer_risk,
            "geometry_fixed_risk": geometry_fixed_risk,
            "missing_family": missing_family,
            "missing_difficulty": missing_difficulty,
            "missing_negative_eval": [],
            "missing_state_binding": missing_state_binding,
            "official_generalization_risk": official_generalization_risk,
        },
        "realism_status": "PASS" if status == "PASS" else status,
        "record_count": len(rows),
        "failures": invalid_reasons,
        "warnings": warnings,
    }


def shield_audit(run_id: str) -> dict[str, Any]:
    target = "five-second-shield-lab"
    evidence_path = ROOT / "public-range-evidence" / target / f"{run_id}.json"
    if not evidence_path.is_file():
        return {"target": target, "status": "NOT_RUN", "failures": [f"missing evidence {evidence_path}"]}
    evidence = read_json(evidence_path)
    metrics = evidence.get("action_replay", {}).get("metrics", {})
    dynamic = evidence.get("dynamic_js_challenge") if isinstance(evidence.get("dynamic_js_challenge"), dict) else {}
    profile_metrics = dynamic.get("profiles") if isinstance(dynamic.get("profiles"), dict) else {}
    ladder = evidence.get("concurrency_ladder") if isinstance(evidence.get("concurrency_ladder"), dict) else {}
    negatives = evidence.get("negative_evals") if isinstance(evidence.get("negative_evals"), list) else []
    failures: list[str] = []
    if int(dynamic.get("samples") or 0) < 100:
        failures.append("dynamic JS samples < 100")
    if int(dynamic.get("unique_script_hashes") or 0) < min(int(dynamic.get("samples") or 0), 100):
        failures.append("script hash did not mutate enough")
    if int(dynamic.get("unique_mutations") or 0) < min(int(dynamic.get("samples") or 0), 100):
        failures.append("mutation inputs did not vary enough")
    if dynamic.get("status") != "pass":
        failures.append("dynamic_js_challenge.status is not pass")
    if len(negatives) < 15:
        failures.append("negative eval count < 15")
    required_profiles = {
        "simple_delay_gate",
        "js_signature_gate",
        "redirect_chain_gate",
        "cookie_clearance_gate",
        "browser_state_binding_gate",
        "dynamic_script_mutation_gate",
        "retry_after_gate",
        "rate_limit_gate",
        "multi_stage_gate",
    }
    missing_profiles = sorted(required_profiles - set(profile_metrics))
    if missing_profiles:
        failures.append(f"missing shield profiles: {','.join(missing_profiles)}")
    for profile, item in profile_metrics.items():
        if int(item.get("sample_count") or 0) <= 0:
            failures.append(f"{profile}: no samples")
        for field in ("dynamic_script_hash", "nonce", "time_window", "expires_at", "replay_protection", "js_mutation", "redirect_chain", "challenge_verify", "final_business_api"):
            if item.get(field) is not True:
                failures.append(f"{profile}: missing {field}")
    for worker in ("worker_1", "worker_2", "worker_5", "worker_10", "worker_20"):
        if not isinstance(ladder.get(worker), dict) or ladder[worker].get("status") != "pass":
            failures.append(f"{worker} concurrency missing or failed")
        elif "p99_ms" not in ladder[worker]:
            failures.append(f"{worker} missing p99_ms")
    return {
        "target": target,
        "status": "PASS" if not failures else "FAIL",
        "realism_status": "DYNAMIC_JS_HARDENED" if not failures else "TOO_SIMPLE",
        "realism_audit": {
            "status": "PASS" if not failures else "INVALID",
            "too_clean_metrics": [],
            "fixed_answer_risk": False,
            "geometry_fixed_risk": False,
            "missing_family": missing_profiles,
            "missing_difficulty": [],
            "missing_negative_eval": [] if len(negatives) >= 15 else ["negative_eval_count_lt_15"],
            "missing_state_binding": [],
            "official_generalization_risk": False,
        },
        "failures": failures,
    }


def update_evidence(run_id: str, report_path: Path, target_reports: list[dict[str, Any]]) -> None:
    by_target = {item["target"]: item for item in target_reports}
    for target, item in by_target.items():
        path = ROOT / "public-range-evidence" / target / f"{run_id}.json"
        if not path.is_file():
            continue
        payload = read_json(path)
        audit = item.get("realism_audit") if isinstance(item.get("realism_audit"), dict) else {"status": item["status"]}
        audit["path"] = str(report_path)
        audit["realism_status"] = item.get("realism_status")
        payload["realism_audit"] = audit
        payload["realism_status"] = item.get("realism_status")
        if item["status"] not in {"PASS"} and payload.get("capability_status") in {"positive_verified", "stable_positive"}:
            payload["capability_status"] = "positive_candidate"
            if isinstance(payload.get("decision"), dict):
                payload["decision"]["skills_participation"] = "positive_candidate"
                payload["decision"]["positive_allowed"] = False
                payload["decision"]["blocked_reason"] = "challenge realism audit blocked verified/stable promotion"
        write_json(path, payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit challenge realism for Phase 3.10")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    reports = [
        vendor_target_audit(args.run_id, "shumei-compatible-lab"),
        vendor_target_audit(args.run_id, "aliyun-compatible-lab"),
        shield_audit(args.run_id),
    ]
    status = "PASS" if all(item.get("status") == "PASS" for item in reports) else "FAIL"
    report = {
        "tool": "challenge_realism_audit",
        "run_id": args.run_id,
        "status": status,
        "targets": reports,
        "decision": {
            "too_easy_cannot_be_verified": True,
            "too_easy_can_only_be_candidate": True,
            "hard_adversarial_required": True,
        },
    }
    out = ROOT / "public-range-evidence" / "raw" / "challenge-realism-audit" / args.run_id / "challenge-realism-audit.json"
    write_json(out, report)
    update_evidence(args.run_id, out, reports)
    print(json.dumps({"status": status, "run_id": args.run_id, "report_path": str(out), "failure_count": sum(len(item.get("failures", [])) for item in reports)}, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
