from __future__ import annotations

import json

from _phase4_lab_validator import validate_lab


EXPECTED = {
    "DPR coordinate mapping",
    "viewport coordinate",
    "crop rect coordinate",
    "touch event coordinate",
    "click captcha coordinate",
    "slider offset",
    "rotate angle",
    "mobile screenshot crop",
    "H5 safe area",
    "scroll offset",
}


def main() -> int:
    payload = validate_lab("mobile-h5-touch-lab", EXPECTED)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
