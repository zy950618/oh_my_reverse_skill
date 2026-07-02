from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "README.md",
    "manifest.json",
    "negative_cases.json",
    "validation_report.json",
    "reports/replay_or_trace_report.md",
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def validate_lab(lab_id: str, expected_coverage: set[str]) -> dict[str, object]:
    lab = ROOT / "public-range-evidence" / "phase4-labs" / lab_id
    failures: list[str] = []
    if not lab.is_dir():
        failures.append(f"missing lab directory: {lab}")
        return {"tool": f"validate_{lab_id}", "status": "FAIL", "failures": failures}

    for name in REQUIRED_FILES:
        if not (lab / name).is_file():
            failures.append(f"missing {name}")

    if not failures:
        manifest = load_json(lab / "manifest.json")
        report = load_json(lab / "validation_report.json")
        negative = load_json(lab / "negative_cases.json")
        coverage = set(manifest.get("coverage", []))
        missing = sorted(expected_coverage - coverage)
        if manifest.get("status") != "PHASE4_LAB_READY":
            failures.append("manifest.status must be PHASE4_LAB_READY")
        if manifest.get("live_site_data_committed") is not False:
            failures.append("live_site_data_committed must be false")
        if missing:
            failures.append(f"missing coverage: {missing}")
        if report.get("status") != "PASS":
            failures.append("validation_report.status must be PASS")
        if report.get("no_live_site_data") is not True:
            failures.append("validation_report.no_live_site_data must be true")
        if len(negative.get("negative_cases", [])) < 3:
            failures.append("at least three negative cases are required")

    return {
        "tool": f"validate_{lab_id.replace('-', '_')}",
        "status": "PASS" if not failures else "FAIL",
        "lab": lab.relative_to(ROOT).as_posix(),
        "coverage_required": len(expected_coverage),
        "failures": failures,
    }
