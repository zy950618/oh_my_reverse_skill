from __future__ import annotations

import json
import re
import sys
from pathlib import Path


TOKEN_PATTERNS = [
    re.compile(r"(?i)(cookie|token|authorization|set-cookie)(\\s*[:=]\\s*)([^\\s,;]+)"),
    re.compile(r"(?i)(order[_-]?id)(\\s*[:=]\\s*)([A-Za-z0-9_-]+)"),
]


def redact_text(text: str) -> str:
    redacted = text
    for pattern in TOKEN_PATTERNS:
        redacted = pattern.sub(lambda match: f"{match.group(1)}{match.group(2)}<REDACTED>", redacted)
    return redacted


def main(argv: list[str]) -> int:
    if len(argv) == 1:
        print(json.dumps({"tool": "redact_live_evidence", "status": "DRY_RUN", "input_required": True}, indent=2))
        return 0
    path = Path(argv[1])
    text = path.read_text(encoding="utf-8-sig", errors="ignore")
    print(redact_text(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
