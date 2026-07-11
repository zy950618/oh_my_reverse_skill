# Governance

## Version

Current version: 0.2.0

Low-LOOP orchestration candidate version: `3.0.0-candidate` (`adoption_status=CANDIDATE`, `implementation_status=MANUAL_ORCHESTRATED_LEDGER_ONLY`, `capability_level=structure_only`). The `0.2.x` line remains the Web/H5 business-loop reference version and must not be interpreted as the repository Low-LOOP orchestration version.

## V3 Candidate Authority And Drift

- Direct operator entry: [`../../../Claude codex 指挥codex 二次优化loop执行文件.md`](../../../Claude%20codex%20指挥codex%20二次优化loop执行文件.md)
- Candidate standard: [`../../../99-SKILLS治理/24-low-loop-execution-standard.md`](../../../99-SKILLS治理/24-low-loop-execution-standard.md)
- Adoption reconciliation: [`../../../99-SKILLS治理/25-low-loop-adoption-record.md`](../../../99-SKILLS治理/25-low-loop-adoption-record.md)
- Canonical candidate schema index: [`../schemas/index.schema.json`](../schemas/index.schema.json)
- Cross-object semantics and drift invariants: [`low-loop-semantic-validation-contract.md`](low-loop-semantic-validation-contract.md)
- Non-operational implementation sequencing: [`low-loop-roadmap.md`](low-loop-roadmap.md)

These links supersede older authority for V3 candidate evaluation. Historical execution/verification reports remain historical and do not become operator entries or current V3 proof. The current implementation is manual orchestration over candidate structures; it does not include the future V3 state package, secure executor, automated Git lifecycle, or actor-separated verifier.

Judge, tests, acceptance rules, and gates are frozen per run. A proposed change requires a new version, shadow validation against the frozen judge, preserved comparison evidence, role-separated manual re-execution, and an explicit Governor decision; the implementing actor cannot use its own gate change to approve itself. Only final reconciliation after source migration, shadow validation, independent review, and governance approval may mark V3 `ADOPTED`.

## Source Patterns

- Ralph-style loops: fresh agent context per iteration, persistent task state, quality checks, progress learning, and explicit stop condition.
- Loop Library style: every loop answers goal, evaluation method, learning capture, and finish-or-ask-for-help boundary.
- oh_my_reverse_skill constraints: Web/H5 only, no unverified success claims, no defeat instructions, no stale evidence as observed fact.

## Change Log

- 0.2.1: Added high-fidelity localhost risk-lab evidence boundary; positive scope is limited to self-owned risk state machine, final business API direct repeat, token lifecycle negatives, and localhost business API worker isolation.
- 0.2.2: Added business data assertion gate; positive LOOP acceptance now requires server-side business ledger assertions, negative ledger_delta=0, and concurrency order/session/worker ownership.
- 0.2.0: Added real execution standard with Loop Runner, acceptance report, fixture freshness report, quantitative metrics, and real execution gate.
- 0.1.0: Added Web/H5 Loop Engineering skill with three-role loop, ledgers, evals, and local validation gate.

## Local Gates

Run after changing loop roles, ledgers, evals, or crawler hardening:

```bash
python3 tools/web_h5/validate_web_h5_loop_gate.py
python3 tools/web_h5/validate_web_h5_crawler_gate.py
python3 tools/web_h5/validate_web_h5_real_execution_gate.py
python3 tools/evidence/validate_business_data_assertions.py public-range-evidence
python3 tools/governance/ci_gate.py .ci-out
```

## Drift Tests

Run evals when:

- role boundaries change
- stop conditions change
- fresh evidence requirements change
- concurrency ladder or session/cache isolation rules change
- real Web/H5 task exposes a loop failure
- runner, acceptance report, fixture freshness, or quantitative metrics change
- candidate standard/operator/schema/semantic-contract references drift
- judge, test, acceptance, or gate version changes without shadow comparison evidence

## Long-Term Governance

Do not let loop automation become unattended infinite execution. Keep max iterations, stop conditions, human review, and cost/token boundaries visible.
