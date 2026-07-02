from __future__ import annotations

import json
import os
import sys
from pathlib import Path


TARGETS = {"mh", "5j", "tg", "scoot", "vn", "cz", "sq"}
REQUIRED_FILES = [
    "observation-pack.json",
    "observation_schema.json",
    "sample_observation.fixture.json",
    "runbook.md",
    "authorization_inputs.example.yaml",
    "do_not_commit_evidence.md",
]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def validate_pack(path: Path) -> dict:
    failures: list[str] = []
    for name in REQUIRED_FILES:
        if not (path / name).is_file():
            failures.append(f"missing {name}")
    if not failures:
        pack = read_json(path / "observation-pack.json")
        fixture = read_json(path / "sample_observation.fixture.json")
        if pack.get("pack_status") == "STRUCTURE_ONLY":
            failures.append("pack_status must not be STRUCTURE_ONLY")
        if pack.get("pack_status") != "authorized-live-ready":
            failures.append("pack_status must be authorized-live-ready")
        local = pack.get("local_validation")
        if not isinstance(local, dict):
            failures.append("local_validation object is required")
        else:
            for key in ("schema_validated", "executable_runbook_validated", "local_fixture_validated", "authorized_live_ready"):
                if local.get(key) is not True:
                    failures.append(f"local_validation.{key} must be true")
        if pack.get("live_capture_performed") is not False:
            failures.append("live_capture_performed must be false without authorization")
        expected_live = "NOT_RUN_NO_AUTHORIZATION_INPUT"
        if os.environ.get("AUTHORIZED_LIVE_OBSERVATION") == "1":
            expected_live = "AUTHORIZED_INPUT_PRESENT_NOT_EXECUTED_BY_VALIDATOR"
        if pack.get("live_observation_status") != expected_live and expected_live == "NOT_RUN_NO_AUTHORIZATION_INPUT":
            failures.append("live_observation_status must be NOT_RUN_NO_AUTHORIZATION_INPUT")
        if fixture.get("live_observation_status") != "NOT_RUN_NO_AUTHORIZATION_INPUT":
            failures.append("sample fixture must mark live observation not run")
    return {"target": path.name, "status": "PASS" if not failures else "FAIL", "failures": failures}


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python tools/validate_real_site_observation_pack.py <root>")
        return 2
    root = Path(argv[1])
    airlines = root / "airlines"
    if not airlines.is_dir():
        print(json.dumps({"status": "FAIL", "failures": [f"missing {airlines}"]}, ensure_ascii=False, indent=2))
        return 1
    found = {p.name for p in airlines.iterdir() if p.is_dir()}
    results = [validate_pack(airlines / target) for target in sorted(found)]
    failures = []
    missing = sorted(TARGETS - found)
    if missing:
        failures.append(f"missing targets: {missing}")
    failures.extend(f"{item['target']}: {failure}" for item in results for failure in item["failures"])
    payload = {
        "tool": "validate_real_site_observation_pack",
        "status": "PASS" if not failures else "FAIL",
        "root": str(root),
        "target_count": len(found),
        "live_observation_status": "NOT_RUN_NO_AUTHORIZATION_INPUT" if os.environ.get("AUTHORIZED_LIVE_OBSERVATION") != "1" else "AUTHORIZED_INPUT_PRESENT_NOT_EXECUTED_BY_VALIDATOR",
        "failures": failures,
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
