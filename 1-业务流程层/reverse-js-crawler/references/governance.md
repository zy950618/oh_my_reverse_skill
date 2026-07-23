# Governance

## Version

Current version: 0.4.0

## Change Log

- 0.1.0: Initial usable Skill package with SKILL.md, references, agents metadata, and evals.
- 0.2.0: Added explicit success criteria, site memory write-back, regression backtest, Skill Bench/GitHub CI wording, and quick_validate requirement.
- 0.3.0: Added Web/H5 crawler hardening gates for fresh packet evidence, clean-state retests, anti-flake repeatability, concurrency ladder, and session/cache isolation.
- 0.4.0: Added acceptance report, risk-control concurrency, UI/API parity, fixture freshness governance, and quantitative metrics gates.

## CI And Drift

- Run quick_validate before accepting changes.
- Run local backtests after trigger or workflow changes.
- Use Skill Bench in GitHub CI when the Skills are mirrored into a repository.
- Track drift when target sites change APIs, crypto, or route decisions.

## Drift Tests

Run evals when:

- description trigger words change
- workflow or boundary rules change
- a real task exposes a missed trigger or false trigger
- a target site or anti-bot behavior changes
- acceptance report, risk-control concurrency, UI/API parity, fixture freshness, or metrics rules change

Track:

- positive trigger pass rate
- negative trigger pass rate
- behavior criteria pass rate
- repeated failure patterns

## Long-Term Governance

Keep examples current, add negative cases for near misses, and do not overfit one real-world incident at the expense of general behavior.
