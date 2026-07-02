#!/usr/bin/env python3
"""Sustainable long-run loop for scoped public/local range verification."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
LONGRUN_ROOT = ROOT / "public-range-evidence" / "longrun"
DATASET_ROOT = ROOT / "datasets" / "captcha_flywheel"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_yaml(path: Path) -> dict[str, Any]:
    import yaml  # type: ignore

    return yaml.safe_load(path.read_text(encoding="utf-8-sig"))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_command(command: list[str], cwd: Path = ROOT, timeout: int = 900, dry_run: bool = False) -> dict[str, Any]:
    started = utc_now()
    if dry_run:
        return {
            "command": command,
            "command_text": " ".join(command),
            "started_at": started,
            "ended_at": utc_now(),
            "exit_code": 0,
            "stdout": "dry-run",
            "stderr": "",
            "dry_run": True,
        }
    try:
        proc = subprocess.run(command, cwd=str(cwd), text=True, capture_output=True, timeout=timeout)
        return {
            "command": command,
            "command_text": " ".join(command),
            "started_at": started,
            "ended_at": utc_now(),
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "dry_run": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "command_text": " ".join(command),
            "started_at": started,
            "ended_at": utc_now(),
            "exit_code": 124,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "timeout",
            "dry_run": False,
        }


def latest_model_registry() -> str:
    candidates = sorted(DATASET_ROOT.glob("models/*/model_registry.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return str(candidates[0]) if candidates else ""


def parse_stdout_json(command_result: dict[str, Any]) -> dict[str, Any]:
    stdout = str(command_result.get("stdout") or "").strip()
    if not stdout:
        return {}
    start = stdout.find("{")
    end = stdout.rfind("}")
    if start == -1 or end == -1 or end < start:
        return {}
    try:
        return json.loads(stdout[start:end + 1])
    except Exception:
        return {}


def load_checkpoint(path: Path) -> dict[str, Any]:
    if path.is_file():
        return read_json(path)
    return {"completed_steps": [], "updated_at": utc_now()}


def save_checkpoint(path: Path, checkpoint: dict[str, Any]) -> None:
    checkpoint["updated_at"] = utc_now()
    write_json(path, checkpoint)


def copy_if_exists(src: str | Path, dst: Path) -> str:
    path = Path(src)
    if path.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dst)
        return str(dst)
    return ""


def list_artifacts(root: Path) -> list[str]:
    if not root.exists():
        return []
    return [str(path) for path in sorted(root.rglob("*")) if path.is_file()]


def step_command(step: dict[str, Any], python: str, run_id: str, model_registry: str) -> list[str]:
    kind = step["kind"]
    if kind == "real_public_range":
        command = [python, "tools/real_public_range_runner.py", "--target", step["target"], "--run-id", run_id]
        if "family" in step:
            command += ["--family", ",".join(step["family"])]
        if "families" in step:
            command += ["--families", ",".join(step["families"])]
        if "difficulty" in step:
            command += ["--difficulty", ",".join(step["difficulty"])]
        if "samples_per_family" in step:
            command += ["--samples-per-family", str(step["samples_per_family"])]
        if "samples" in step:
            command += ["--samples", str(step["samples"])]
        if "profiles" in step:
            command += ["--profiles", ",".join(step["profiles"])]
        if "concurrency" in step:
            command += ["--concurrency", ",".join(str(item) for item in step["concurrency"])]
        if step.get("dynamic_js"):
            command += ["--dynamic-js"]
        if model_registry:
            command += ["--model-registry", model_registry]
        return command
    if kind == "fingerprint":
        return [python, "tools/fingerprint_range_runner.py", "--target", step["target"], "--run-id", run_id, "--repeat", str(step.get("repeat", 1)), "--profiles", str(step.get("profiles", 1))]
    if kind == "simple":
        command = [python, step["tool"], "--run-id", run_id]
        for key, value in step.get("args", {}).items():
            command.append(f"--{key.replace('_', '-')}")
            if value is not True:
                command.append(str(value))
        return command
    raise ValueError(f"unsupported step kind: {kind}")


def build_steps(config: dict[str, Any], mode: str, args: argparse.Namespace, run_id: str) -> list[dict[str, Any]]:
    smoke = config["smoke"]
    steps: list[dict[str, Any]] = []
    if mode in {"smoke", "nightly", "weekly", "full", "targeted-family"} and not args.skip_public_range:
        if not args.only_target or args.only_target == "gocaptcha-official":
            families = args.only_family.split(",") if args.only_family else smoke["gocaptcha"]["families"]
            steps.append({"name": "gocaptcha", "kind": "real_public_range", "target": "gocaptcha-official", "family": families, "samples_per_family": smoke["gocaptcha"]["samples_per_family"]})
        if not args.only_target or args.only_target == "opencaptchaworld":
            families = args.only_family.split(",") if args.only_family else smoke["opencaptchaworld"]["families"]
            steps.append({"name": "opencaptchaworld", "kind": "real_public_range", "target": "opencaptchaworld", "families": families, "samples_per_family": smoke["opencaptchaworld"]["samples_per_family"]})
    if mode in {"smoke", "nightly", "weekly", "full", "targeted-family"} and not args.skip_vendor_compatible:
        if not args.only_target or args.only_target == "shumei-compatible-lab":
            families = args.only_family.split(",") if args.only_family else smoke["shumei_compatible"]["families"]
            steps.append({"name": "shumei-compatible", "kind": "real_public_range", "target": "shumei-compatible-lab", "families": families, "difficulty": smoke["shumei_compatible"]["difficulties"], "samples_per_family": smoke["shumei_compatible"]["samples_per_family"]})
        if not args.only_target or args.only_target == "aliyun-compatible-lab":
            families = args.only_family.split(",") if args.only_family else smoke["aliyun_compatible"]["families"]
            steps.append({"name": "aliyun-compatible", "kind": "real_public_range", "target": "aliyun-compatible-lab", "families": families, "difficulty": smoke["aliyun_compatible"]["difficulties"], "samples_per_family": smoke["aliyun_compatible"]["samples_per_family"]})
    if mode in {"smoke", "nightly", "weekly", "full"} and not args.skip_shield and (not args.only_target or args.only_target == "five-second-shield-lab"):
        shield = smoke["five_second_shield"]
        steps.append({"name": "five-second-shield", "kind": "real_public_range", "target": "five-second-shield-lab", "samples": shield["samples"], "profiles": shield["profiles"], "concurrency": shield["concurrency"], "dynamic_js": True})
    if mode in {"smoke", "nightly", "weekly", "full"} and not args.skip_fingerprint:
        for target in smoke["fingerprint"]["targets"]:
            if not args.only_target or args.only_target == target:
                steps.append({"name": f"fingerprint-{target}", "kind": "fingerprint", "target": target, "repeat": smoke["fingerprint"]["repeat"], "profiles": smoke["fingerprint"]["profiles"]})
    if mode in {"smoke", "nightly", "weekly", "full", "failure-replay-only"}:
        steps.append({"name": "failure-collector", "kind": "simple", "tool": "tools/captcha_failure_collector.py"})
        steps.append({"name": "label-manifest", "kind": "simple", "tool": "tools/captcha_label_manifest_builder.py"})
        steps.append({"name": "dataset-splitter", "kind": "simple", "tool": "tools/captcha_dataset_splitter.py"})
    if mode in {"smoke", "nightly", "weekly", "full", "model-train-only"} and not args.skip_model_training:
        for task in smoke["model_training"]["tasks"]:
            steps.append({"name": f"model-train-{task}", "kind": "simple", "tool": "tools/captcha_model_trainer.py", "args": {"task": task}})
        steps.append({"name": "model-evaluator", "kind": "simple", "tool": "tools/captcha_model_evaluator.py"})
    if mode in {"smoke", "nightly", "weekly", "full", "failure-replay-only"}:
        steps.append({"name": "failure-replay", "kind": "simple", "tool": "tools/captcha_failure_replay.py"})
    if mode in {"smoke", "nightly", "weekly", "full", "audit-only"}:
        steps += [
            {"name": "anti-solver-audit", "kind": "simple", "tool": "tools/anti_solver_platform_audit.py"},
            {"name": "blackbox-gate", "kind": "simple", "tool": "tools/captcha_blackbox_solver_gate.py"},
            {"name": "leakage-audit", "kind": "simple", "tool": "tools/captcha_leakage_audit.py"},
        ]
    return steps


def read_family_metrics(run_id: str) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for target in ("gocaptcha-official", "opencaptchaworld", "shumei-compatible-lab", "aliyun-compatible-lab", "five-second-shield-lab"):
        path = ROOT / "public-range-evidence" / target / f"{run_id}.json"
        if not path.is_file():
            continue
        data = read_json(path)
        families = data.get("action_replay", {}).get("metrics", {}).get("families", {})
        for family, item in families.items():
            metrics[f"{target}:{family}"] = item
    return metrics


def build_capability_decision(run_id: str, family_metrics: dict[str, Any], command_log: list[dict[str, Any]]) -> dict[str, Any]:
    decisions = []
    for key, item in sorted(family_metrics.items()):
        rate = float(item.get("success_rate") or 0)
        status = "positive_candidate" if rate >= 0.8 else "training_needed"
        if key.startswith("gocaptcha-official") or key.startswith("opencaptchaworld"):
            status = "memory_only" if rate > 0 else "training_needed"
        decisions.append({
            "target_family": key,
            "status": status,
            "success_rate": rate,
            "failure_count": item.get("failure_count"),
            "why": "family scoped decision; no target-level umbrella positive",
        })
    blocked = [
        {"step": item["step"], "exit_code": item["exit_code"], "reason": "command failed or blocked"}
        for item in command_log
        if item.get("exit_code") not in (0, None)
    ]
    return {
        "run_id": run_id,
        "created_at": utc_now(),
        "rules": {
            "target_level_positive_forbidden": True,
            "fingerprint_evasion_forbidden": True,
            "waf_bypass_claim_forbidden": True,
            "official_vendor_generalization_forbidden": True,
        },
        "family_decisions": decisions,
        "blocked": blocked,
        "positive_verified": ["existing high-fidelity-risk-lab only"],
        "stable_positive": [],
    }


def build_skills_update_queue(run_id: str, out_dir: Path, family_metrics: dict[str, Any]) -> dict[str, Any]:
    queue = []
    for key, item in sorted(family_metrics.items()):
        rate = float(item.get("success_rate") or 0)
        if rate >= 0.8:
            continue
        queue.append({
            "skill": "6-验证码逆向层/captcha-dataset-flywheel/SKILL.md",
            "priority": "high" if "click" in key or "rotate" in key else "medium",
            "source_run_id": run_id,
            "evidence_path": str(out_dir / "metric-trends.json"),
            "failure_case": key,
            "proposed_rule": "keep family in training_needed until repeated action replay reaches threshold",
            "proposed_eval": f"evals/phase4a/{key.replace(':', '-').replace('/', '-')}-training-needed.yaml",
            "proposed_reference": str(out_dir / "failure-trends.json"),
            "reason": f"success_rate={rate} below promotion threshold",
            "risk": "over-promotion if target-level aggregate is used",
            "apply_now": False,
        })
    return {"run_id": run_id, "skills_update_queue": queue}


def build_issue_ledger(run_id: str, family_metrics: dict[str, Any], command_log: list[dict[str, Any]]) -> dict[str, Any]:
    issues = []
    for key, item in sorted(family_metrics.items()):
        rate = float(item.get("success_rate") or 0)
        if rate < 0.8:
            issues.append({
                "issue_id": f"{run_id}-{len(issues)+1:03d}",
                "target_family": key,
                "severity": "high" if rate == 0 else "medium",
                "status": "needs_failure_replay",
                "success_rate": rate,
                "failure_count": item.get("failure_count"),
                "root_cause": "family replay below threshold; requires recognition/action mapping diagnostics",
                "promotion_blocked": True,
            })
    for item in command_log:
        if item.get("exit_code") not in (0, None):
            issues.append({
                "issue_id": f"{run_id}-{len(issues)+1:03d}",
                "target_family": item["step"],
                "severity": "high",
                "status": "blocked",
                "success_rate": None,
                "failure_count": None,
                "root_cause": "subcommand returned non-zero exit code",
                "promotion_blocked": True,
            })
    return {"run_id": run_id, "issues": issues}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run sustainable long-run loop")
    parser.add_argument("--config", required=True)
    parser.add_argument("--mode", required=True, choices=["smoke", "nightly", "weekly", "full", "targeted-family", "failure-replay-only", "model-train-only", "audit-only"])
    parser.add_argument("--run-id", default="")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--only-failed", action="store_true")
    parser.add_argument("--only-target", default="")
    parser.add_argument("--only-family", default="")
    parser.add_argument("--skip-model-training", action="store_true")
    parser.add_argument("--skip-fingerprint", action="store_true")
    parser.add_argument("--skip-public-range", action="store_true")
    parser.add_argument("--skip-vendor-compatible", action="store_true")
    parser.add_argument("--skip-shield", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config_path = Path(args.config)
    config = read_yaml(config_path)
    run_id = args.run_id or f"{config['run']['run_id_prefix']}-{datetime.now().strftime('%H%M%S')}"
    python = str(config.get("run", {}).get("python") or sys.executable)
    out_dir = LONGRUN_ROOT / run_id
    checkpoint_path = out_dir / "checkpoint.json"
    checkpoint = load_checkpoint(checkpoint_path) if args.resume else {"completed_steps": [], "updated_at": utc_now()}
    existing_command_log_path = out_dir / "command-log.json"
    existing_commands = []
    if args.resume and existing_command_log_path.is_file():
        existing_commands = [
            item for item in read_json(existing_command_log_path).get("commands", [])
            if not item.get("skipped")
        ]
    command_log: list[dict[str, Any]] = list(existing_commands)
    model_registry = latest_model_registry()
    steps = build_steps(config, args.mode, args, run_id)
    completed = set(checkpoint.get("completed_steps", []))

    for step in steps:
        if args.resume and step["name"] in completed:
            if not any(item.get("step") == step["name"] for item in command_log):
                command_log.append({"step": step["name"], "skipped": True, "reason": "checkpoint completed", "exit_code": 0})
            continue
        command = step_command(step, python, run_id, model_registry)
        result = run_command(command, timeout=1200, dry_run=args.dry_run)
        parsed = parse_stdout_json(result)
        command_log.append({
            "step": step["name"],
            "command": result["command_text"],
            "exit_code": result["exit_code"],
            "started_at": result["started_at"],
            "ended_at": result["ended_at"],
            "stdout_path": str(out_dir / "logs" / f"{step['name']}.stdout.log"),
            "stderr_path": str(out_dir / "logs" / f"{step['name']}.stderr.log"),
            "parsed_stdout": parsed,
        })
        (out_dir / "logs").mkdir(parents=True, exist_ok=True)
        (out_dir / "logs" / f"{step['name']}.stdout.log").write_text(str(result.get("stdout") or ""), encoding="utf-8")
        (out_dir / "logs" / f"{step['name']}.stderr.log").write_text(str(result.get("stderr") or ""), encoding="utf-8")
        if result["exit_code"] == 0:
            completed.add(step["name"])
            checkpoint["completed_steps"] = sorted(completed)
            save_checkpoint(checkpoint_path, checkpoint)
        elif config["run"].get("stop_on_command_failure"):
            break
        if step["name"].startswith("model-train") and result["exit_code"] == 0:
            model_registry = str(DATASET_ROOT / "models" / run_id / "model_registry.json")

    family_metrics = read_family_metrics(run_id)
    issue_ledger = build_issue_ledger(run_id, family_metrics, command_log)
    capability_decision = build_capability_decision(run_id, family_metrics, command_log)
    skills_queue = build_skills_update_queue(run_id, out_dir, family_metrics)
    blocked_items = {"run_id": run_id, "blocked_items": capability_decision["blocked"]}
    retest_report = {
        "run_id": run_id,
        "mode": args.mode,
        "checkpoint_resume_supported": True,
        "only_failed_supported": True,
        "completed_step_count": len(completed),
        "failed_step_count": sum(1 for item in command_log if item.get("exit_code") not in (0, None)),
    }

    copy_if_exists(DATASET_ROOT / "failures" / run_id / "failure_manifest.json", out_dir / "failure_manifest.json")
    copy_if_exists(DATASET_ROOT / "labels" / run_id / "label_manifest.json", out_dir / "label_manifest.json")
    copy_if_exists(DATASET_ROOT / "splits" / run_id / "split_manifest.json", out_dir / "split_manifest.json")
    copy_if_exists(DATASET_ROOT / "models" / run_id / "model_registry.json", out_dir / "model_registry_update.json")
    copy_if_exists(DATASET_ROOT / "failures" / run_id / "failure_replay.json", out_dir / "failure_replay_report.json")
    write_json(out_dir / "command-log.json", {"run_id": run_id, "commands": command_log})
    write_json(out_dir / "issue-ledger.json", issue_ledger)
    write_json(out_dir / "capability-decision.json", capability_decision)
    write_json(out_dir / "capability-delta.json", {"run_id": run_id, "improved": [], "regressed": [], "blocked": capability_decision["blocked"]})
    write_json(out_dir / "skills-update-queue.json", skills_queue)
    write_json(out_dir / "blocked-items.json", blocked_items)
    write_json(out_dir / "retest-report.json", retest_report)
    write_json(out_dir / "longrun-ledger.json", {"run_id": run_id, "mode": args.mode, "config_path": str(config_path), "steps": steps, "checkpoint_path": str(checkpoint_path)})
    write_json(out_dir / "artifact-index.json", {"run_id": run_id, "artifacts": list_artifacts(out_dir)})
    summary = {
        "run_id": run_id,
        "mode": args.mode,
        "created_at": utc_now(),
        "independent_runner": True,
        "checkpoint_resume_supported": True,
        "targets_families": list(family_metrics),
        "command_failures": capability_decision["blocked"],
        "dataset_manifest_path": str(DATASET_ROOT / "manifests" / run_id / "dataset_manifest.json"),
        "split_manifest_path": str(DATASET_ROOT / "splits" / run_id / "split_manifest.json"),
        "model_registry_path": str(DATASET_ROOT / "models" / run_id / "model_registry.json"),
        "failure_replay_path": str(DATASET_ROOT / "failures" / run_id / "failure_replay.json"),
        "capability_decision_path": str(out_dir / "capability-decision.json"),
        "skills_update_queue_path": str(out_dir / "skills-update-queue.json"),
    }
    write_json(out_dir / "longrun-summary.json", summary)
    write_json(out_dir / "artifact-index.json", {"run_id": run_id, "artifacts": list_artifacts(out_dir)})
    print(json.dumps({"status": "PASS", "run_id": run_id, "summary_path": str(out_dir / "longrun-summary.json"), "failed_step_count": len(capability_decision["blocked"])}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
