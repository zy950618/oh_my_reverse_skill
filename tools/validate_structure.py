#!/usr/bin/env python3
"""Validate the repository has a compact current skill structure.

This gate also guards public-facing documentation against stale skill-count
claims. Keep the stale phrases assembled from fragments so repository-wide
residue greps stay focused on active docs rather than the validator itself.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_LAYERS = {
    "1-业务流程层",
    "2-JS逆向工具层",
    "4-通用规范层",
    "5-沉淀工具层",
    "7-指纹风控层",
}
FORBIDDEN_DIRS = {
    "6-" + "验" + "证" + "码" + "逆向层",
    "验" + "证" + "码" + "经验库",
    "6-" + "人工挑战" + "逆向层",
    "人工挑战" + "经验库",
}
PUBLIC_DOCS = [
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "TRIGGERS.md",
    "INSTALL.md",
    "USAGE.md",
    "00-SKILLS索引.md",
]
# Intentional denylist for stale public skill-count claims. Build the phrases from
# fragments so the repository-wide residue grep does not flag this validator.
STALE_COUNT_PATTERNS = (
    "12" + " 个 " + "skill",
    "12" + " 个 " + "Skill",
    "12" + " 个 " + "SKILL",
    "全部 " + "12",
    "23" + " 个 " + "active",
)
COUNT_AUTHORITY = "python3 tools/score_skills.py --repo ."


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def line_hits(path: Path, patterns: tuple[str, ...]) -> list[str]:
    hits: list[str] = []
    text = read_text(path)
    lowered = text.lower()
    for pattern in patterns:
        target = pattern.lower()
        if target not in lowered:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            if target in line.lower():
                hits.append(f"{path.relative_to(ROOT).as_posix()}:{line_no}: stale skill-count claim {pattern!r}")
    return hits


def public_docs_must_delegate_count(failures: list[str]) -> None:
    for rel in PUBLIC_DOCS:
        path = ROOT / rel
        if not path.is_file():
            failures.append(f"missing public routing doc: {rel}")
            continue
        failures.extend(line_hits(path, STALE_COUNT_PATTERNS))

    score_doc = ROOT / "99-SKILLS治理" / "05-当前评分与回测结果.md"
    if score_doc.is_file():
        failures.extend(line_hits(score_doc, STALE_COUNT_PATTERNS))

    for rel in ("README.md", "USAGE.md", "INSTALL.md", "AGENTS.md", "00-SKILLS索引.md"):
        path = ROOT / rel
        if path.is_file() and COUNT_AUTHORITY not in read_text(path):
            failures.append(f"{rel}: active skill count must point to {COUNT_AUTHORITY!r}")


def skill_files() -> list[Path]:
    skip = {".git", ".agent-control", ".claude", ".ci-out", ".venv", "node_modules", "__pycache__"}
    return sorted(p for p in ROOT.rglob("SKILL.md") if not any(part in skip for part in p.parts))


def validate_skill_route_coverage(skill_names: list[str], failures: list[str]) -> None:
    index = ROOT / "00-SKILLS索引.md"
    triggers = ROOT / "TRIGGERS.md"
    for route_doc in (index, triggers):
        if not route_doc.is_file():
            continue
        text = read_text(route_doc)
        missing = [name for name in skill_names if name not in text]
        if missing:
            failures.append(f"{route_doc.relative_to(ROOT).as_posix()}: missing active skill route entries: {missing}")

    for install_doc in (ROOT / "README.md", ROOT / "INSTALL.md"):
        if not install_doc.is_file():
            continue
        text = read_text(install_doc)
        missing = [name for name in skill_names if name not in text]
        if missing:
            failures.append(f"{install_doc.relative_to(ROOT).as_posix()}: install docs missing active skill links: {missing}")


def validate_no_layer_count_claims(failures: list[str]) -> None:
    pattern = re.compile(r"顶层入口\(\d+ 个 skill\)|Web/JS 原子工具\(\d+ 个\)|业务流程层 \(\d+ 个\)|JS 工具层 \(\d+ 个\)", re.IGNORECASE)
    for rel in PUBLIC_DOCS:
        path = ROOT / rel
        if not path.is_file():
            continue
        for line_no, line in enumerate(read_text(path).splitlines(), 1):
            if pattern.search(line):
                failures.append(f"{rel}:{line_no}: hard-coded layer skill-count claim must delegate to score output")


def main() -> int:
    skills = skill_files()
    layers = {p.relative_to(ROOT).parts[0] for p in skills}
    skill_names = [p.parent.name for p in skills]
    failures: list[str] = []

    for name in sorted(FORBIDDEN_DIRS):
        if (ROOT / name).exists():
            failures.append(f"forbidden migrated directory remains: {name}")
    if not layers <= EXPECTED_LAYERS:
        failures.append(f"unexpected skill layers: {sorted(layers - EXPECTED_LAYERS)}")
    if len(skills) != 15:
        failures.append(f"expected current release gate skill count 15, found {len(skills)}")

    public_docs_must_delegate_count(failures)
    validate_no_layer_count_claims(failures)
    validate_skill_route_coverage(skill_names, failures)

    payload = {
        "tool": "validate_structure",
        "status": "PASS" if not failures else "FAIL",
        "skill_count": len(skills),
        "count_authority": COUNT_AUTHORITY,
        "layers": sorted(layers),
        "skill_names": skill_names,
        "failures": failures[:120],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
