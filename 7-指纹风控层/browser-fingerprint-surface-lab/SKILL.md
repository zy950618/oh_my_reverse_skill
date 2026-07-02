---
name: browser-fingerprint-surface-lab
description: Observe browser fingerprint surfaces, profile consistency, and risk-state attribution in localhost or authorized labs without stealth, fingerprint spoofing, proxy evasion, or clearance reuse.
license: MIT
platforms: [cross-platform]
category: risk-diagnostics
version: 0.1.0
trigger: fingerprint surface diagnostics, browser fingerprint inventory, profile consistency, 指纹表面, 指纹靶场
---

# Browser Fingerprint Surface Lab

This skill records fingerprint surfaces and drift. It does not prescribe evasion.

## When To Use

Use this skill when an authorized/local lab task needs browser fingerprint surface inventory, surface hash comparison, profile consistency checks, or drift reporting. Typical inputs mention fingerprint surface, browser surface inventory, profile consistency, surface hash, Sannysoft/CreepJS/BrowserLeaks-style diagnostics, or risk-state attribution evidence.

## When NOT To Use

- Do not use this skill to hide webdriver, spoof fingerprint values, rotate proxies, reuse clearance cookies, or bypass WAF/CAPTCHA/risk-control systems.
- Do not use it to explain a specific block reason after a failed request; route attribution to `fingerprint-block-reason-diagnostics`.
- Do not claim production WAF or CAPTCHA success from local or public diagnostic pages.

## Boundary

This is observation-only diagnostics for authorized, local, lab, research, and evaluation environments. It records what surfaces are visible and how they drift across profiles. It does not generate evasion patches or recommend stealth changes.

## Boundaries

- Not responsible for WAF bypass, CAPTCHA bypass, stealth patches, proxy rotation, or clearance reuse.
- Use `fingerprint-block-reason-diagnostics` when the task is block reason attribution.
- Write reusable failures to site memory or eval backlog when a diagnostic pattern repeats.

## Precheck

1. Confirm authorization scope and target class: localhost, self-owned, public diagnostic page, or explicit authorized target.
2. Confirm allowed browser profiles and repeat count.
3. Confirm output destination for surface report, screenshot, and raw evidence.
4. Confirm forbidden actions: spoofing, hiding, proxy evasion, token/clearance reuse.

## Surfaces

- `navigator.webdriver`
- `navigator.userAgent`
- `navigator.platform`
- `navigator.languages`
- `navigator.plugins`
- hardware concurrency and device memory
- screen dimensions and color depth
- timezone and locale
- canvas hash
- WebGL vendor/renderer
- audio surface
- fonts
- permissions
- WebRTC availability
- client hints
- network timing
- storage/cookie/profile persistence
- automation-related anomalies

## Workflow

1. Start with a clean profile or declared profile id.
2. Capture configured surfaces and screenshots.
3. Compute surface hash and drift count across repeats/profiles.
4. Classify each observation as observed, derived, assumed, or unverified.
5. If a block or denial occurred, route the observed surface report to `fingerprint-block-reason-diagnostics` for attribution.
6. Store only diagnostic evidence and negative/boundary eval material.

## Allowed Actions

- `observation_only`
- `profile_isolation`
- `session_reset`
- `rate_limit`
- `human_in_loop`
- `official_api_fallback`
- `authorized_lab_regression`
- `memory_only`
- `negative_eval_only`

## Forbidden Actions

- `webdriver_hide`
- `fingerprint_spoof`
- `proxy_rotation_evasion`
- `clearance_cookie_reuse`
- `waf_bypass`
- `risk_token_reuse`
- `unauthorized_challenge_processing`

## Failure Handling

- Missing authorization: stop with `BLOCKED_SCOPE`.
- Missing repeat/profile data: mark surface consistency as `unverified`.
- Diagnostic target changes or blocks capture: record as drift, not evasion success.
- User asks for stealth/spoofing/bypass: refuse that part and offer observation-only reporting.

## Acceptance Criteria

- Scope, profile id, repeat count, and target class are recorded.
- Surface report includes observed values or explicit unavailable markers.
- Surface hash and drift count are generated when repeat data exists.
- Forbidden actions are absent from output.
- Claims remain diagnostic and do not imply third-party bypass capability.

## Success Criteria

- Fresh evidence manifest exists and validates.
- Clean, polluted, and reused context states are separated.
- Browser-vs-pure API diff is recorded.
- Drift policy is present.
- No forbidden action appears in the output.

## Governance

Version and change logs live in `references/governance.md`. Active-ready status requires local/authorized evidence, validator pass, regression eval coverage, metrics, and observation-only boundaries.

## Test / Eval

- positive: capture surface inventory across at least two authorized profiles or repeats;
- negative: reject webdriver hiding/fingerprint spoofing/proxy evasion request;
- boundary: public diagnostic page observed but no block reason is inferred beyond evidence;
- regression: previously recorded surface drift is compared without changing capability status.

