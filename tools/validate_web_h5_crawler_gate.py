#!/usr/bin/env python3
"""Validate mandatory Web/H5 crawler hardening gates.

This is a local structure gate. It does not prove a target site is stable.
It verifies that the current skill package still requires the evidence needed
to prevent flaky one-off success, stale HAR reuse, shared session leakage, and
unsupported concurrency claims.
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
        "name": "reverse skill workflow hardening",
        "path": "1-业务流程层/reverse-js-crawler/SKILL.md",
        "tokens": [
            "clean_unverified",
            "repeat_verified",
            "并发阶梯",
            "偶发成功",
            "state_reset",
            "session/cache 隔离",
            "acceptance report",
            "UI/API parity",
        ],
    },
    {
        "name": "reverse testing hardening",
        "path": "1-业务流程层/reverse-js-crawler/references/testing.md",
        "tokens": [
            "Packet Evidence",
            "Clean State Retest",
            "Repeat Count",
            "Failure Split",
            "Concurrency Ladder",
            "Session Isolation",
            "Acceptance Report",
            "Fixture Freshness",
        ],
    },
    {
        "name": "crawler hardening reference",
        "path": "1-业务流程层/reverse-js-crawler/references/web-h5-crawler-hardening.md",
        "tokens": [
            "Ponytail",
            "Playwright BrowserContext",
            "Scrapy AutoThrottle",
            "Crawlee SessionPool",
            "Clean-State Retest Gate",
            "Anti-Flake Gate",
            "Concurrency Ladder Gate",
            "Session/Cache Isolation Gate",
            "Risk-Control Concurrency Gate",
            "Data Acceptance Gate",
            "Fixture Freshness Governance Gate",
            "Quantitative Metrics Gate",
        ],
    },
    {
        "name": "crawler acceptance reference",
        "path": "1-业务流程层/reverse-js-crawler/references/crawler-acceptance-pack.md",
        "tokens": [
            "Acceptance Report",
            "clean_unverified",
            "1/2/5/10",
            "risk-control",
            "UI/API parity",
            "strict freshness",
        ],
    },
    {
        "name": "crawler hardening eval",
        "path": "1-业务流程层/reverse-js-crawler/evals/005-web-h5-crawler-hardening.yaml",
        "tokens": [
            "fresh packet evidence",
            "clean_unverified",
            "repeat_verified",
            "1/2/5/10 worker",
            "shared cookies",
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
        ],
    },
    {
        "name": "governance hardening eval",
        "path": "1-业务流程层/skills-evaluation-governance/evals/013-web-h5-crawler-hardening-gate.yaml",
        "tokens": [
            "Web/H5 crawler",
            "fresh capture",
            "clean-state validation",
            "anti-flake",
            "concurrency ladder",
            "session/cache isolation",
        ],
    },
    {
        "name": "anti-overgeneralization governance",
        "path": "99-SKILLS治理/12-反泛化与任务收敛规约.md",
        "tokens": [
            "单次请求 200",
            "Scope Ledger",
            "单 market",
            "单 session",
        ],
    },
    {
        "name": "concurrency isolation governance",
        "path": "99-SKILLS治理/13-并发指纹与会话隔离规约.md",
        "tokens": [
            "1 worker baseline",
            "2 workers isolation check",
            "5 workers stability check",
            "10 workers",
            "cookie jar 不共享",
            "token cache 不共享",
        ],
    },
    {
        "name": "freshness governance",
        "path": "99-SKILLS治理/16-实战复测与证据新鲜度规约.md",
        "tokens": [
            "clean_unverified",
            "verified",
            "repeat_verified",
            "state_reset",
            "source_freshness",
            "Old-vs-New Diff",
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
        "gate": "web_h5_crawler_hardening",
        "passed": passed,
        "failures": failures,
        "pass_count": len(passed),
        "total": len(CHECKS),
        "status": "PASS" if not failures else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Web/H5 crawler hardening gates")
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="repository root")
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    payload = run_checks(repo_root)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
