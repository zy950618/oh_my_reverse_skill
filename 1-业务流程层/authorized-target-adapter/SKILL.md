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

For unknown third-party production targets, use observation-only diagnostics. Do not automate CAPTCHA challenges, token clearance, WAF evasion, or high-concurrency tests.

## Phase 3.5 Longrun Feedback

- Source run_id: `run-20260630-041500-phase3-5-longrun`.
- Failure evidence: `public-range-evidence/longrun/phase3-5/run-20260630-041500-phase3-5-longrun/issue-ledger.json`.
- Rule added: local longrun evidence cannot be adapted to a real target unless authorization, allowed hosts, rate limit, stop condition, kill switch, and business-data assertions are supplied.
- Eval added: `evals/longrun/phase3-5/001-phase3-5-longrun-regression.yaml`.
- Capability impact: adapter remains boundary-gated; no production high-concurrency or third-party CAPTCHA/WAF claim is allowed from Phase 3.5.

## Phase 3.8 Authorized Target Rule

- Source run_id: `run-20260630-101500-phase3-8-family-hardening`.
- Evidence: `public-range-evidence/raw/capability-promotion-gate/run-20260630-101500-phase3-8-family-hardening/capability-promotion-decision.json`.
- Evals: `evals/phase3-8/004-gocaptcha-family-capability-split.yaml`.
- Scope classification is mandatory before adapter work. `unknown_third_party` and `production_unverified` are observation_only and manual handoff scopes.
- For `public_range`, `localhost_lab`, `self_owned`, and `authorized_target`, allowed work must be bounded by a scope contract: visual solver, action replay, JS runtime parity, fingerprint diagnostics, business API replay, concurrency ladder, business data assertions, failure cases, and evals.
- Authorized target positive promotion requires allowed_hosts/scope, business_data_assertions PASS, direct repeat PASS, concurrency ladder PASS, evidence redaction PASS, stop condition, and kill switch.

## Phase 3.9 Vendor Scope Rule

- Source run_id: `run-20260630-113000-phase3-9-vendor-shield-range`.
- Evidence: `public-range-evidence/shumei-captcha-demo/run-20260630-113000-phase3-9-vendor-shield-range.json`, `public-range-evidence/aliyun-captcha-demo/run-20260630-113000-phase3-9-vendor-shield-range.json`, and `public-range-evidence/five-second-shield-lab/run-20260630-113000-phase3-9-vendor-shield-range.json`.
- Playbook: `docs/REAL_WEBSITE_HANDLING_PLAYBOOK.md`.
- Official demos are readonly unless interactive replay permission is explicit. Self-owned trials require organization/scene/app scope and business verify flow before any positive claim.
- Unknown third-party and production-unverified targets stay observation-only; no automatic challenge handling, token forgery, WAF bypass, fingerprint spoof, proxy evasion, or clearance reuse.

## Workflow

Use `configs/range_scope_contract.yaml` before adapting any target. Route official demos to readonly observation, localhost labs to scoped action replay, and authorized targets to business-data assertions with stop conditions.

## Success Criteria

Accept a positive adapter result only when final business API acceptance, repeat direct interface acceptance, concurrency ladder, redaction, and ledger-backed assertions pass for the same run_id.

## Boundaries

This skill is not responsible for bypassing WAF/CAPTCHA controls on unknown third-party or production-unverified targets. Those scopes remain observation-only with manual handoff.

## Governance

Write back run_id, evidence path, known failures, and eval backlog before promotion. Drift requires replaying scope, business-data, and capability-promotion gates.

## Change Log

- 2026-06-30: Added Phase 3.9 vendor/shield candidate boundary from `run-20260630-113000-phase3-9-vendor-shield-range`.

## Phase 3.10 Self-Owned Trial And Shield Rule

- Source run_id: `run-20260630-163000-phase3-10-realism-hardening`.
- Evidence: `public-range-evidence/five-second-shield-lab/run-20260630-163000-phase3-10-realism-hardening.json`, `public-range-evidence/raw/vendor-trial-adapter/run-20260630-163000-phase3-10-realism-hardening/shumei.json`, and `public-range-evidence/raw/vendor-trial-adapter/run-20260630-163000-phase3-10-realism-hardening/aliyun.json`.
- Scope: local shield lab is `localhost_waf_lab`; Shumei/Aliyun official trial is `blocked_authorization_required` until private config exists.
- Capability level: five-second shield local lab is `positive_candidate`; official trials are `memory_only/BLOCKED`.
- Boundary: no fake credentials, no compatible-lab substitution, no production WAF/CAPTCHA claim.
- Failure cases: negative eval ledger_delta=0 and blocked adapter missing fields must be preserved.
- Eval: `evals/phase3-10/five-second-shield-lab-dynamic.yaml`.
- Next training goal: rerun adapter with real self-owned scene/app/allowed_host and business verify endpoint.
## Phase 3.11 official trial and real website handling

- source_run_id: `run-20260630-173000-phase3-11-type-matrix`
- evidence: `public-range-evidence/raw/vendor-trial-adapter/run-20260630-173000-phase3-11-type-matrix/`, `public-range-evidence/raw/real-website-handling-planner/run-20260630-173000-phase3-11-type-matrix/`
- evals: `evals/phase3-11/real-website-handling-plans.yaml`
- Unknown third-party sites default to observation_only and memory_only. Self-owned and authorized targets require allowed_hosts/scope, evidence redaction, business data assertions, direct repeat, and concurrency ladder before any candidate decision.
- Official demo pages are readonly unless action_allowed is explicit. Readonly official demo observation must not be written as action success.
- The planner must never suggest bypass, fingerprint spoofing, webdriver hide, proxy evasion, clearance reuse, or rate-limit evasion.
## Phase 3.12 authorized sample training policy

- source_run_id: `run-20260630-183000-phase3-12-model-flywheel`
- evidence: `docs/REAL_WEBSITE_HANDLING_PLAYBOOK.md`
- evals: `evals/phase3-12/`
- Unknown real websites remain observation-only.
- Self-owned or authorized targets may feed `datasets/captcha_flywheel/authorized/` only after redaction removes real tokens, cookies, auth headers, and personal information.
- Authorized-target model results can only be replayed inside the same authorized scope and cannot be generalized to other third-party sites.
