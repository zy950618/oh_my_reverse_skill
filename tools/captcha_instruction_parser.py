#!/usr/bin/env python3
"""Parse local CAPTCHA instruction text into a challenge type."""
from __future__ import annotations
import argparse, json
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", default="")
    args = parser.parse_args()
    lower = args.text.lower()
    ctype = "slider-captcha" if "slider" in lower else "rotate-captcha" if "rotate" in lower else "click-captcha" if "click" in lower else "text-captcha"
    print(json.dumps({"status": "PASS", "challenge_type": ctype}, indent=2))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())

