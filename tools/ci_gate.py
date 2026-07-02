#!/usr/bin/env python3
"""
ci_gate.py — 按"层"设阈值，读取 .ci-out/*.json，任何 skill 低于其层阈值则 exit 1。

为什么按层不按统一阈值？
- 业务流程层 (1-) / 沉淀工具层 (5-) 是 package skill，含 SKILL.md + evals + references + agents
  → 高阈值 (70)
- 原子工具层 (2- / 4-) 是 atom/foundation skill，只有 SKILL.md 也可以有效
  → 低阈值 (15)，主要确保 SKILL.md 还在 + frontmatter 完整

这是 v1 baseline。后续随 skill 演化可调高阈值。

用法:
  python tools/ci_gate.py .ci-out
  python tools/ci_gate.py .ci-out --release
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

from skill_score_config import load_skill_score_config


REPO_ROOT = Path(__file__).resolve().parent.parent
SCORE_CONFIG = load_skill_score_config(REPO_ROOT)
LAYER_MIN = SCORE_CONFIG["layer_thresholds"]
LAYER_GATE_MODES = SCORE_CONFIG["layer_gate_modes"]

MIN_REPLAY_RATE = 0.90  # 任何 skill 的 applicable_domains 中若有 latest_rate < 0.90 则 fail


def structure_total(skill: dict, data: dict, threshold: int, release: bool) -> tuple[int, list[str]]:
    total = skill["scores"]["total"]
    if release:
        return total, []
    if threshold < 70:
        return total, []

    consistency_score = skill["scores"].get("consistency", 0)
    consistency_by_domain = data.get("consistency_by_domain") or {}
    if consistency_score == 0 and not consistency_by_domain:
        return total + 20, ["private site-memory consistency excluded from structure gate"]
    return total, []


def run_web_h5_crawler_gate(out_dir: Path) -> tuple[bool, str]:
    repo_root = out_dir.resolve().parent
    script = repo_root / "tools" / "validate_web_h5_crawler_gate.py"
    if not script.is_file():
        return False, f"ERROR: 缺少 Web/H5 crawler gate 脚本: {script}"

    result = subprocess.run(
        [sys.executable, str(script), "--repo-root", str(repo_root)],
        cwd=str(repo_root),
        text=True,
        capture_output=True,
    )
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0, output.strip()


def run_web_h5_loop_gate(out_dir: Path) -> tuple[bool, str]:
    repo_root = out_dir.resolve().parent
    script = repo_root / "tools" / "validate_web_h5_loop_gate.py"
    if not script.is_file():
        return False, f"ERROR: 缺少 Web/H5 loop gate 脚本: {script}"

    result = subprocess.run(
        [sys.executable, str(script), "--repo-root", str(repo_root)],
        cwd=str(repo_root),
        text=True,
        capture_output=True,
    )
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0, output.strip()


def run_web_h5_real_execution_gate(out_dir: Path) -> tuple[bool, str]:
    repo_root = out_dir.resolve().parent
    script = repo_root / "tools" / "validate_web_h5_real_execution_gate.py"
    if not script.is_file():
        return False, f"ERROR: 缺少 Web/H5 real execution gate 脚本: {script}"

    result = subprocess.run(
        [sys.executable, str(script), "--repo-root", str(repo_root)],
        cwd=str(repo_root),
        text=True,
        capture_output=True,
    )
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0, output.strip()


def run_public_range_evidence_gate(out_dir: Path) -> tuple[bool, str]:
    repo_root = out_dir.resolve().parent
    script = repo_root / "tools" / "validate_public_range_evidence.py"
    if not script.is_file():
        return False, f"ERROR: missing public range evidence gate script: {script}"

    result = subprocess.run(
        [sys.executable, str(script), "--repo-root", str(repo_root)],
        cwd=str(repo_root),
        text=True,
        capture_output=True,
    )
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0, output.strip()


def run_real_execution_proof_gate(out_dir: Path) -> tuple[bool, str]:
    repo_root = out_dir.resolve().parent
    script = repo_root / "tools" / "validate_real_execution_proof.py"
    if not script.is_file():
        return False, f"ERROR: missing real execution proof gate script: {script}"

    result = subprocess.run(
        [sys.executable, str(script), "--repo-root", str(repo_root)],
        cwd=str(repo_root),
        text=True,
        capture_output=True,
    )
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0, output.strip()


def run_business_data_gate(out_dir: Path) -> tuple[bool, str]:
    repo_root = out_dir.resolve().parent
    script = repo_root / "tools" / "validate_business_data_assertions.py"
    if not script.is_file():
        return False, f"ERROR: missing business data assertion gate script: {script}"

    result = subprocess.run(
        [sys.executable, str(script), "--repo-root", str(repo_root)],
        cwd=str(repo_root),
        text=True,
        capture_output=True,
    )
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0, output.strip()


def run_scope_contract_gate(out_dir: Path) -> tuple[bool, str]:
    repo_root = out_dir.resolve().parent
    script = repo_root / "tools" / "validate_scope_contract.py"
    config = repo_root / "configs" / "range_scope_contract.yaml"
    if not script.is_file():
        return False, f"ERROR: missing scope contract gate script: {script}"
    if not config.is_file():
        return False, f"ERROR: missing scope contract config: {config}"

    result = subprocess.run(
        [sys.executable, str(script), "--config", str(config), "--repo-root", str(repo_root)],
        cwd=str(repo_root),
        text=True,
        capture_output=True,
    )
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0, output.strip()


def run_repo_command(out_dir: Path, command: list[str]) -> tuple[bool, str]:
    repo_root = out_dir.resolve().parent
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, *command],
        cwd=str(repo_root),
        env=env,
        text=True,
        capture_output=True,
    )
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0, output.strip()


def run_second_loop_release_gates(out_dir: Path) -> tuple[bool, str]:
    checks = [
        ("pure_api_lab", ["tools/validate_pure_api_delivery.py", "public-range-evidence/pure-api-lab"]),
        ("airline_pure_api_lab", ["tools/validate_pure_api_delivery.py", "public-range-evidence/airline-lab-order-flow"]),
        ("captcha_action_schema", ["tools/validate_captcha_action_schema.py"]),
        ("captcha_dataset", ["tools/validate_captcha_dataset.py"]),
        ("captcha_training_report", ["tools/validate_captcha_training_report.py"]),
        ("captcha_model_package", ["tools/validate_captcha_model_package.py"]),
        ("captcha_pass_rate", ["tools/validate_captcha_pass_rate.py"]),
        ("captcha_sample_infer", ["public-range-evidence/captcha-model-lab/inference/sample_infer.py"]),
        ("captcha_evaluate_pass_rate", ["public-range-evidence/captcha-model-lab/eval/evaluate_pass_rate.py"]),
        ("fingerprint_surface_lab", ["tools/validate_fingerprint_surface_lab.py"]),
        ("block_reason_lab", ["tools/validate_block_reason_lab.py"]),
        ("browser_context_isolation", ["tools/validate_browser_context_isolation.py"]),
        ("captcha_fingerprint_linkage", ["tools/validate_captcha_fingerprint_linkage.py"]),
        ("real_site_observation_pack", ["tools/validate_real_site_observation_pack.py", "public-range-evidence/real-site-observation-pack"]),
        ("airline_replay", ["public-range-evidence/airline-lab-order-flow/replay/replay.py"]),
        ("airline_deep_validation", ["public-range-evidence/airline-lab-order-flow/tests/run_order_flow_tests.py"]),
        ("cleanup_check", ["tools/cleanup_workspace.py", "--check"]),
    ]
    failures: list[str] = []
    lines: list[str] = []
    for label, command in checks:
        ok, output = run_repo_command(out_dir, command)
        status = "PASS" if ok else "FAIL"
        lines.append(f"{label}: {status}")
        if output:
            lines.append(output)
        if not ok:
            failures.append(label)
    if failures:
        lines.append(f"second_loop_release_failures={failures}")
    return not failures, "\n".join(lines)


def parse_gate_json(output: str) -> dict:
    start = output.find("{")
    end = output.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    try:
        payload = json.loads(output[start:end + 1])
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def run_fixture_freshness_report(out_dir: Path, strict_fresh: bool = False) -> tuple[bool, str]:
    repo_root = out_dir.resolve().parent
    script = repo_root / "tools" / "fixture_freshness_report.py"
    if not script.is_file():
        return False, f"ERROR: 缺少 fixture freshness report 脚本: {script}"

    command = [sys.executable, str(script), "站点经验库"]
    if strict_fresh:
        command.append("--strict-fresh")

    result = subprocess.run(
        command,
        cwd=str(repo_root),
        text=True,
        capture_output=True,
    )
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0, output.strip()


def layer_from_filename(name: str) -> str:
    # ".ci-out/1-业务流程层.json"  →  "1-业务流程层"
    return Path(name).stem.replace("_", "/")


def main():
    parser = argparse.ArgumentParser(description="Layer-aware SKILLS gate")
    parser.add_argument("out_dir", help=".ci-out directory")
    parser.add_argument(
        "--release",
        action="store_true",
        help="enforce release gates, including fixture_freshness_report.py --strict-fresh",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    if not out_dir.is_dir():
        print(f"ERROR: 目录不存在 {out_dir}", file=sys.stderr)
        sys.exit(2)

    failures = []
    passed = []
    advisory = []
    replay_failures = []

    for json_path in sorted(out_dir.glob("*.json")):
        layer = layer_from_filename(json_path.name)
        threshold = LAYER_MIN.get(layer)
        if threshold is None:
            if json_path.name == "scores-current.json":
                continue
            print(f"WARN: 未知层 {layer}, 跳过")
            continue
        gate_mode = LAYER_GATE_MODES.get(layer, "active")
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        consistency_by_domain = data.get("consistency_by_domain", {})
        for skill in data.get("skills", []):
            total, total_notes = structure_total(skill, data, threshold, args.release)
            raw_total = skill["scores"]["total"]
            name = skill["skill"]
            if gate_mode in {"advisory", "experimental", "excluded"}:
                advisory.append((layer, name, raw_total, total, threshold, gate_mode, total_notes))
                continue
            if total < threshold:
                failures.append((layer, name, raw_total, total, threshold, skill.get("gaps", []), total_notes))
            else:
                passed.append((layer, name, raw_total, total, threshold, total_notes))

            # replay rate 检查
            for domain in skill.get("applicable_domains") or []:
                dom_info = consistency_by_domain.get(domain)
                if not dom_info:
                    continue
                rate = dom_info.get("latest_rate")
                if rate is None:
                    continue
                if rate < MIN_REPLAY_RATE:
                    replay_failures.append((layer, name, domain, rate, MIN_REPLAY_RATE))

    print("=" * 70)
    gate_name = "Skill Bench Release Gate" if args.release else "Skill Bench Structure Gate"
    print(gate_name + " - layer-aware thresholds")
    print("=" * 70)
    print(f"\n通过 ({len(passed)}):")
    for layer, name, raw_total, total, threshold, notes in passed:
        suffix = f" effective={total:3d}" if total != raw_total else ""
        print(f"  PASS  {layer:25s} {name:40s} {raw_total:3d} / {threshold}{suffix}")
        for note in notes:
            print(f"        - {note}")

    if advisory:
        print(f"\n纳入但不作为 active gate ({len(advisory)}):")
        for layer, name, raw_total, total, threshold, mode, notes in advisory:
            suffix = f" effective={total:3d}" if total != raw_total else ""
            print(f"  {mode.upper():8s} {layer:25s} {name:40s} {raw_total:3d} / {threshold}{suffix}")
            for note in notes:
                print(f"        - {note}")

    if failures:
        print(f"\n失败 ({len(failures)}):")
        for layer, name, raw_total, total, threshold, gaps, notes in failures:
            suffix = f" effective={total:3d}" if total != raw_total else ""
            print(f"  FAIL  {layer:25s} {name:40s} {raw_total:3d} / {threshold}{suffix}")
            for note in notes:
                print(f"        - {note}")
            for gap in gaps[:3]:
                print(f"        - {gap}")
        print(f"\n{'!' * 70}")
        print(f"CI Gate 失败: {len(failures)} 个 skill 低于其所在层阈值")
        print(f"{'!' * 70}")
        sys.exit(1)

    if replay_failures:
        print(f"\nReplay Rate 失败 ({len(replay_failures)}):")
        for layer, name, domain, rate, min_rate in replay_failures:
            print(f"  FAIL  {layer:25s} {name:40s} {domain:25s} rate={rate:.4f} < {min_rate}")
        print(f"\n{'!' * 70}")
        print(f"CI Gate 失败: {len(replay_failures)} 个 (skill, domain) 重放率低于 {MIN_REPLAY_RATE}")
        print(f"{'!' * 70}")
        sys.exit(1)

    crawler_gate_ok, crawler_gate_output = run_web_h5_crawler_gate(out_dir)
    print("\nWeb/H5 crawler hardening gate:")
    print(crawler_gate_output)
    if not crawler_gate_ok:
        print(f"\n{'!' * 70}")
        print("CI Gate 失败: Web/H5 crawler hardening gate 未通过")
        print(f"{'!' * 70}")
        sys.exit(1)

    loop_gate_ok, loop_gate_output = run_web_h5_loop_gate(out_dir)
    print("\nWeb/H5 loop engineering gate:")
    print(loop_gate_output)
    if not loop_gate_ok:
        print(f"\n{'!' * 70}")
        print("CI Gate 失败: Web/H5 loop engineering gate 未通过")
        print(f"{'!' * 70}")
        sys.exit(1)

    real_execution_gate_ok, real_execution_gate_output = run_web_h5_real_execution_gate(out_dir)
    print("\nWeb/H5 real execution gate:")
    print(real_execution_gate_output)
    if not real_execution_gate_ok:
        print(f"\n{'!' * 70}")
        print("CI Gate 失败: Web/H5 real execution gate 未通过")
        print(f"{'!' * 70}")
        sys.exit(1)

    if args.release:
        public_range_ok, public_range_output = run_public_range_evidence_gate(out_dir)
        print("\nPublic range evidence hard gate:")
        print(public_range_output)
        if not public_range_ok:
            print(f"\n{'!' * 70}")
            print("CI Gate failed: public range evidence freshness/acceptance/repeat hard gate did not pass")
            print(f"{'!' * 70}")
            sys.exit(1)
        public_range_payload = parse_gate_json(public_range_output)

        real_execution_ok, real_execution_output = run_real_execution_proof_gate(out_dir)
        print("\nReal execution proof gate:")
        print(real_execution_output)
        if not real_execution_ok:
            print(f"\n{'!' * 70}")
            print("CI Gate failed: real execution proof gate found invalid execution evidence")
            print(f"{'!' * 70}")
            sys.exit(1)
        real_execution_payload = parse_gate_json(real_execution_output)
        business_data_ok, business_data_output = run_business_data_gate(out_dir)
        print("\nBusiness data assertion gate:")
        print(business_data_output)
        if not business_data_ok:
            print(f"\n{'!' * 70}")
            print("CI Gate failed: business data assertions did not pass")
            print(f"{'!' * 70}")
            sys.exit(1)
        business_data_payload = parse_gate_json(business_data_output)

        scope_contract_ok, scope_contract_output = run_scope_contract_gate(out_dir)
        print("\nScope contract gate:")
        print(scope_contract_output)
        if not scope_contract_ok:
            print(f"\n{'!' * 70}")
            print("CI Gate failed: scope contract did not pass")
            print(f"{'!' * 70}")
            sys.exit(1)

        second_loop_ok, second_loop_output = run_second_loop_release_gates(out_dir)
        print("\nSecond LOOP release gates:")
        print(second_loop_output)
        if not second_loop_ok:
            print(f"\n{'!' * 70}")
            print("CI Gate failed: second LOOP release checks did not pass")
            print(f"{'!' * 70}")
            sys.exit(1)

        print("\nFour-layer gate summary:")
        print("  execution gate: validate_real_execution_proof.py")
        print("  control-flow gate: validate_public_range_evidence.py control_flow_status")
        print("  business-data gate: validate_business_data_assertions.py")
        print("  capability gate: positive_allowed only after execution/control-flow plus either business-data pass or scope-limited solver/diagnostics gates")
        print(
            "  REAL_EXECUTION_PASS files are execution proof only; positive capability is counted only by "
            "capability_status=positive_allowed after public-range, scope-contract, and applicable hard gates."
        )
        print(f"  real_execution_pass_count={real_execution_payload.get('real_execution_pass_count', 'unknown')}")
        print(f"  control_flow_counts={real_execution_payload.get('control_flow_counts', {})}")
        print(f"  business_data_pass_count={business_data_payload.get('business_data_pass_count', 'unknown')}")
        print(f"  total_positive_count={public_range_payload.get('total_positive_count', 'unknown')}")
        print(f"  positive_allowed_count={public_range_payload.get('positive_allowed_count', 'unknown')}")
        print(f"  positive_candidate_count={public_range_payload.get('positive_candidate_count', 'unknown')}")
        print(f"  positive_verified_count={public_range_payload.get('positive_verified_count', 'unknown')}")
        print(f"  stable_positive_count={public_range_payload.get('stable_positive_count', 'unknown')}")
        print(f"  negative_eval_only_count={real_execution_payload.get('negative_eval_only_count', 'unknown')}")
    else:
        print("\nRelease-only evidence gates: SKIPPED in default structure gate")
        print("  skipped: validate_public_range_evidence.py")
        print("  skipped: validate_real_execution_proof.py")
        print("  skipped: validate_business_data_assertions.py")
        print("  skipped: validate_scope_contract.py")
        print("  run with --release to enforce public-range, execution-proof, business-data, scope-contract, and strict freshness gates")

    freshness_ok, freshness_output = run_fixture_freshness_report(out_dir, strict_fresh=args.release)
    freshness_label = "strict release gate" if args.release else "report-only for historical fixtures"
    print(f"\nFixture freshness report ({freshness_label}):")
    print(freshness_output)
    if not freshness_ok:
        print(f"\n{'!' * 70}")
        if args.release:
            print("Release Gate 失败: fixture freshness strict check 未通过")
        else:
            print("CI Gate 失败: fixture freshness report 无法运行")
        print(f"{'!' * 70}")
        sys.exit(1)

    if args.release:
        print(f"\nRelease Gate 通过: {len(passed)} 个 skill 达标且 strict freshness 通过")
    else:
        print(
            f"\nStructure Gate 通过: {len(passed)} 个 active skill 达标；"
            f"{len(advisory)} 个 advisory/experimental/excluded skill 已纳入报告但不计 active gate；"
            f"release 前必须另跑 `python tools/ci_gate.py {out_dir} --release`"
        )
    sys.exit(0)


if __name__ == "__main__":
    main()
