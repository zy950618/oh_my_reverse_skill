---
name: authorized-target-adapter
description: Adapt reverse-engineering workflows only for owned or explicitly authorized targets with scope, allowed hosts, rate limits, stop conditions, redaction, and Phase 2.1 business data assertions.
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

## Phase 3.5 Longrun Feedback

- Source run_id: `run-20260630-041500-phase3-5-longrun`.
- Failure evidence: `public-range-evidence/longrun/phase3-5/run-20260630-041500-phase3-5-longrun/issue-ledger.json`.
- Rule added: local longrun evidence cannot be adapted to a real target unless authorization, allowed hosts, rate limit, stop condition, kill switch, and business-data assertions are supplied.
- Eval added: `evals/longrun/phase3-5/001-phase3-5-longrun-regression.yaml`.
- Capability impact: adapter remains boundary-gated; no production high-concurrency or third-party challenge/WAF claim is allowed from Phase 3.5.

## Phase 3.8 Authorized Target Rule

- Source run_id: `run-20260630-101500-phase3-8-family-hardening`.
- Evidence: `public-range-evidence/raw/capability-promotion-gate/run-20260630-101500-phase3-8-family-hardening/capability-promotion-decision.json`.
- Scope classification is mandatory before adapter work. `unknown_third_party` and `production_unverified` are observation_only and manual handoff scopes.
- For `public_range`, `localhost_lab`, `self_owned`, and `authorized_target`, allowed work must be bounded by a scope contract: JS runtime parity, fingerprint diagnostics, business API replay, concurrency ladder, business data assertions, failure cases, and evals.
- Authorized target positive promotion requires allowed_hosts/scope, business_data_assertions PASS, direct repeat PASS, concurrency ladder PASS, evidence redaction PASS, stop condition, and kill switch.

## Workflow

Use `configs/range_scope_contract.yaml` before adapting any target. Route official demos to readonly observation, localhost labs to scoped action replay, and authorized targets to business-data assertions with stop conditions.

## Success Criteria

Accept a positive adapter result only when final business API acceptance, repeat direct interface acceptance, concurrency ladder, redaction, and ledger-backed assertions pass for the same run_id.

## Boundaries

This skill is not responsible for bypassing WAF/challenge controls on unknown third-party or production-unverified targets. Those scopes remain observation-only with manual handoff.

## Governance

Write back run_id, evidence path, known failures, and eval backlog before promotion. Drift requires replaying scope, business-data, and capability-promotion gates.

## Change Log

- 2026-06-30: Added Phase 3.9 vendor/shield candidate boundary from `run-20260630-113000-phase3-9-vendor-shield-range`.

