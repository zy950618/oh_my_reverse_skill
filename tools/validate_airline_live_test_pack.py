from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AIRLINES = ROOT / "public-range-evidence" / "real-site-observation-pack" / "airlines"
TARGETS = {"mh", "5j", "tg", "scoot", "vn", "cz", "sq"}
REQUIRED_FILES = [
    "authorized_mapping.template.yaml",
    "readonly_query_plan.md",
    "challenge_state_mapping.md",
    "pure_api_transition_plan.md",
    "redaction_checklist.md",
    "live_report.template.md",
]
REQUIRED_TEXT = [
    "observation_only",
    "authorized_readonly",
    "authorized_sandbox_mutation",
    "authorized_fullflow",
    "real_cookie",
    "real_token",
    "real_har",
    "passenger_info",
    "payment_info",
    "human_confirmation",
]


def validate_target(target: str) -> dict[str, object]:
    root = AIRLINES / target
    failures: list[str] = []
    for name in REQUIRED_FILES:
        if not (root / name).is_file():
            failures.append(f"missing {name}")
    if not failures:
        corpus = "\n".join((root / name).read_text(encoding="utf-8-sig", errors="ignore") for name in REQUIRED_FILES)
        for term in REQUIRED_TEXT:
            if term not in corpus:
                failures.append(f"missing required live boundary text: {term}")
    return {"target": target, "status": "PASS" if not failures else "FAIL", "failures": failures}


def main() -> int:
    found = {path.name for path in AIRLINES.iterdir() if path.is_dir()} if AIRLINES.is_dir() else set()
    results = [validate_target(target) for target in sorted(TARGETS & found)]
    failures = []
    missing = sorted(TARGETS - found)
    if missing:
        failures.append(f"missing targets: {missing}")
    failures.extend(f"{item['target']}: {failure}" for item in results for failure in item["failures"])
    payload = {
        "tool": "validate_airline_live_test_pack",
        "status": "PASS" if not failures else "FAIL",
        "target_count": len(found & TARGETS),
        "live_status": "NOT_RUN_NO_AUTHORIZATION_INPUT",
        "failures": failures,
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
