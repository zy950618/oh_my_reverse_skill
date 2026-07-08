#!/usr/bin/env python3
"""Validate evidence-policy guardrails for the current repository."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = [
    "99-SKILLS治理/11-AI事实证据规约.md",
    "99-SKILLS治理/12-反泛化与任务收敛规约.md",
    "99-SKILLS治理/13-并发指纹与会话隔离规约.md",
    "99-SKILLS治理/16-实战复测与证据新鲜度规约.md",
]
FORBIDDEN = ("token/cookie 复用教程", "webdriver 隐藏能力宣传", "未授权绕过宣传")
RESIDUE_ROOTS = (
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "TRIGGERS.md",
    "INSTALL.md",
    "USAGE.md",
    "00-SKILLS索引.md",
    "1-业务流程层",
    "2-JS逆向工具层",
    "7-指纹风控层",
    "configs",
    "docs",
    "evals",
    "skills-experience",
    "tools",
    "datasets",
    "public-range-evidence",
)
RESIDUE_PATTERNS = (
    "phase3-12",
    "183000-phase3-12",
    "model-flywheel",
    "anti-solver",
    "visual_solver",
    "visual solver",
    "action planner",
    "blackbox_solver",
    "challenge_solver_training",
    "public_range_solver_positive",
    "remote solver",
    "third-party solver",
    "verified vendor solver",
    "action_replay",
    "blackbox_gate",
    "compatible-lab",
    "shumei-compatible",
    "aliyun-compatible",
    "solver_token_reuse",
)
SKIP_PARTS = {".git", ".agent-control", ".ci-out", "node_modules", "__pycache__"}
TEXT_SUFFIXES = {".md", ".py", ".yaml", ".yml", ".json", ".txt"}


def iter_residue_files() -> list[Path]:
    paths: list[Path] = []
    for rel in RESIDUE_ROOTS:
        base = ROOT / rel
        if not base.exists():
            continue
        if base.is_file():
            paths.append(base)
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            if path.resolve() == Path(__file__).resolve():
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            paths.append(path)
    return paths


def main() -> int:
    failures: list[str] = []
    corpus = []
    for rel in REQUIRED:
        path = ROOT / rel
        if not path.is_file():
            failures.append(f"missing evidence policy file: {rel}")
            continue
        corpus.append(path.read_text(encoding="utf-8-sig", errors="replace"))
    joined = "\n".join(corpus)
    for token in ("observed", "derived", "assumed", "unverified", "positive_allowed", "direct interface"):
        if token not in joined:
            failures.append(f"missing evidence token: {token}")
    for token in FORBIDDEN:
        if token in joined:
            failures.append(f"forbidden unsafe policy phrase remains: {token}")

    for path in iter_residue_files():
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        lowered = text.lower()
        for pattern in RESIDUE_PATTERNS:
            if pattern.lower() in lowered:
                failures.append(f"migrated verification/solver residue {pattern!r} remains in {path.relative_to(ROOT).as_posix()}")
                break

    payload = {"tool": "validate_evidence_policy", "status": "PASS" if not failures else "FAIL", "failures": failures[:80]}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
