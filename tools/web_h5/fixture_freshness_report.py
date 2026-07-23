#!/usr/bin/env python3
"""Compatibility entry for the canonical fixture freshness gate.

The shared result retains ``expired_count``, ``review_pending_count``, and
``source_freshness``; the legacy ``--strict-fresh`` alias remains executable.
"""
from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools" / "replayer"))

from fixture_gate import cli_main


def main() -> int:
    return cli_main("fixture_freshness_report")


if __name__ == "__main__":
    raise SystemExit(main())
