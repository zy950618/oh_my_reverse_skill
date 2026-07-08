#!/usr/bin/env python3
"""Validate current public routing sources exclude migrated challenge routes."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from validate_structure import PUBLIC_DOCS as ROUTING_FILES, STALE_COUNT_PATTERNS as STALE_COUNT

ROOT = Path(__file__).resolve().parents[2]
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
ROUTING_FILES = list(ROUTING_FILES)
PRIMARY_ENTRY_ROUTE = {
    "loop": "web-h5-loop-engineering",
    "pure_api": "website-314-api-delivery",
    "single_chain": "reverse-js-crawler",
}
FINGERPRINT_ROUTES = {
    "browser-fingerprint-surface-lab",
    "fingerprint-block-reason-diagnostics",
}
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
    "browser-fingerprint-surface-lab",
    "fingerprint-block-reason-diagnostics",
}
EXPECTED_INTERNAL_OR_AUX = {
    "find-crypto-entry",
    "ast-deobfuscate",
    "env-patch",
    "js-page-runtime-parity",
    "ai-reverse-skill-creator",
    "karpathy-guidelines",
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
    if "current active count is 15" in lowered and "python3 tools/governance/score_skills.py --repo ." not in text:
        failures.append(f"{rel}: hard-coded active count lacks score_skills authority")


def check_route_contract(failures: list[str]) -> None:
    index = ROOT / "00-SKILLS索引.md"
    triggers = ROOT / "TRIGGERS.md"
    usage = ROOT / "USAGE.md"
    if not index.is_file() or not triggers.is_file():
        return
    index_text = read_text(index)
    triggers_text = read_text(triggers)
    usage_text = read_text(usage) if usage.is_file() else ""
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

    route_sources = "\n".join([triggers_text, usage_text, index_text])
    for route in PRIMARY_ENTRY_ROUTE.values():
        if route not in route_sources:
            failures.append(f"public routing docs missing primary entry route {route}")
    if "入口优先级" in triggers_text:
        priority_line = next((line for line in triggers_text.splitlines() if "入口优先级" in line), "")
        for route in PRIMARY_ENTRY_ROUTE.values():
            if route not in priority_line:
                failures.append(f"TRIGGERS.md: entry priority line missing {route}")

    # Intentional denylist for unsafe fingerprint routing wording: public docs may
    # describe observation/refusal only, never ownership by WAF handlers or evasion.
    for line_no, line in enumerate(triggers_text.splitlines(), 1):
        line_lower = line.lower()
        if "fingerprint" in line_lower or "浏览器指纹" in line or "anti-bot" in line_lower:
            if "imperva-waf-reese84" in line and not any(route in line for route in FINGERPRINT_ROUTES):
                failures.append(f"TRIGGERS.md:{line_no}: fingerprint/anti-bot route must not be owned only by imperva-waf-reese84")
        if "指纹模拟" in line or "fingerprint spoof" in line_lower or "stealth" in line_lower:
            failures.append(f"TRIGGERS.md:{line_no}: public routing must describe fingerprint observation, not spoofing/stealth")


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
