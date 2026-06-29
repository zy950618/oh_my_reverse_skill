# Real Execution Standard

This reference turns Loop Engineering from a concept into a repeatable Web/H5
execution package. It standardizes the artifacts; it does not claim a site is
stable until the artifacts contain current evidence. It covers quantitative
metrics and fixture freshness as first-class gates. The phrase quantitative metrics is intentional: these counts are required evidence, not decoration.

## Required Tools

- Loop Runner: `python tools/web_h5_loop_runner.py init|record-iteration|validate`
- Acceptance Report: `python tools/web_h5_acceptance_report.py template|validate`
- Fixture freshness: `python tools/fixture_freshness_report.py 站点经验库`
- Release gate: `python tools/ci_gate.py .ci-out --release`

Use `--require-complete`, `--strict-fresh`, or both only when claiming real
completion, release readiness, concurrency, or long-term stability.

## Validation Status

- `STRUCTURE_PASS`: required sections exist. This is not real success.
- `BLOCKED`: the artifact is readable, but fresh evidence, retest, backend acceptance, data acceptance, or strict freshness is missing.
- `SUCCESS_PASS`: all real-completion evidence required by the tool is present.
- `FAIL`: the artifact is malformed or internally inconsistent.

Only `SUCCESS_PASS` can support a real completion claim. `STRUCTURE_PASS` and
`BLOCKED` must be reported as structure-ready or blocked, not successful.

## Execution Package

Every real loop run produces these artifacts:

```text
loop-ledger.json
acceptance-report.json
fixture-freshness.json
metrics/real-task-summary.md update
site memory update or explicit blocked reason
```

The ledger is the source of truth for role handoff. The acceptance report is
the source of truth for crawler readiness. The freshness report prevents stale
fixtures from being counted as observed facts.

## Completion Rule

The loop can complete only when all of these are true:

- Verifier has a pass record for fresh evidence, clean-state retest, replay or
  UI/API parity, and applicable concurrency ladder.
- Governor has a pass or stop-complete record for fact level, scope, session
  isolation, risk-control, memory, cleanup, and human-review boundaries.
- Loop Runner `validate --require-complete` returns `SUCCESS_PASS`.
- Acceptance Report `validate --require-complete` returns `SUCCESS_PASS`.
- Fixture freshness is fresh when the task claims real data consistency.
- Quantitative metrics are updated without inventing positive counts.

## Quantitative Metrics

Record these fields after every real Web/H5 run:

```yaml
task_count:
iterations_total:
success_browserless_verified:
concurrency_verified:
strict_review_pass_count:
flaky_count:
blocked_by_protection:
blocked_by_manual_challenge:
latest_replay_rate:
latest_fixture_freshness:
```

Do not raise `success_browserless_verified` unless the final business API is
accepted by the backend and repeat_verified evidence exists. Do not raise
`concurrency_verified` unless 1/2/5/10 worker stages pass with isolated session
and cache evidence.

## Risk Boundary

Risk-control handling means classification, isolation, backoff, session
retirement, kill switch, and human review. It does not mean WAF bypass,
CAPTCHA bypass, fingerprint spoofing, proxy rotation, or clearance cookie reuse.

When a protection blocks completion, persist it as blocked evidence, known
failure, human review, or negative eval. Do not write it as capability.

## Freshness Boundary

Historical replay rate is not fresh evidence. A fresh claim requires:

- strict fixture review passes
- no expired snapshots
- no review_pending placeholders
- recent replay/diff report for the current adapter target
- source_freshness recorded as `fresh`

If any item is missing, the final status is `unverified`, `stale`, `blocked`, or
`human_review`, not complete.
