#!/usr/bin/env python3
"""Conservative Markdown link validator for current repository docs."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)]+)\)")


def main() -> int:
    failures: list[str] = []
    checked = 0
    for path in ROOT.rglob("*.md"):
        if any(part in {".git", ".agent-control", ".claude", ".ci-out", "node_modules"} for part in path.parts):
            continue
        raw_text = path.read_text(encoding="utf-8-sig", errors="replace")
        checked += 1
        visible_lines: list[str] = []
        in_fence = False
        for line in raw_text.splitlines():
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                visible_lines.append("")
                continue
            visible_lines.append("" if in_fence else line)
        text = "\n".join(visible_lines)
        for match in LINK_RE.finditer(text):
            target = match.group(1).split("#", 1)[0].strip()
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            candidate = (path.parent / target).resolve()
            try:
                candidate.relative_to(ROOT.resolve())
            except ValueError:
                failures.append(f"{path.relative_to(ROOT)} links outside repo: {target}")
                continue
            if not candidate.exists():
                failures.append(f"{path.relative_to(ROOT)} broken link: {target}")
    payload = {"tool": "validate_links", "status": "PASS" if not failures else "FAIL", "checked_markdown": checked, "failure_count": len(failures), "failures": failures[:50]}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
