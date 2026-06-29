#!/usr/bin/env python3
"""Validate Web/H5 real execution standardization assets.

This gate checks that the repository contains the runner, acceptance report,
freshness governance, metrics, references, and evals needed for real Web/H5
loop execution. It does not prove any target site is currently stable.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent

CHECKS = [
    {
        "name": "loop runner tool",
        "path": "tools/web_h5_loop_runner.py",
        "tokens": [
            "record-iteration",
            "validate",
            "loop_id",
            "Verifier",
            "Governor",
            "concurrency_ladder",
            "fixture_freshness",
            "metrics",
        ],
    },
    {
        "name": "acceptance report tool",
        "path": "tools/web_h5_acceptance_report.py",
        "tokens": [
            "clean_unverified",
            "repeat_verified",
            "worker_1",
            "worker_2",
            "worker_5",
            "worker_10",
            "risk_control",
            "ui_api_parity",
            "fixtures_freshness",
        ],
    },
    {
        "name": "fixture freshness report tool",
        "path": "tools/fixture_freshness_report.py",
        "tokens": [
            "expired_count",
            "review_pending_count",
            "source_freshness",
            "--strict-fresh",
        ],
    },
    {
        "name": "loop ledgers upgraded",
        "path": "1-业务流程层/web-h5-loop-engineering/references/loop-ledgers.md",
        "tokens": [
            "Runner Execution Ledger",
            "Risk-Control Ledger",
            "Data Acceptance Ledger",
            "Fixture Freshness Ledger",
            "Metrics Ledger",
        ],
    },
    {
        "name": "crawler hardening upgraded",
        "path": "1-业务流程层/reverse-js-crawler/references/web-h5-crawler-hardening.md",
        "tokens": [
            "Risk-Control Concurrency Gate",
            "Data Acceptance Gate",
            "Fixture Freshness Governance Gate",
            "Quantitative Metrics Gate",
        ],
    },
    {
        "name": "real execution reference",
        "path": "1-业务流程层/web-h5-loop-engineering/references/real-execution-standard.md",
        "tokens": [
            "Loop Runner",
            "Acceptance Report",
            "quantitative metrics",
            "fixture freshness",
            "human review",
        ],
    },
    {
        "name": "crawler acceptance reference",
        "path": "1-业务流程层/reverse-js-crawler/references/crawler-acceptance-pack.md",
        "tokens": [
            "clean_unverified",
            "1/2/5/10",
            "risk-control",
            "UI/API parity",
            "strict freshness",
        ],
    },
    {
        "name": "loop metrics artifact",
        "path": "1-业务流程层/web-h5-loop-engineering/metrics/real-task-summary.md",
        "tokens": [
            "task_count",
            "success_browserless_verified",
            "concurrency_verified",
            "strict_review_pass_count",
            "blocked_by_protection",
        ],
    },
    {
        "name": "real execution eval",
        "path": "1-业务流程层/web-h5-loop-engineering/evals/004-real-execution-standardization.yaml",
        "tokens": [
            "Loop Runner",
            "Acceptance Report",
            "fresh fixtures",
            "concurrency ladder",
            "quantitative metrics",
        ],
    },
    {
        "name": "crawler acceptance eval",
        "path": "1-业务流程层/reverse-js-crawler/evals/006-crawler-acceptance-risk-freshness.yaml",
        "tokens": [
            "risk-control concurrency",
            "UI/API parity",
            "fixture freshness",
            "1/2/5/10 worker",
            "expect_skill: true",
        ],
    },
    {
        "name": "governance real execution eval",
        "path": "1-业务流程层/skills-evaluation-governance/evals/015-real-execution-metrics-freshness.yaml",
        "tokens": [
            "real execution",
            "metrics",
            "strict-review",
            "freshness",
            "cannot pass",
        ],
    },
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def run_checks(repo_root: Path) -> dict:
    failures: list[dict] = []
    passed: list[str] = []

    for check in CHECKS:
        path = repo_root / check["path"]
        if not path.is_file():
            failures.append({
                "check": check["name"],
                "path": str(path),
                "missing_file": True,
                "missing_tokens": check["tokens"],
            })
            continue
        text = read_text(path)
        missing = [token for token in check["tokens"] if token not in text]
        if missing:
            failures.append({
                "check": check["name"],
                "path": str(path),
                "missing_file": False,
                "missing_tokens": missing,
            })
        else:
            passed.append(check["name"])

    return {
        "gate": "web_h5_real_execution",
        "passed": passed,
        "failures": failures,
        "pass_count": len(passed),
        "total": len(CHECKS),
        "status": "PASS" if not failures else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Web/H5 real execution assets")
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="repository root")
    args = parser.parse_args()

    payload = run_checks(Path(args.repo_root))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
