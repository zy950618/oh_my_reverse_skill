---
name: authorized-target-adapter
standard_type: conditional_escalation
description: Adapt reverse-engineering workflows only for owned or explicitly authorized targets with scope, allowed hosts, rate limits, stop conditions, redaction, and business data assertions.
triggers: [authorized-target, scope-contract, business-data-assertions, five-second-shield-lab]
license: MIT
platforms: [cross-platform]
category: workflow
version: 0.1.0
---

# Authorized Target Adapter

Use this skill before adapting a real target beyond localhost or public labs.

## Required Scope

- authorization statement
- `allowed_hosts`
- allowed modes
- rate limit
- stop condition
- kill switch
- evidence redaction rule

## Positive Gate

Any positive capability claim must include:

- final business API acceptance
- repeat direct interface acceptance without live browser profile dependency
- server-side business ledger or equivalent authoritative business data proof
- `business_data_status=DATA_ASSERTION_PASS`

## Non-Authorized Targets

For unknown third-party production targets, use observation-only diagnostics. Do not automate challenge challenges, token clearance, WAF evasion, or high-concurrency tests.

## Workflow

Use `configs/range_scope_contract.yaml` before adapting any target. Route official demos to readonly observation, localhost labs to scoped action replay, and authorized targets to business-data assertions with stop conditions.

## Success Criteria

Accept a positive adapter result only when final business API acceptance, repeat direct interface acceptance, concurrency ladder, redaction, and ledger-backed assertions pass for the same run_id.

## Boundaries

This skill is not responsible for defeating WAF/challenge controls on unknown third-party or production-unverified targets. Those scopes remain observation-only with manual handoff.

## Governance

Write back run_id, evidence path, known failures, and eval backlog before promotion. Drift requires replaying scope, business-data, and capability-promotion gates.

## Change Log

- 2026-06-30: Added vendor/shield candidate boundary from local WAF/shield candidate evidence.


## Auxiliary Policy

- Engineering discipline follows `4-通用规范层/karpathy-guidelines/SKILL.md`.
- Scope contract details live in `references/scope-contract.md`.
