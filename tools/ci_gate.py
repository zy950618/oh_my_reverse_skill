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
import subprocess
import sys
from pathlib import Path

LAYER_MIN = {
    "1-业务流程层": 70,
    "2-JS逆向工具层": 15,
    "4-通用规范层": 15,
    "5-沉淀工具层": 70,
    "6-验证码逆向层": 70,
}

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
    replay_failures = []

    for json_path in sorted(out_dir.glob("*.json")):
        layer = layer_from_filename(json_path.name)
        threshold = LAYER_MIN.get(layer)
        if threshold is None:
            if json_path.name == "scores-current.json":
                continue
            print(f"WARN: 未知层 {layer}, 跳过")
            continue
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        consistency_by_domain = data.get("consistency_by_domain", {})
        for skill in data.get("skills", []):
            total, total_notes = structure_total(skill, data, threshold, args.release)
            raw_total = skill["scores"]["total"]
            name = skill["skill"]
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

    public_range_ok, public_range_output = run_public_range_evidence_gate(out_dir)
    print("\nPublic range evidence hard gate:")
    print(public_range_output)
    if not public_range_ok:
        print(f"\n{'!' * 70}")
        print("CI Gate failed: public range evidence freshness/acceptance/repeat hard gate did not pass")
        print(f"{'!' * 70}")
        sys.exit(1)

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
        print(f"\nStructure Gate 通过: {len(passed)} 个 skill 达标；release 前必须另跑 `python tools/ci_gate.py {out_dir} --release`")
    sys.exit(0)


if __name__ == "__main__":
    main()
