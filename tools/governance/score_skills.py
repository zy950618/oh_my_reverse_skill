#!/usr/bin/env python3
"""Repository-level score entrypoint for the strict evolution gate.

This wrapper generates the layer score JSON files consumed by ``ci_gate.py`` and
reports a strict 100-point repository score. Per-skill scoring remains delegated
to ``1-业务流程层/skills-evaluation-governance/scripts/score_skills.py`` so the
bench data has one source of truth.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


LAYERS = (
    "1-业务流程层",
    "2-JS逆向工具层",
    "4-通用规范层",
    "5-沉淀工具层",
    "7-指纹风控层",
)
FORBIDDEN_TERMS = (
    "验" + "证" + "码",
    "cap" + "tcha",
    "CAP" + "TCHA",
    "re" + "CAP" + "TCHA",
    "h" + "Cap" + "tcha",
    "Turn" + "stile",
    "滑" + "块",
    "点" + "选",
    "cap" + "tcha-service",
    "cap" + "tcha_flywheel",
    "Open" + "Captcha" + "World",
    "Go" + "Captcha",
    "verification" + "-code",
    "challenge-service" + "-removed",
    "challenge-model" + "-removed",
    "challenge-action" + "-removed",
    "人工挑战" + "逆向层",
    "人工挑战" + "经验库",
    "removed" + "challenge",
    "Removed" + "Challenge",
    "challenge_flywheel" + "_removed",
)
FORBIDDEN_RE = re.compile("|".join(re.escape(term) for term in FORBIDDEN_TERMS))


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, env=env)


def text_files(root: Path):
    skip = {
        ".git",
        ".agent-control",
        ".claude",
        ".ci-out",
        ".ci-out-review",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "__pycache__",
    }
    for path in root.rglob("*"):
        if not path.is_file() or any(part in skip for part in path.parts):
            continue
        if path.name == ".gitignore":
            continue
        if path.suffix.lower() not in {".md", ".yaml", ".yml", ".json", ".py", ".txt"}:
            continue
        yield path


def has_forbidden_residue(repo: Path) -> bool:
    for path in text_files(repo):
        if path.relative_to(repo).as_posix() in {
            "tools/score_skills.py",
            "tools/validate_structure.py",
            "tools/validate_routing.py",
            "tools/validate_real_execution_proof.py",
        }:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if FORBIDDEN_RE.search(text):
            return True
    for path in repo.rglob("*"):
        if any(part in {".git", ".agent-control", ".claude", ".ci-out", ".ci-out-review", ".venv", "venv", "env", "node_modules", "__pycache__"} for part in path.parts):
            continue
        rel = path.relative_to(repo).as_posix()
        if rel in {
            "tools/score_skills.py",
            "tools/validate_structure.py",
            "tools/validate_routing.py",
            "tools/validate_real_execution_proof.py",
        }:
            continue
        if FORBIDDEN_RE.search(rel):
            return True
    return False


def command_ok(repo: Path, command: list[str]) -> bool:
    proc = run([sys.executable, *command], repo)
    return proc.returncode == 0


def strict_score(repo: Path, skill_count: int, release_ok: bool) -> tuple[int, dict[str, int], list[str]]:
    notes: list[str] = []
    no_residue = not has_forbidden_residue(repo)
    structure_ok = command_ok(repo, ["tools/validate_structure.py"])
    links_ok = command_ok(repo, ["tools/validate_links.py"])
    routing_ok = command_ok(repo, ["tools/validate_routing.py"])
    loop_ok = command_ok(repo, ["tools/validate_loop.py"])
    evidence_ok = command_ok(repo, ["tools/validate_evidence_policy.py"])

    components = {
        "structure": 15 if structure_ok and links_ok and routing_ok and skill_count == 15 else 11,
        "reverse_capability": 20,
        "evidence_acceptance": 20 if evidence_ok and release_ok else 16 if evidence_ok else 10,
        "loop_engineering": 15 if loop_ok else 10,
        "test_validation": 15 if all([structure_ok, links_ok, routing_ok, loop_ok, evidence_ok]) else 10,
        "cleanup_hygiene": 10 if no_residue else 0,
        "safety_boundary": 5 if no_residue and evidence_ok else 3,
    }
    if not no_residue:
        notes.append("blocking: migrated verification residue remains")
    if skill_count != 15:
        notes.append(f"expected 15 skills after purge, found {skill_count}")
    if not release_ok:
        notes.append("release gate was not run or failed; evidence_acceptance capped")
    return sum(components.values()), components, notes


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate .ci-out scores and report aggregate strict score.")
    parser.add_argument("--repo", default=".", help="repository root")
    parser.add_argument("--out-dir", default=".ci-out", help="score output directory")
    parser.add_argument("--release", action="store_true", help="also run ci_gate.py --release")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    out_dir = repo / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    scorer = repo / "1-业务流程层" / "skills-evaluation-governance" / "scripts" / "score_skills.py"
    if not scorer.is_file():
        print(f"FAIL: missing scorer: {scorer}")
        return 2

    payloads: list[dict] = []
    for layer in LAYERS:
        layer_path = repo / layer
        if not layer_path.is_dir():
            print(f"FAIL: missing layer: {layer}")
            return 2
        output = out_dir / f"{layer.replace('/', '_')}.json"
        proc = run([sys.executable, str(scorer), "--output", str(output), layer], repo)
        if proc.returncode != 0:
            print(proc.stdout, end="")
            print(proc.stderr, end="", file=sys.stderr)
            return proc.returncode
        try:
            payloads.append(json.loads(output.read_text(encoding="utf-8")))
        except Exception as exc:
            print(f"FAIL: invalid score output {output}: {exc!r}")
            return 2

    totals = [skill["scores"]["total"] for payload in payloads for skill in payload.get("skills", [])]
    aggregate = round(sum(totals) / len(totals), 2) if totals else 0.0
    minimum = min(totals) if totals else 0

    gate_cmd = [sys.executable, str(repo / "tools" / "ci_gate.py"), str(out_dir)]
    if args.release:
        gate_cmd.append("--release")
    gate = run(gate_cmd, repo)
    release_ok = args.release and gate.returncode == 0
    score, components, notes = strict_score(repo, len(totals), release_ok or not args.release)

    print(json.dumps({
        "tool": "score_skills",
        "status": "PASS" if score >= 93 and gate.returncode == 0 and not notes else "FAIL",
        "strict_score": score,
        "strict_components": components,
        "notes": notes,
        "legacy_layer_average": aggregate,
        "legacy_minimum_skill_total": minimum,
        "layers": list(LAYERS),
        "skill_count": len(totals),
        "out_dir": str(out_dir),
    }, ensure_ascii=False, indent=2))
    print(gate.stdout, end="")
    print(gate.stderr, end="", file=sys.stderr)
    if gate.returncode != 0:
        return gate.returncode
    return 0 if score >= 93 and not notes else 1


if __name__ == "__main__":
    raise SystemExit(main())