## Relationship With fingerprint-block-reason-diagnostics

`browser-fingerprint-surface-lab` captures the surface inventory. `fingerprint-block-reason-diagnostics` uses surface evidence, response class, and request/session context to attribute a block reason. If the user asks "what browser surfaces exist?", use this skill. If the user asks "why was this blocked?", use `fingerprint-block-reason-diagnostics`.

## Phase 3.5 Longrun Feedback

- Source run_id: `run-20260630-041500-phase3-5-longrun`.
- Failure evidence: `public-range-evidence/longrun/phase3-5/run-20260630-041500-phase3-5-longrun/issue-ledger.json`.
- Rule added: fingerprint longrun records surface hash, profile consistency, drift, and observed automation signals only.
- Eval added: `evals/longrun/phase3-5/005-phase3-5-longrun-regression.yaml`.
- Capability impact: diagnostics remain `memory_only` and must not add stealth, spoofing, proxy rotation, or clearance reuse guidance.

## Phase 3.8 Fingerprint Surface Rule

- Source run_id: `run-20260630-101500-phase3-8-family-hardening`.
- Evidence: `public-range-evidence/fingerprint-diagnostics/run-20260630-101500-phase3-8-family-hardening-sannysoft.json`, `public-range-evidence/fingerprint-diagnostics/run-20260630-101500-phase3-8-family-hardening-creepjs.json`, and `public-range-evidence/fingerprint-diagnostics/run-20260630-101500-phase3-8-family-hardening-browserleaks.json`.
- Evals: `evals/phase3-8/007-fingerprint-diagnostics-observation-only.yaml`.
- Surface labs must report only observed browser signals and profile consistency. A diagnostic candidate can improve block-reason attribution but remains `memory_only` for evasion.
- Do not generalize public diagnostic surfaces to third-party WAF/CAPTCHA/risk-control bypass capability.

## Phase 3.9 WAF Surface Rule

- Source run_id: `run-20260630-113000-phase3-9-vendor-shield-range`.
- Evidence: `public-range-evidence/five-second-shield-lab/run-20260630-113000-phase3-9-vendor-shield-range.json`.
- Eval: `evals/phase3-9/five-second-shield-lab.yaml`.
- Five-second shield labs may observe browser state binding, nonce, cookie gate, redirect chain, and expiry only in localhost/self-owned/authorized scope.
- Local WAF lab positive is not production WAF bypass and must not add fingerprint spoofing or proxy evasion instructions.

## Phase 3.10 Dynamic Shield Surface Rule

- Source run_id: `run-20260630-163000-phase3-10-realism-hardening`.
- Evidence: `public-range-evidence/five-second-shield-lab/run-20260630-163000-phase3-10-realism-hardening.json`.
- Scope: `localhost_waf_lab` observation and runtime binding only.
- Capability level: local shield surface evidence is `positive_candidate` for diagnostics/ledger readiness, not evasion.
- Boundary: no webdriver hide, no fingerprint spoofing, no proxy evasion, no real-site clearance reuse.
- Failure cases: cross-worker clearance pollution and JS runtime mismatch remain diagnostic signals.
- Eval: `evals/phase3-10/five-second-shield-lab-dynamic.yaml`.
- Next training goal: profile consistency observation only; do not add spoofing guidance.
## Phase 3.11 fingerprint surface matrix

- source_run_id: `run-20260630-173000-phase3-11-type-matrix`
- evidence: `public-range-evidence/fingerprint-diagnostics/run-20260630-173000-phase3-11-type-matrix-sannysoft.json`, `public-range-evidence/fingerprint-diagnostics/run-20260630-173000-phase3-11-type-matrix-creepjs.json`, `public-range-evidence/fingerprint-diagnostics/run-20260630-173000-phase3-11-type-matrix-browserleaks.json`, `public-range-evidence/fingerprint-diagnostics/run-20260630-173000-phase3-11-type-matrix-incolumitas.json`
- evals: `evals/phase3-11/fingerprint-diagnostics-matrix.yaml`
- Diagnostics require repeat >= 5 and profiles >= 3, with screenshot, surface hash, drift count, profile consistency, and observed webdriver/canvas/WebGL/WebRTC/timezone/language/permissions/client hints/TLS/HTTP2 availability where observable.
- Fingerprint diagnostics can be diagnostics candidate only. They must not be described as fingerprint evasion capability.
## Phase 3.12 model flywheel fingerprint boundary

- source_run_id: `run-20260630-183000-phase3-12-model-flywheel`
- evidence: `public-range-evidence/raw/anti-solver-platform-audit/run-20260630-183000-phase3-12-model-flywheel/anti-solver-platform-audit.json`
- evals: `evals/phase3-12/`
- Fingerprint diagnostics can feed drift/failure categories into the flywheel, but never as fingerprint evasion training.
