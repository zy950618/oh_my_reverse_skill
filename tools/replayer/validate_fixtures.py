#!/usr/bin/env python3
"""Compatibility entry for the canonical fixture gate."""
from __future__ import annotations

import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fixture_gate import cli_main


def main() -> int:
    return cli_main("validate_fixtures")


if __name__ == "__main__":
    sys.exit(main())
