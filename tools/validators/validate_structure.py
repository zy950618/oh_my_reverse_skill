#!/usr/bin/env python3
"""Validate the repository has a compact current skill structure.

This gate also guards public-facing documentation against stale skill-count
claims. Keep the stale phrases assembled from fragments so repository-wide
residue greps stay focused on active docs rather than the validator itself.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))
from skills_manifest import load_manifest, validate_manifest, skill_paths, layer_map

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "skills-manifest.json"
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
SOURCE_OF_TRUTH_DOCS = [
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "TRIGGERS.md",
    "USAGE.md",
    "INSTALL.md",
    "00-SKILLS索引.md",
    "STATE.md",
    "LOOP.md",
    "docs/architecture.md",
    "docs/routing.md",
    "docs/validation.md",
    "docs/scoring.md",
    "docs/cleanup-policy.md",
    "docs/evidence-policy.md",
    "docs/loop-engineering.md",
]
ACTIVE_PUBLIC_DOCS = PUBLIC_DOCS + [
    "docs/architecture.md",
    "docs/routing.md",
    "docs/validation.md",
    "docs/scoring.md",
    "docs/cleanup-policy.md",
    "docs/evidence-policy.md",
    "docs/loop-engineering.md",
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
COUNT_AUTHORITY = "skills-manifest.json"
# Intentional public-doc denylist for phase/report process terms.
PUBLIC_DOC_PHASE_RE = re.compile(r"\bphase\s*\d|\bphase\d", re.IGNORECASE)
# Intentional active skill-doc denylist for process-history blocks.
ACTIVE_SKILL_HISTORY_RE = re.compile(r"\bphase\s*\d|\bphase\d|evidence-backed phase|longrun feedback|source run_id|evidence run_id|failure evidence", re.IGNORECASE)
# Intentional public-doc denylist for unresolved lifecycle/status terms.
PUBLIC_DOC_STATE_PATTERNS = (
    "phase_",
    "current_phase",
    "next_action",
    "context_ledger",
    "run_log",
    "deprecated",
    "obsolete",
    "in_progress",
    "pending",
    "structure_only success",
    "memory_only success",
    "codex sandbox",
    "localhost socket",
)
# Intentional denylist for old score history in active release docs.
STALE_SCORE_HISTORY_PATTERNS = (
    "score history",
    "评分历史",
    "old baseline",
)
# Intentional public-doc denylist for migrated challenge residue.
PUBLIC_DOC_FORBIDDEN_RESIDUE = (
    "managed challenge",
    "交互挑战",
)
# Intentional denylist for unsafe capability claims; active docs/skills/evals must
# use observation/refusal wording instead. Validator-local occurrences are allowed.
FORBIDDEN_CAPABILITY_TERMS = (
    "spoofing",
    "stealth",
    "webdriver hiding",
    "bypass",
    "clearance reuse",
    "fake pass",
    "structure-only success",
    "反爬突破",
    "反爬虫机制识别与突破",
    "代理池",
    "user-agent 轮换",
    "cookie 池",
    "请求指纹随机化",
    "undetected-chromedriver",
    "playwright-concealment",
    "修改 navigator.webdriver",
    "打码平台",
    "超级鹰",
    "复用 cookie",
    "破 waf",
    "深度破解",
)
VALID_STANDARD_TYPES = {"external_entry", "conditional_escalation", "internal_tool", "auxiliary_policy"}
HARD_ACTIVE_COUNT_RE = re.compile(r"\b\d+\s*个\s*active\s+skill", re.IGNORECASE)
BARE_PYTHON_TOOLS_RE = re.compile(r"(?<!python3\s)(?<!python3\s\")\bpython\s+[\"']?tools[/\\]", re.IGNORECASE)
LEGACY_SCORER_RE = re.compile(r"skills-evaluation-governance[/\\]scripts[/\\]score_skills\.py")


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
            failures.append(f"{rel}: active skill inventory must point to {COUNT_AUTHORITY!r}")


def manifest_skill_files(failures: list[str]) -> list[Path]:
    try:
        manifest = load_manifest(DEFAULT_MANIFEST)
    except Exception as exc:
        failures.append(f"manifest read failed: {exc}")
        return []
    errors = validate_manifest(manifest)
    if errors:
        failures.extend(f"manifest {error}" for error in errors)
        return []
    return sorted(path / "SKILL.md" for path in skill_paths(manifest))


def manifest_layers(failures: list[str]) -> set[str]:
    try:
        manifest = load_manifest(DEFAULT_MANIFEST)
    except Exception as exc:
        failures.append(f"manifest read failed: {exc}")
        return set()
    errors = validate_manifest(manifest)
    if errors:
        failures.extend(f"manifest {error}" for error in errors)
        return set()
    return {str(item["path"]) for item in layer_map(manifest).values() if isinstance(item.get("path"), str)}


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

    install_doc = ROOT / "INSTALL.md"
    if install_doc.is_file():
        text = read_text(install_doc)
        if "skills-manifest.json" not in text or "tools/skills_manifest.py" not in text:
            failures.append("INSTALL.md: install docs must delegate active inventory to skills-manifest.json and tools/skills_manifest.py")


def validate_no_layer_count_claims(failures: list[str]) -> None:
    pattern = re.compile(r"顶层入口\(\d+ 个 skill\)|Web/JS 原子工具\(\d+ 个\)|业务流程层 \(\d+ 个\)|JS 工具层 \(\d+ 个\)", re.IGNORECASE)
    for rel in PUBLIC_DOCS:
        path = ROOT / rel
        if not path.is_file():
            continue
        for line_no, line in enumerate(read_text(path).splitlines(), 1):
            if pattern.search(line):
                failures.append(f"{rel}:{line_no}: hard-coded layer skill-count claim must delegate to score output")


def validate_public_doc_convergence(failures: list[str]) -> None:
    for rel in ACTIVE_PUBLIC_DOCS:
        path = ROOT / rel
        if not path.is_file():
            continue
        for line_no, line in enumerate(read_text(path).splitlines(), 1):
            line_lower = line.lower()
            if PUBLIC_DOC_PHASE_RE.search(line):
                failures.append(f"{rel}:{line_no}: active public doc contains phase/history marker")
            if HARD_ACTIVE_COUNT_RE.search(line):
                failures.append(f"{rel}:{line_no}: hard-coded active skill count must delegate to score output")
            if BARE_PYTHON_TOOLS_RE.search(line):
                failures.append(f"{rel}:{line_no}: use python3 for tools commands")
            if LEGACY_SCORER_RE.search(line) and "--manifest" not in line:
                failures.append(f"{rel}:{line_no}: public docs must use manifest scoring")
            for token in PUBLIC_DOC_FORBIDDEN_RESIDUE:
                if token in line_lower:
                    failures.append(f"{rel}:{line_no}: active public doc contains migrated residue token {token!r}")
                    break
            for token in PUBLIC_DOC_STATE_PATTERNS:
                if token in line_lower:
                    failures.append(f"{rel}:{line_no}: active public doc contains unresolved state token {token!r}")
                    break
            for token in FORBIDDEN_CAPABILITY_TERMS:
                if token in line_lower:
                    failures.append(f"{rel}:{line_no}: active public doc contains forbidden capability term {token!r}")
                    break


def validate_source_of_truth_docs(failures: list[str]) -> None:
    for rel in SOURCE_OF_TRUTH_DOCS:
        if not (ROOT / rel).is_file():
            failures.append(f"missing source-of-truth doc: {rel}")

    if not ((ROOT / "memory-templates").is_dir() or ((ROOT / "站点经验库" / "_templates").is_dir() and (ROOT / "逆向工程经验库" / "_templates").is_dir())):
        failures.append("missing memory templates: expected memory-templates/ or both site/reverse template directories")


def validate_loop_docs(failures: list[str]) -> None:
    loop_state = ROOT / "reports" / "loop_state"
    if loop_state.exists():
        failures.append("reports/loop_state must not be used as an active state source")

    run_log = ROOT / ".loop" / "run-log.md"
    if run_log.is_file():
        text = read_text(run_log)
        summary_count = sum(1 for line in text.splitlines() if re.match(r"\s*\d+\.\s+", line))
        if summary_count > 5:
            failures.append(f".loop/run-log.md: keep at most five recent summaries, found {summary_count}")

    state = ROOT / "STATE.md"
    if state.is_file():
        lines = [line for line in read_text(state).splitlines() if line.strip()]
        allowed_prefixes = (
            "current_branch:",
            "current_phase:",
            "current_goal:",
            "validation_status:",
            "score:",
            "minimum_active_skill_score:",
            "strict_score:",
            "codex_blocking:",
            "merge_allowed:",
            "next_action:",
        )
        for line_no, line in enumerate(lines, 1):
            if not line.startswith(allowed_prefixes):
                failures.append(f"STATE.md:{line_no}: current state only; remove long-history or changed-file detail")
                break
        if len(lines) > len(allowed_prefixes):
            failures.append(f"STATE.md: current state only; found {len(lines)} non-empty lines")


def validate_score_docs(failures: list[str]) -> None:
    score_docs = [ROOT / "docs" / "scoring.md", ROOT / "99-SKILLS治理" / "05-当前评分与回测结果.md", ROOT / ".loop" / "score-ledger.md"]
    for path in score_docs:
        if not path.is_file():
            continue
        for line_no, line in enumerate(read_text(path).splitlines(), 1):
            line_lower = line.lower()
            for token in STALE_SCORE_HISTORY_PATTERNS:
                if token in line_lower:
                    failures.append(f"{path.relative_to(ROOT).as_posix()}:{line_no}: old score history must not be part of release docs")
                    break
            if re.match(r"\s*\|\s*phase\b", line_lower):
                failures.append(f"{path.relative_to(ROOT).as_posix()}:{line_no}: old score history table must be removed")


def frontmatter(path: Path) -> dict[str, str]:
    lines = read_text(path).splitlines()
    if not lines or lines[0] != "---":
        return {}
    data: dict[str, str] = {}
    for line in lines[1:]:
        if line == "---":
            break
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip('"')
    return data


def validate_skill_types(skills: list[Path], failures: list[str]) -> None:
    for path in skills:
        data = frontmatter(path)
        name = data.get("name", path.parent.name)
        actual = data.get("standard_type")
        if actual not in VALID_STANDARD_TYPES:
            failures.append(f"{path.relative_to(ROOT).as_posix()}: standard_type must be one of {sorted(VALID_STANDARD_TYPES)}, got {actual!r}")
        for line_no, line in enumerate(read_text(path).splitlines(), 1):
            if ACTIVE_SKILL_HISTORY_RE.search(line):
                failures.append(f"{path.relative_to(ROOT).as_posix()}:{line_no}: active skill doc contains process-history phase marker")
                break
        text = read_text(path).lower()
        for token in FORBIDDEN_CAPABILITY_TERMS:
            if token in text:
                failures.append(f"{path.relative_to(ROOT).as_posix()}: forbidden capability term {token!r}")
                break


def validate_active_package_terms(skills: list[Path], failures: list[str]) -> None:
    checked_suffixes = {".md", ".yaml", ".yml"}
    checked_dirs = {"agents", "evals", "references"}
    for skill in skills:
        for path in skill.parent.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in checked_suffixes:
                continue
            rel_parts = path.relative_to(skill.parent).parts
            if path.name != "SKILL.md" and (not rel_parts or rel_parts[0] not in checked_dirs):
                continue
            text = read_text(path).lower()
            for token in FORBIDDEN_CAPABILITY_TERMS:
                if token in text:
                    failures.append(f"{path.relative_to(ROOT).as_posix()}: forbidden capability term {token!r}")
                    break


def main() -> int:
    failures: list[str] = []
    skills = manifest_skill_files(failures)
    layers = {p.relative_to(ROOT).parts[0] for p in skills}
    expected_layers = manifest_layers(failures)
    skill_names = [p.parent.name for p in skills]

    for name in sorted(FORBIDDEN_DIRS):
        if (ROOT / name).exists():
            failures.append(f"forbidden migrated directory remains: {name}")
    if expected_layers and not layers <= expected_layers:
        failures.append(f"unexpected skill layers: {sorted(layers - expected_layers)}")

    public_docs_must_delegate_count(failures)
    validate_source_of_truth_docs(failures)
    validate_no_layer_count_claims(failures)
    validate_public_doc_convergence(failures)
    validate_loop_docs(failures)
    validate_score_docs(failures)
    validate_skill_route_coverage(skill_names, failures)
    validate_skill_types(skills, failures)
    validate_active_package_terms(skills, failures)

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
