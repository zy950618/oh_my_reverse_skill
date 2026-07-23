#!/usr/bin/env python3
"""Structure-only fixture replay checks for the local airline lab."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def pointer_exists(payload: Any, pointer: str) -> bool:
    current = payload
    for part in pointer.strip("/").split("/"):
        if isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return False
        elif isinstance(current, dict):
            if part not in current:
                return False
            current = current[part]
        else:
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate local airline lab fixture pointers")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--plan", default="replay/replay_plan.json")
    args = parser.parse_args()
    root = Path(args.root)
    plan_path = root / args.plan
    plan = read_json(plan_path)
    failures: list[str] = []
    for step in plan.get("steps", []):
        response_path = root / step["response_fixture"]
        response = read_json(response_path)
        for pointer in step.get("required_pointers", []):
            if not pointer_exists(response, pointer):
                failures.append(f"{step['name']} missing {pointer} in {response_path}")
    payload = {
        "tool": "airline_lab_fixture_replay",
        "status": "PASS" if not failures else "FAIL",
        "plan": str(plan_path),
        "failures": failures,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

