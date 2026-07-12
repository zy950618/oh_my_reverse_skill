# SKILLS Changelog

## 2026-07-09 — Runtime evidence and internal capability hardening

### Changed

- Added manifest-aware safe uninstall checks to `INSTALL.md`.
- Added optional JSON summary output to `tools/governance/score_skills.py` while preserving the existing stdout behavior.
- Hardened script collection and runtime-trace contracts with source linkage, hashes, freshness, evidence levels, redaction, and `raw_secret_persisted: false` requirements.
- Hardened crypto-entry and browser/Node parity contracts with observed anchors, call-chain or run evidence, explicit failure splits, and no unsupported production claim.
- Added clean-room external-source handling and negative evals that prohibit importing unknown-license or risk-sensitive external code, templates, prompts, tests, or examples into active Skills.
- Added internal-base attachment rules for external capability patterns: every retained pattern must map to an existing Skill, contract, eval, or governance rule with an evidence level, prohibited conversion, validation path, and remaining gap.

### Evidence boundary

- External source observations do not establish real-site, sign/token, WAF/challenge, concurrency, or production capability.
- Risk-sensitive patterns remain reference-only, clean-room summaries, negative eval seeds, or observation/lab evidence contracts.
- Durable product contracts and evals are retained; repository execution plans, per-run acceptance records, and local orchestration state are not Skill functionality.
