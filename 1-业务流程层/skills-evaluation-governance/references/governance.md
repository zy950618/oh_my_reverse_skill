# Governance

## Version

Current version: 0.4.0

## Change Log

- 0.1.0: Initial usable Skill package with SKILL.md, references, agents metadata, and evals.
- 0.2.0: Added stricter scorecard, new Skill admission gate, local score script, and Karpathy-style behavior checks.
- 0.3.0: Added Web/H5 crawler hardening scoring coverage for fresh capture, clean-state retest, anti-flake repeatability, concurrency ladder, and session/cache isolation.
- 0.4.0: Added real execution scoring coverage for Loop Runner ledger, acceptance report, risk-control concurrency, UI/API parity, fixture freshness, and quantitative metrics.

## Drift Tests

Run evals when:

- description trigger words change
- workflow or boundary rules change
- a real task exposes a missed trigger or false trigger
- a target site or anti-bot behavior changes
- runner, acceptance report, fixture freshness, risk-control concurrency, or metrics gates change

Track:

- positive trigger pass rate
- negative trigger pass rate
- behavior criteria pass rate
- repeated failure patterns

## Long-Term Governance

Keep examples current, add negative cases for near misses, and do not overfit one real-world incident at the expense of general behavior.
