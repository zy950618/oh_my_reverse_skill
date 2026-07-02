# Governance

## Version

Current version: 0.4.1

## Change Log

- 0.4.2: Added Phase 2 governance boundary from `run-20260630-013842-high-fidelity-risk-lab`; local positive evidence must stay scoped to self-owned localhost risk-lab mechanics and cannot be scored as third-party CAPTCHA/WAF/fingerprint or production concurrency capability.
- 0.1.0: Initial usable Skill package with SKILL.md, references, agents metadata, and evals.
- 0.2.0: Added stricter scorecard, new Skill admission gate, local score script, and Karpathy-style behavior checks.
- 0.3.0: Added Web/H5 crawler hardening scoring coverage for fresh capture, clean-state retest, anti-flake repeatability, concurrency ladder, and session/cache isolation.
- 0.4.0: Added real execution scoring coverage for Loop Runner ledger, acceptance report, risk-control concurrency, UI/API parity, fixture freshness, and quantitative metrics.
- 0.4.1: Added trigger convergence governance so public entry skills, conditional escalation skills, and internal support tools remain separated instead of all triggering on adjacent keywords.
- 0.4.2: Added Phase 2 high-fidelity local risk-lab scope boundaries.
- 0.4.3: Added Phase 2.1 business data assertion admission gate; evidence without DATA_ASSERTION_PASS is not positive_allowed even when direct replay or control flow passes.

## Drift Tests

Run evals when:

- description trigger words change
- workflow or boundary rules change
- a real task exposes a missed trigger or false trigger
- a target site or anti-bot behavior changes
- runner, acceptance report, fixture freshness, risk-control concurrency, or metrics gates change
- business_data_assertions, server-side business ledger, or positive downgrade rules change
- trigger scope is narrowed or a support skill is moved behind an entry skill

Track:

- positive trigger pass rate
- negative trigger pass rate
- behavior criteria pass rate
- repeated failure patterns

## Long-Term Governance

Keep examples current, add negative cases for near misses, and do not overfit one real-world incident at the expense of general behavior.
