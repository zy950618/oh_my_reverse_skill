from __future__ import annotations

import json

from _phase4_lab_validator import validate_lab


EXPECTED = {
    "no_challenge",
    "captcha_detected",
    "waf_challenge_detected",
    "fingerprint_challenge_detected",
    "login_required",
    "rate_limited",
    "forbidden",
    "token_expired",
    "manual_review_required",
    "pure_api_replay_ready",
    "pure_api_replay_blocked",
}


def main() -> int:
    payload = validate_lab("challenge-state-lab", EXPECTED)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
