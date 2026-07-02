---
name: fingerprint-block-reason-diagnostics
description: Record and attribute observed browser fingerprint and risk-block signals such as webdriver, canvas, WebGL, WebRTC, timezone, language, permissions, headers, and client hints without evasion.
license: MIT
platforms: [cross-platform]
category: risk-diagnostics
version: 0.1.0
trigger: fingerprint block reason, risk block diagnostics, 指纹阻断归因, 风控阻断诊断
---

# Fingerprint Block Reason Diagnostics

Use this skill only for diagnostics and evidence attribution.

## When To Use

Use this skill when an authorized/local lab task asks why a request, browser session, or risk-state flow was blocked and provides or requests observed evidence such as status code, response class, browser surface report, request/session context, redirect chain, or risk-state ledger.

## When NOT To Use

- Do not use this skill to inventory browser surfaces without a block-reason question; route that to `browser-fingerprint-surface-lab`.
- Do not use it to hide webdriver, forge fingerprints, rotate proxies, reuse clearance, or bypass rate limits.
- Do not use it to claim production WAF/CAPTCHA success from local diagnostics.

## Boundary

This is an attribution skill. It can classify observed, derived, assumed, and unverified block reasons, then recommend stop/ask/official API fallback/human review. It must not produce stealth patches, spoofing recipes, token reuse instructions, or evasion playbooks.

## Boundaries

- Not responsible for browser surface inventory; use `browser-fingerprint-surface-lab`.
- Not responsible for WAF bypass, CAPTCHA bypass, webdriver hiding, fingerprint spoofing, proxy evasion, clearance reuse, or risk token reuse.
- Write reusable failure modes to site memory or eval backlog.

## Precheck

1. Confirm authorization scope and target class.
2. Collect status code, response class, request/session context, and timing.
3. Collect browser surface report if fingerprint attribution is in scope.
4. Identify whether the claim is observed, derived, assumed, or unverified.
5. Confirm no bypass/evasion action is requested.

## Observed Signals

- webdriver
- canvas
- WebGL
- WebRTC
- timezone
- language
- permissions
- headers
- client hints

## Workflow

1. Build a diagnostic ledger entry for the run.
2. Attach observed signals, response class, and session context.
3. Separate direct observations from derived attribution.
4. Map the result to `blocked_by_scope`, `blocked_by_auth`, `blocked_by_stale_state`, `blocked_by_fingerprint_signal`, `blocked_by_rate_limit`, `unknown`, or another evidence-backed category.
5. Recommend safe next action: stop, ask for authorization, reset local lab state, use official API fallback, or route to human review.
6. Feed reusable failure categories back to eval or known-failure records.

## Ledger

Each diagnostic run must record:

- target and authorization scope
- observed block reason
- signal snapshot
- request/session context
- status code and response class
- whether the result is observed, derived, assumed, or unverified

## Prohibited

Do not generate stealth patches, webdriver hiding, fingerprint forgery, proxy rotation, or rate-limit evasion.

## Failure Handling

- Missing authorization or target context: stop with `BLOCKED_SCOPE`.
- Missing response evidence: mark attribution `unverified` and request capture/ledger evidence.
- Conflicting signals: record each signal separately and avoid a single-root-cause claim.
- User asks for evasion: refuse that part and provide diagnostic-only alternatives.

## Acceptance Criteria

- Diagnostic ledger includes scope, response evidence, observed signals, and attribution level.
- Each block reason is labeled observed, derived, assumed, or unverified.
- Output contains no stealth, spoofing, proxy evasion, token reuse, or rate-limit bypass steps.
- Safe next action is explicit.

## Success Criteria

- Block taxonomy is evidence-backed.
- CAPTCHA/fingerprint linkage is diagnostic-only.
- Incomplete evidence remains `unverified`.
- Fresh validation report exists.
- No forbidden action appears in the output.

## Governance

Version and change logs live in `references/governance.md`. Active-ready status requires local/authorized evidence, validator pass, negative/boundary eval coverage, metrics, and observation-only boundaries.

## Test / Eval

- positive: classify a localhost block with status code, response class, and surface report;
- negative: reject webdriver hiding or proxy evasion request;
- boundary: incomplete evidence produces `unverified` rather than a guessed root cause;
- regression: repeated known block reason maps to the same safe next action.

## Relationship With browser-fingerprint-surface-lab

Use `browser-fingerprint-surface-lab` to capture the surface inventory and drift. Use this skill to explain a block reason from that evidence plus request/session context. This skill consumes surface reports; it does not modify browser surfaces.

## Phase 3.5 Longrun Feedback

