#!/usr/bin/env python3
"""Validate Web/H5 Loop Engineering skill structure.

This gate checks for bounded multi-role loop requirements. It does not run
real subagents and does not prove a target site is stable.
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
        "name": "loop skill core",
        "path": "1-业务流程层/web-h5-loop-engineering/SKILL.md",
        "tokens": [
            "Executor",
            "Verifier",
            "Governor",
            "最大迭代次数",
            "停止条件",
            "人工复核",
            "observed / derived / assumed / unverified",
        ],
    },
    {
        "name": "loop roles reference",
        "path": "1-业务流程层/web-h5-loop-engineering/references/loop-roles.md",
        "tokens": [
            "Executor",
            "Verifier",
            "Governor",
            "Human Reviewer",
            "The Verifier must be able to fail the Executor",
            "The Governor must be able to stop the loop",
        ],
    },
    {
        "name": "loop ledgers reference",
        "path": "1-业务流程层/web-h5-loop-engineering/references/loop-ledgers.md",
        "tokens": [
            "Loop Ledger",
            "Iteration Record",
            "Verification Ledger",
            "Runner Execution Ledger",
            "Risk-Control Ledger",
            "Fixture Freshness Ledger",
            "Metrics Ledger",
            "Stop Ledger",
            "Cleanup Ledger",
            "concurrency_ladder",
            "session_cache_isolation",
        ],
    },
    {
        "name": "loop governance reference",
        "path": "1-业务流程层/web-h5-loop-engineering/references/governance.md",
        "tokens": [
            "Ralph-style loops",
            "Loop Library style",
            "max iterations",
            "stop conditions",
            "human review",
            "real execution",
        ],
    },
    {
        "name": "loop real execution reference",
        "path": "1-业务流程层/web-h5-loop-engineering/references/real-execution-standard.md",
        "tokens": [
            "Loop Runner",
            "Acceptance Report",
            "quantitative metrics",
            "fixture freshness",
            "Risk Boundary",
        ],
    },
    {
        "name": "loop eval coverage",
        "path": "1-业务流程层/web-h5-loop-engineering/evals/001-loop-orchestrates-three-roles.yaml",
        "tokens": [
            "Executor",
            "Verifier",
            "Governor",
            "max iterations",
            "stop conditions",
        ],
    },
    {
        "name": "loop negative eval",
        "path": "1-业务流程层/web-h5-loop-engineering/evals/002-negative-one-shot-crawler.yaml",
        "tokens": [
            "expect_skill: false",
            "atomic reverse task",
            "does not invent extra loop agents",
        ],
    },
    {
        "name": "loop stale evidence regression eval",
        "path": "1-业务流程层/web-h5-loop-engineering/evals/003-regression-loop-stops-on-stale-evidence.yaml",
        "tokens": [
            "old HAR",
            "old token",
            "flaky",
            "clean_unverified",
            "repeat_verified",
            "1/2/5 worker ladder",
        ],
    },
    {
        "name": "loop real execution eval",
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
        "name": "governance loop eval",
        "path": "1-业务流程层/skills-evaluation-governance/evals/014-loop-engineering-governance.yaml",
        "tokens": [
            "Loop Engineering",
            "Executor",
            "Verifier",
            "Governor",
            "stop conditions",
            "fresh evidence",
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
        "gate": "web_h5_loop_engineering",
        "passed": passed,
        "failures": failures,
        "pass_count": len(passed),
        "total": len(CHECKS),
        "status": "PASS" if not failures else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Web/H5 Loop Engineering gates")
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="repository root")
    args = parser.parse_args()

    payload = run_checks(Path(args.repo_root))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
