from __future__ import annotations

import json

from _phase4_lab_validator import validate_lab


EXPECTED = {
    "site profile",
    "endpoint schema",
    "sign strategy",
    "token strategy",
    "captcha strategy",
    "fingerprint strategy",
    "pure API adapter",
    "FastAPI adapter",
    "SDK example",
    "replay report",
}


def main() -> int:
    payload = validate_lab("multi-site-adapter-lab", EXPECTED)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
