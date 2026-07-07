#!/usr/bin/env python3
"""Validate current public routing sources exclude migrated challenge routes."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Intentional denylist for migrated verification/challenge residue. Tokens are
# assembled from fragments so the repository-wide residue grep does not flag the
# validator itself; active docs and routing files must not contain these terms.
FORBIDDEN = (
    "cap" + "tcha",
    "CAP" + "TCHA",
    "验" + "证" + "码",
    "re" + "CAP" + "TCHA",
    "h" + "Cap" + "tcha",
    "Turn" + "stile",
    "滑" + "块",
    "点" + "选",
    "cap" + "tcha-service",
    "cap" + "tcha_flywheel",
    "Open" + "Captcha" + "World",
    "Go" + "Captcha",
    "challenge-service" + "-removed",
    "challenge-model" + "-removed",
    "challenge-action" + "-removed",
    "人工挑战" + "逆向层",
    "人工挑战" + "经验库",
    "removed" + "challenge",
)
STALE_COUNT = (
    "12" + " 个 " + "skill",
    "12" + " 个 " + "Skill",
    "12" + " 个 " + "SKILL",
    "全部 " + "12",
    "23" + " 个 " + "active",
)
ROUTING_FILES = ["README.md", "AGENTS.md", "TRIGGERS.md", "INSTALL.md", "USAGE.md", "00-SKILLS索引.md", "CLAUDE.md"]
EXPECTED_EXTERNAL = {
    "website-314-api-delivery",
    "reverse-js-crawler",
    "web-h5-loop-engineering",
    "skills-evaluation-governance",
}
EXPECTED_CONDITIONAL = {
    "imperva-waf-reese84",
    "authorized-target-adapter",
    "site-api-adapter",
}
EXPECTED_INTERNAL_OR_AUX = {
    "find-crypto-entry",
    "ast-deobfuscate",
    "env-patch",
    "js-page-runtime-parity",
    "ai-reverse-skill-creator",
    "karpathy-guidelines",
    "browser-fingerprint-surface-lab",
    "fingerprint-block-reason-diagnostics",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def check_tokens(rel: str, text: str, failures: list[str]) -> None:
    lowered = text.lower()
    for line_no, line in enumerate(text.splitlines(), 1):
        line_lower = line.lower()
        for token in FORBIDDEN:
            if token.lower() in line_lower:
                failures.append(f"{rel}:{line_no}: forbidden migrated routing token {token!r}")
                break
        for token in STALE_COUNT:
            if token.lower() in line_lower:
                failures.append(f"{rel}:{line_no}: stale skill-count routing token {token!r}")
                break
    if "current active count is 15" in lowered and "python3 tools/score_skills.py --repo ." not in text:
        failures.append(f"{rel}: hard-coded active count lacks score_skills authority")


def check_route_contract(failures: list[str]) -> None:
    index = ROOT / "00-SKILLS索引.md"
    triggers = ROOT / "TRIGGERS.md"
    if not index.is_file() or not triggers.is_file():
        return
    index_text = read_text(index)
    triggers_text = read_text(triggers)
    for name in sorted(EXPECTED_EXTERNAL | EXPECTED_CONDITIONAL | EXPECTED_INTERNAL_OR_AUX):
        if name not in index_text:
            failures.append(f"00-SKILLS索引.md: missing active skill route for {name}")
        if name not in triggers_text:
            failures.append(f"TRIGGERS.md: missing active skill trigger row for {name}")

    # Public routing docs must preserve the standard entry distinction: external
    # entries are user-facing; internal/auxiliary tools do not steal the business
    # entry route.
    for name in EXPECTED_EXTERNAL:
        if not re.search(rf"`{re.escape(name)}`", index_text):
            failures.append(f"00-SKILLS索引.md: external entry not listed with code span: {name}")
    for tool in ["find-crypto-entry", "ast-deobfuscate", "env-patch", "js-page-runtime-parity"]:
        pattern = rf"内部工具[^\n]*`?{re.escape(tool)}`?"
        if not re.search(pattern, index_text):
            failures.append(f"00-SKILLS索引.md: {tool} must remain internal-tool routed")


def main() -> int:
    failures: list[str] = []
    for rel in ROUTING_FILES:
        path = ROOT / rel
        if not path.is_file():
            failures.append(f"missing routing file: {rel}")
            continue
        check_tokens(rel, read_text(path), failures)
    check_route_contract(failures)
    payload = {"tool": "validate_routing", "status": "PASS" if not failures else "FAIL", "checked": ROUTING_FILES, "failures": failures[:120]}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
