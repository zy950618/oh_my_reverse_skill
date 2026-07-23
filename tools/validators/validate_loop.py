#!/usr/bin/env python3
"""Validate Loop Engineering spine remains executable."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = [
    "1-业务流程层/web-h5-loop-engineering/SKILL.md",
    "1-业务流程层/web-h5-loop-engineering/references/loop-roles.md",
    "1-业务流程层/web-h5-loop-engineering/references/loop-ledgers.md",
    "tools/web_h5/web_h5_loop_runner.py",
    "tools/web_h5/web_h5_acceptance_report.py",
]


def main() -> int:
    failures = [f"missing {rel}" for rel in REQUIRED if not (ROOT / rel).is_file()]
    gate = subprocess.run([sys.executable, str(ROOT / "tools" / "web_h5" / "validate_web_h5_loop_gate.py")], cwd=str(ROOT), text=True, capture_output=True)
    if gate.returncode != 0:
        failures.append("validate_web_h5_loop_gate.py failed")
    payload = {"tool": "validate_loop", "status": "PASS" if not failures else "FAIL", "failures": failures, "loop_gate_stdout": gate.stdout[:4000]}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
