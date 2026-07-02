#!/usr/bin/env python3
"""Build Phase 4A long-run trend reports from scoped evidence."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
LONGRUN_ROOT = ROOT / "public-range-evidence" / "longrun"
DATASET_ROOT = ROOT / "datasets" / "captcha_flywheel"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def collect_public_family_metrics(run_id: str) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for target in ("gocaptcha-official", "opencaptchaworld", "shumei-compatible-lab", "aliyun-compatible-lab", "five-second-shield-lab"):
        path = ROOT / "public-range-evidence" / target / f"{run_id}.json"
        if not path.is_file():
            continue
        data = read_json(path)
        families = data.get("action_replay", {}).get("metrics", {}).get("families", {})
        for family, item in families.items():
            key = f"{target}:{family}"
            metrics[key] = {
                "target": target,
                "family": family,
                "success_rate": item.get("success_rate", 0),
                "p95_error": item.get("p95_error"),
                "failure_count": item.get("failure_count", 0),
                "capability_status": item.get("capability_status", data.get("capability_status")),
            }
    return metrics


def collect_model_trends(run_id: str) -> dict[str, Any]:
    path = DATASET_ROOT / "predictions" / run_id / "prediction_manifest.json"
    if not path.is_file():
        return {"models": [], "improved_tasks": [], "training_needed_tasks": []}
    data = read_json(path)
    return {
        "models": [
            {
                "task": item.get("task"),
                "model_id": item.get("model_id"),
                "baseline_success_rate": item.get("baseline_metrics", {}).get("success_rate"),
                "trained_success_rate": item.get("trained_metrics", {}).get("success_rate"),
                "holdout_success_rate": item.get("holdout_metrics", {}).get("success_rate"),
                "delta": item.get("delta"),
                "promotion_decision": item.get("promotion_decision"),
            }
            for item in data.get("models", [])
        ],
        "improved_tasks": data.get("improved_tasks", []),
        "training_needed_tasks": data.get("training_needed_tasks", []),
    }


def collect_audit_counts(run_id: str) -> dict[str, Any]:
    counts = {
        "leakage_failure_count": None,
        "blackbox_gate_failure_count": None,
        "anti_solver_violation_count": None,
    }
    paths = {
        "leakage_failure_count": ROOT / "public-range-evidence" / "raw" / "captcha-leakage-audit" / run_id / "leakage-audit.json",
        "blackbox_gate_failure_count": ROOT / "public-range-evidence" / "raw" / "captcha-blackbox-gate" / run_id / "blackbox-gate.json",
        "anti_solver_violation_count": ROOT / "public-range-evidence" / "raw" / "anti-solver-platform-audit" / run_id / "anti-solver-platform-audit.json",
    }
    source_fields = {
        "leakage_failure_count": "failures",
        "blackbox_gate_failure_count": "failures",
        "anti_solver_violation_count": "violations",
    }
    for name, path in paths.items():
        if path.is_file():
            value = read_json(path).get(source_fields[name])
            counts[name] = len(value) if isinstance(value, list) else value
    return counts


def compare_with_previous(run_id: str, current: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    previous_files = sorted(
        [path for path in LONGRUN_ROOT.glob("*/metric-trends.json") if path.parent.name != run_id],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not previous_files:
        return [], []
    previous = read_json(previous_files[0]).get("target_family_trends", {})
    improved = []
    regressed = []
    for key, item in current.items():
        old = previous.get(key, {})
        if "success_rate" not in old:
            continue
        delta = float(item.get("success_rate") or 0) - float(old.get("success_rate") or 0)
        row = {"target_family": key, "previous": old.get("success_rate"), "current": item.get("success_rate"), "delta": delta}
        if delta > 0.05:
            improved.append(row)
        elif delta < -0.05:
            regressed.append(row)
    return improved, regressed


def main() -> int:
    parser = argparse.ArgumentParser(description="Build long-run metric trend report")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    run_id = args.run_id
    out_dir = LONGRUN_ROOT / run_id
    family_metrics = collect_public_family_metrics(run_id)
    model_trends = collect_model_trends(run_id)
    audit_counts = collect_audit_counts(run_id)
    improved, regressed = compare_with_previous(run_id, family_metrics)
    failure_trends = {
        key: {
            "failure_count": item.get("failure_count"),
            "needs_failure_replay": float(item.get("success_rate") or 0) < 0.8,
            "capability_status": item.get("capability_status"),
        }
        for key, item in family_metrics.items()
    }
    metric_trends = {
        "run_id": run_id,
        "created_at": utc_now(),
        "target_family_trends": family_metrics,
        "ocr_trends": {"char_accuracy": None, "sequence_accuracy": None, "status": "no_ocr_samples"},
        "action_replay_before_after_trends": read_json(DATASET_ROOT / "failures" / run_id / "failure_replay.json").get("before_after_action_replay", []) if (DATASET_ROOT / "failures" / run_id / "failure_replay.json").is_file() else [],
        "model_metric_delta": model_trends,
        "capability_changes": {"improved": improved, "regressed": regressed, "stable_positive": []},
        "business_data_pass_count": None,
        "fingerprint_drift_count": 0,
        "js_parity_flaky_count": 0,
        "concurrency_failure_rate": None,
        **audit_counts,
    }
    issues = []
    for key, item in failure_trends.items():
        if item["needs_failure_replay"]:
            issues.append({
                "issue_id": f"{run_id}-trend-{len(issues)+1:03d}",
                "target_family": key,
                "status": "needs_failure_replay",
                "failure_count": item["failure_count"],
                "promotion_blocked": True,
            })
    capability_delta = {
        "run_id": run_id,
        "improved": improved,
        "regressed": regressed,
        "promotion_blocked": bool(regressed or issues),
    }
    write_json(out_dir / "metric-trends.json", metric_trends)
    write_json(out_dir / "failure-trends.json", {"run_id": run_id, "failure_trends": failure_trends})
    write_json(out_dir / "model-trends.json", {"run_id": run_id, **model_trends})
    if issues:
        existing_path = out_dir / "issue-ledger.json"
        existing = read_json(existing_path) if existing_path.is_file() else {"run_id": run_id, "issues": []}
        base_issues = [
            item for item in existing.get("issues", [])
            if not str(item.get("issue_id", "")).startswith(f"{run_id}-trend-")
        ]
        covered = {item.get("target_family") for item in base_issues}
        existing["issues"] = base_issues + [item for item in issues if item.get("target_family") not in covered]
        write_json(existing_path, existing)
    write_json(out_dir / "capability-delta.json", capability_delta)
    artifact_index = {"run_id": run_id, "artifacts": [str(path) for path in sorted(out_dir.rglob("*")) if path.is_file()]}
    write_json(out_dir / "artifact-index.json", artifact_index)
    print(json.dumps({"status": "PASS", "run_id": run_id, "metric_trends": str(out_dir / "metric-trends.json"), "issue_count": len(issues), "regressed_count": len(regressed)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
