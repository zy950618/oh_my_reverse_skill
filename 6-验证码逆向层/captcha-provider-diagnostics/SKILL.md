---
name: captcha-provider-diagnostics
description: Diagnose CAPTCHA provider type, script/iframe/sitekey/action/token fields, state observers, and verify-vs-business API boundaries without bypassing providers.
triggers: [provider-diagnostics, official-demo-readonly, vendor-compatible-lab, shumei, aliyun]
license: MIT
platforms: [cross-platform]
category: captcha
version: 0.1.0
---

# CAPTCHA Provider Diagnostics

Use this skill for provider observation and boundary classification.

## Diagnostics

- provider/type detection
- script and iframe inventory
- sitekey/action/token field observation
- challenge, verify, and final business API separation
- state observer evidence

## Boundary Rule

Challenge endpoint success and verify endpoint success are not business success. A positive capability claim requires final business API acceptance plus Phase 2.1 business data assertions.

## Safety

Provider demo keys, testing keys, and local dummy flows can only produce boundary, negative, or memory evidence unless a final business API with server ledger is verified.

## Phase 3.8 Public Range Diagnostics Rule

- Source run_id: `run-20260630-101500-phase3-8-family-hardening`.
- Evidence: `public-range-evidence/opencaptchaworld/run-20260630-101500-phase3-8-family-hardening.json` and `public-range-evidence/gocaptcha-official/run-20260630-101500-phase3-8-family-hardening.json`.
- Evals: `evals/phase3-8/001-opencaptcha-answer-field-leakage.yaml`, `evals/phase3-8/004-gocaptcha-family-capability-split.yaml`.
- Scope classification must be recorded before any solver route: `localhost_lab`, `public_range`, `local_open_source_range`, `self_owned`, `authorized_target`, `official_demo`, `unknown_third_party`, or `production_unverified`.
- For `unknown_third_party` and `production_unverified`, allowed work is observation_only provider detection, challenge presence, risk block summary, manual handoff, official API, permission, or allowlist. Automatic challenge handling, token forging, WAF bypass, fingerprint spoof, proxy evasion, clearance reuse, and risk token reuse are forbidden.
- Provider diagnostics must emit challenge provider, challenge_family, challenge_type, required user action, visible asset sources, API endpoints observed, and whether any answer-shaped fields are present. Answer-shaped fields such as `correct_option_index` and `hold_time` are leakage observations, not solver input.

## Phase 3.9 Shumei / Aliyun Handling Rule

- Source run_id: `run-20260630-113000-phase3-9-vendor-shield-range`.
- Evidence: `public-range-evidence/shumei-captcha-demo/run-20260630-113000-phase3-9-vendor-shield-range.json`, `public-range-evidence/aliyun-captcha-demo/run-20260630-113000-phase3-9-vendor-shield-range.json`, `public-range-evidence/shumei-compatible-lab/run-20260630-113000-phase3-9-vendor-shield-range.json`, and `public-range-evidence/aliyun-compatible-lab/run-20260630-113000-phase3-9-vendor-shield-range.json`.
- Evals: `evals/phase3-9/shumei-compatible-lab-compatible-lab.yaml`, `evals/phase3-9/aliyun-compatible-lab-compatible-lab.yaml`.
- Shumei/Aliyun targets must be classified as official_demo, self_owned_trial, authorized_target, vendor-compatible-lab, unknown_third_party, or production_unverified.
- Official demos allow provider diagnostics and state observation only unless interaction is explicitly allowed. Vendor-compatible labs train solver/action strategy only and never prove official vendor production capability.

## Workflow

Use `configs/vendor_challenge_matrix.yaml` and `configs/range_scope_contract.yaml` before provider work. Official demos are state observers; compatible labs are scoped local replay targets.

## Success Criteria

Provider diagnostics must record provider markers, challenge family, action mode, evidence path, and whether business API acceptance is absent or present.

## Boundaries

This skill is not responsible for vendor production bypass, token forging, fingerprint spoofing, or unapproved action replay. Unknown third-party targets remain observation-only.

## Governance

Write known failures, run_id, screenshot/network evidence, and eval backlog. Drift requires rerunning official-demo diagnostics and compatible-lab gates.

## Change Log

- 2026-06-30: Added Phase 3.9 Shumei/Aliyun demo and compatible-lab rules from `run-20260630-113000-phase3-9-vendor-shield-range`.

## Phase 3.10 Realism Hardening Rule

- Source run_id: `run-20260630-163000-phase3-10-realism-hardening`.
- Evidence: `public-range-evidence/shumei-compatible-lab/run-20260630-163000-phase3-10-realism-hardening.json`, `public-range-evidence/aliyun-compatible-lab/run-20260630-163000-phase3-10-realism-hardening.json`, and `public-range-evidence/raw/challenge-realism-audit/run-20260630-163000-phase3-10-realism-hardening/challenge-realism-audit.json`.
- Scope: `localhost_vendor_compatible_lab`; official vendor trial is `blocked_authorization_required` without `configs/private/vendor_trial.<target>.json`.
- Capability level: compatible families remain `positive_candidate`; official Shumei/Aliyun remain `memory_only` or `blocked_authorization_required`.
- Boundary: compatible lab evidence cannot be extrapolated to Shumei/Aliyun production or unknown third-party sites.
- Failure cases: hard/adversarial failures must be kept in `failure-cases.json` and used as provider mode drift examples.
- Eval: `evals/phase3-10/shumei-compatible-lab-hardening.yaml` and `evals/phase3-10/aliyun-compatible-lab-hardening.yaml`.
- Next training goal: run self-owned official trial diagnostics after real scene/app/allowed_host config is provided.
## Phase 3.11 vendor-compatible diagnostics boundary

- source_run_id: `run-20260630-173000-phase3-11-type-matrix`
- evidence: `public-range-evidence/shumei-compatible-lab/run-20260630-173000-phase3-11-type-matrix.json`, `public-range-evidence/aliyun-compatible-lab/run-20260630-173000-phase3-11-type-matrix.json`
- evals: `evals/phase3-11/vendor-compatible-type-matrix.yaml`
- Shumei-compatible families must be tracked separately as `slide`, `select`, `icon_select`, `seq_select`, `spatial_select`, `no_sense`; Aliyun-compatible families must be tracked separately as `slider`, `puzzle`, `image_restore`, `spatial_reasoning`, `one_click`, `no_trace`.
- Compatible lab results are local training diagnostics only. They must not be written as official Shumei or official Aliyun capability, and `one_click` / `no_sense` / `no_trace` are state-machine observation paths, not no-sense risk-control bypass capability.
- Every family-level decision must bind run_id, scope, evidence, eval, blackbox gate, leakage audit, realism audit, and capability decision before it can influence SKILLS scoring.
## Phase 3.12 model flywheel provider boundary

- source_run_id: `run-20260630-183000-phase3-12-model-flywheel`
- evidence: `public-range-evidence/aliyun-compatible-lab/run-20260630-183000-phase3-12-model-flywheel.json`
- evals: `evals/phase3-12/`
- Provider-compatible model improvements are local/public-range diagnostics only and must not be written as official Shumei/Aliyun capability.