- Source run_id: `run-20260630-041500-phase3-5-longrun`.
- Failure evidence: `public-range-evidence/longrun/phase3-5/run-20260630-041500-phase3-5-longrun/issue-ledger.json`.
- Rule added: block-reason diagnostics must classify observed, derived, assumed, and unverified signals separately.
- Eval added: `evals/longrun/phase3-5/005-phase3-5-longrun-regression.yaml`.
- Capability impact: a local `not_blocked` observation is not a production WAF or CAPTCHA bypass capability.

## Phase 3.6 Public Diagnostics Feedback

- Source run_id: `run-20260630-053000-phase3-6-public-model`.
- Evidence: `public-range-evidence/fingerprint-diagnostics/run-20260630-053000-phase3-6-public-model-sannysoft.json`.
- Rule added: public fingerprint diagnostics must be observation-only, record observed signals and risk attribution, and keep capability status `memory_only` or `negative_eval_only`.
- Eval added: `evals/phase3-6/003-fingerprint-public-diagnostics.yaml`.
- Capability impact: diagnostics evidence can improve attribution rules but cannot promote evasion capability.

## Phase 3.8 Public Fingerprint Diagnostics Rule

- Source run_id: `run-20260630-101500-phase3-8-family-hardening`.
- Evidence: `public-range-evidence/fingerprint-diagnostics/run-20260630-101500-phase3-8-family-hardening-sannysoft.json`, `public-range-evidence/fingerprint-diagnostics/run-20260630-101500-phase3-8-family-hardening-creepjs.json`, and `public-range-evidence/fingerprint-diagnostics/run-20260630-101500-phase3-8-family-hardening-browserleaks.json`.
- Evals: `evals/phase3-8/007-fingerprint-diagnostics-observation-only.yaml`.
- Public fingerprint ranges are observation_only. Record observed signals, block reason, risk attribution, repeat/profile variance, screenshots, and surface report.
- Diagnostics positive is not evasion positive. Do not add webdriver hide, fingerprint spoof, proxy evasion, clearance reuse, or automated bypass guidance.

## Phase 3.9 Shield And Fingerprint Boundary

- Source run_id: `run-20260630-113000-phase3-9-vendor-shield-range`.
- Evidence: `public-range-evidence/five-second-shield-lab/run-20260630-113000-phase3-9-vendor-shield-range.json`.
- Eval: `evals/phase3-9/five-second-shield-lab.yaml`.
- Fingerprint or WAF block reason diagnostics may record observed browser signals, redirects, cookie writes, JS challenge state, and risk attribution.
- Diagnostics must not become stealth guidance. Production WAF bypass, real-site clearance reuse, proxy rotation evasion, and spoofing remain prohibited.

## Phase 3.10 Dynamic Shield Block-Reason Rule

- Source run_id: `run-20260630-163000-phase3-10-realism-hardening`.
- Evidence: `public-range-evidence/five-second-shield-lab/run-20260630-163000-phase3-10-realism-hardening.json`.
- Scope: local shield diagnostics and authorized/self-owned observation.
- Capability level: diagnostic attribution only; local shield flow may be `positive_candidate` for business-data lab readiness.
- Boundary: not production WAF bypass and not fingerprint evasion.
- Failure cases: missing challenge, stale nonce, expired clearance, wrong session, wrong signature, JS runtime mismatch, browser-only success not direct repeat.
- Eval: `evals/phase3-10/five-second-shield-lab-dynamic.yaml`.
- Next training goal: map block reason to stop/ask/official API fallback decisions on authorized targets.
## Phase 3.11 block reason diagnostics boundary

- source_run_id: `run-20260630-173000-phase3-11-type-matrix`
- evidence: `public-range-evidence/fingerprint-diagnostics/`
- evals: `evals/phase3-11/fingerprint-diagnostics-matrix.yaml`
- Public diagnostics targets such as Sannysoft, CreepJS, BrowserLeaks, and Incolumitas are observation-only unless explicitly authorized otherwise.
- Do not hide webdriver, spoof fingerprint surfaces, rotate proxies for evasion, reuse clearance cookies, or claim evasion positive. Record observed signals and risk attribution only.
## Phase 3.12 fingerprint failure category boundary

- source_run_id: `run-20260630-183000-phase3-12-model-flywheel`
- evidence: `public-range-evidence/raw/anti-solver-platform-audit/run-20260630-183000-phase3-12-model-flywheel/anti-solver-platform-audit.json`
- evals: `evals/phase3-12/`
- Fingerprint_drift can be a failure_category for diagnostics reports only; it cannot promote spoofing, webdriver hide, proxy evasion, or clearance reuse.
