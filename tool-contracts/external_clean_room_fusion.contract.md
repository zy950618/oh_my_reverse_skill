## Purpose
Define the internal clean-room gate for turning external-source observations into abstract repository assets without importing external code, templates, prompts, or active skills.

## Allowed Scope
- Inputs may reference only internal fact packs, license decisions, risk scans, and validation ledgers already recorded in this repository.
- Outputs are limited to abstract contracts, eval seeds, routing notes, and reference notes written in original wording.
- Risk-sensitive content is observation, lab, or evidence-contract only.

## Inputs
- `external_source_fact_pack`: source name, URL or path label, observed fact level, source freshness, inventory summary, and risk markers.
- `license_decision`: one of `permissive_clean_room_allowed`, `copyleft_reference_only`, `unknown_reference_only`, or `blocked`.
- `prohibited_use_scan`: explicit scan for code import, template import, prompt import, active skill creation, concealment, falsification, WAF defeat, fingerprint falsification, cookie/token/sign workflow enablement, and production success claims.
- `allowed_fusion_mode`: one or more of `reference_only`, `clean_room_summary`, `eval_seed_without_verbatim_copy`, `tool_contract`, or `lab_or_evidence_contract_observation_only`.
- `attribution_plan`: required when reference notes or public-source observations are retained.
- `validation_ledger`: commands, reviewer decision, evidence level, failure split, cleanup ledger, and remaining gaps.

## Outputs
- Abstract tool contracts with original wording and no external implementation details.
- Governance eval seeds that test allowed/prohibited fusion behavior.
- Reference notes that preserve attribution and evidence boundaries.
- Validation ledger entries that keep observed, derived, assumed, and unverified facts separate.

## Prohibited Outputs
- Imported external source code, templates, prompts, tests, examples, or generated active skills.
- Direct migration of GPL or unknown-license implementation content.
- Instructions that enable concealment, falsification, WAF/challenge defeat, fingerprint falsification, clearance-cookie replay, or production sign/token/cookie success.
- Claims that external README examples prove real-site, concurrency, challenge, or production capability.

## Evidence Files
- `external_source_fact_pack`
- `license_decision_record`
- `prohibited_use_scan`
- `attribution_plan`
- `validation_ledger`
- `cleanup_ledger`

## Failure Modes
- Missing fact pack, license decision, prohibited-use scan, allowed fusion mode, attribution plan, or validation ledger.
- Unknown-license or GPL source treated as importable implementation.
- Risk-sensitive marker converted from observation into operational defeat or concealment instructions.
- Active skill, manifest entry, code, template, or prompt created from external material.
- Evidence level blurred between observed, derived, assumed, and unverified.

## Retry Strategy
- Downgrade the source to `reference_only` when license or source identity is incomplete.
- Rewrite outputs as original abstract contracts or eval seeds.
- Move risk-sensitive details to evidence-boundary notes and require human review before expansion.
- Re-run structure validators and record the failure split before retrying fusion.

## Acceptance Checks
- Every source has an `external_source_fact_pack`, `license_decision`, `prohibited_use_scan`, `allowed_fusion_mode`, attribution decision, and validation ledger.
- GPL and unknown-license sources do not produce imported code/templates/prompts or active skills.
- Risk-sensitive content remains observation/lab/evidence-contract only.
- Outputs are limited to abstract contracts, eval seeds, and reference notes.
- `skills-manifest.json` is unchanged and no active skill directory is created.

## Related Skills
- `skills-evaluation-governance`
- `web-h5-loop-engineering`
- `karpathy-guidelines`
