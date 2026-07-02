from __future__ import annotations

import json

from _phase4_lab_validator import validate_lab


EXPECTED = {
    "timestamp sign",
    "nonce sign",
    "HMAC-like sign",
    "AES-like payload encryption",
    "RSA-like envelope mock",
    "token lifecycle",
    "expired token",
    "invalid token",
    "replay mismatch",
    "browser-vs-node diff",
    "Node/V8 pure solver",
    "Python pure solver",
}


def main() -> int:
    payload = validate_lab("js-sign-token-lab", EXPECTED)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
