from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIVE_ROOT = ROOT / "authorized-live-tests"
LOCAL_CONFIG = "authorized-live-tests/authorized-live-targets.local.yaml"
REQUIRED_FILES = [
    "authorized-live-targets.schema.yaml",
    "authorized-live-targets.example.yaml",
    "live-test-policy.md",
    "redaction-policy.md",
    "live-observation-runbook.md",
    "live-readonly-runbook.md",
    "live-sandbox-mutation-runbook.md",
    "live-fullflow-runbook.md",
    "reports/.gitkeep",
]
REQUIRED_LEVELS = {
    "observation_only",
    "authorized_readonly",
    "authorized_sandbox_mutation",
    "authorized_fullflow",
}
FORBIDDEN_TERMS = {"real_cookie", "real_token", "real_har", "payment_info", "passenger_info"}


def git_ls_files(path: str) -> list[str]:
    raw = subprocess.check_output(["git", "ls-files", path], cwd=ROOT, text=True)
    return [line for line in raw.splitlines() if line.strip()]


def main() -> int:
    failures: list[str] = []
    for name in REQUIRED_FILES:
        if not (LIVE_ROOT / name).is_file():
            failures.append(f"missing {name}")

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8-sig", errors="ignore")
    if LOCAL_CONFIG not in gitignore:
        failures.append(f"{LOCAL_CONFIG} must be ignored")
    if git_ls_files(LOCAL_CONFIG):
        failures.append(f"{LOCAL_CONFIG} must not be tracked")

    if not failures:
        schema = (LIVE_ROOT / "authorized-live-targets.schema.yaml").read_text(encoding="utf-8-sig")
        example = (LIVE_ROOT / "authorized-live-targets.example.yaml").read_text(encoding="utf-8-sig")
        missing_levels = sorted(level for level in REQUIRED_LEVELS if level not in schema)
        if missing_levels:
            failures.append(f"schema missing authorization levels: {missing_levels}")
        for key in ("allowed_actions", "forbidden_actions", "redaction", "rate_limit"):
            if key not in example:
                failures.append(f"example missing {key}")
        for term in FORBIDDEN_TERMS:
            if term not in schema:
                failures.append(f"schema missing forbidden term {term}")

    payload = {
        "tool": "validate_authorized_live_config",
        "status": "PASS" if not failures else "FAIL",
        "live_status": "DRY_RUN_NO_LOCAL_AUTH_CONFIG",
        "local_config_tracked": bool(git_ls_files(LOCAL_CONFIG)),
        "failures": failures,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
