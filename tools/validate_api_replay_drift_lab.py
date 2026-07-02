from __future__ import annotations

import json

from _phase4_lab_validator import validate_lab


EXPECTED = {
    "schema drift",
    "field missing",
    "field renamed",
    "JSON pointer mismatch",
    "timestamp drift",
    "signature drift",
    "token drift",
    "response business data drift",
    "replay diff report",
}


def main() -> int:
    payload = validate_lab("api-replay-drift-lab", EXPECTED)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
