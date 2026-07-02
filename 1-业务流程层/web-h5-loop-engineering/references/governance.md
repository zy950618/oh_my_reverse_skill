# Governance

## Version

Current version: 0.2.0

## Source Patterns

- Ralph-style loops: fresh agent context per iteration, persistent task state, quality checks, progress learning, and explicit stop condition.
- Loop Library style: every loop answers goal, evaluation method, learning capture, and finish-or-ask-for-help boundary.
- oh_my_reverse_skill constraints: Web/H5 only, no unverified success claims, no bypass instructions, no stale evidence as observed fact.

## Change Log

- 0.2.1: Added Phase 2 high-fidelity localhost risk-lab evidence boundary from `run-20260630-013842-high-fidelity-risk-lab`; positive scope is limited to self-owned risk state machine, final business API direct repeat, token lifecycle negatives, and localhost business API worker isolation.
- 0.2.2: Added Phase 2.1 business data assertion gate from `run-20260630-022227-high-fidelity-risk-lab`; positive LOOP acceptance now requires server-side business ledger assertions, negative ledger_delta=0, and concurrency order/session/worker ownership.
- 0.2.0: Added real execution standard with Loop Runner, acceptance report, fixture freshness report, quantitative metrics, and real execution gate.
- 0.1.0: Added Web/H5 Loop Engineering skill with three-role loop, ledgers, evals, and local validation gate.

## Local Gates

Run after changing loop roles, ledgers, evals, or crawler hardening:

```bash
python tools/validate_web_h5_loop_gate.py
python tools/validate_web_h5_crawler_gate.py
python tools/validate_web_h5_real_execution_gate.py
python tools/validate_business_data_assertions.py public-range-evidence
python tools/ci_gate.py .ci-out
```

## Drift Tests

Run evals when:

- role boundaries change
- stop conditions change
- fresh evidence requirements change
- concurrency ladder or session/cache isolation rules change
- real Web/H5 task exposes a loop failure
- runner, acceptance report, fixture freshness, or quantitative metrics change

## Long-Term Governance

Do not let loop automation become unattended infinite execution. Keep max iterations, stop conditions, human review, and cost/token boundaries visible.
