from __future__ import annotations

import json

from _phase4_lab_validator import validate_lab


EXPECTED = {
    "string array obfuscation",
    "control flow flattening",
    "dead code",
    "virtual dispatch mock",
    "dynamic function call",
    "anti-debug signal mock",
    "AST deobfuscation report",
    "runtime trace report",
    "pure solver output",
}


def main() -> int:
    payload = validate_lab("jsvmp-obfuscation-lab", EXPECTED)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
