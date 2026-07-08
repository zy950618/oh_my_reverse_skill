---
name: browser-fingerprint-surface-lab
standard_type: conditional_escalation
description: Observe browser fingerprint surfaces, profile consistency, and risk-state attribution in localhost or authorized labs without concealment, fingerprint falsification, proxy avoidance, or clearance-cookie recycling.
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

- Do not use this skill to conceal webdriver, forge fingerprint values, rotate proxies, recycle clearance-cookies, or defeat WAF/challenge/risk-control systems.
- Do not use it to explain a specific block reason after a failed request; route attribution to `fingerprint-block-reason-diagnostics`.
- Do not claim production WAF or challenge success from local or public diagnostic pages.

## Boundary

This is observation-only diagnostics for authorized, local, lab, research, and evaluation environments. It records what surfaces are visible and how they drift across profiles. It does not generate evasion patches or recommend concealment changes.

## Boundaries

- Not responsible for WAF defeat, challenge defeat, concealment patches, proxy rotation, or clearance-cookie recycling.
- Use `fingerprint-block-reason-diagnostics` when the task is block reason attribution.
- Write reusable failures to site memory or eval backlog when a diagnostic pattern repeats.

## Precheck

1. Confirm authorization scope and target class: localhost, self-owned, public diagnostic page, or explicit authorized target.
2. Confirm allowed browser profiles and repeat count.
3. Confirm output destination for surface report, screenshot, and raw evidence.
4. Confirm forbidden actions: falsification, hiding, proxy avoidance, token/clearance-cookie recycling.

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
- `waf_defeat`
- `risk_token_reuse`
- `unauthorized_challenge_processing`

## Failure Handling

- Missing authorization: stop with `BLOCKED_SCOPE`.
- Missing repeat/profile data: mark surface consistency as `unverified`.
- Diagnostic target changes or blocks capture: record as drift, not evasion success.
- User asks for concealment/falsification/defeat: refuse that part and offer observation-only reporting.

## Acceptance Criteria

- Scope, profile id, repeat count, and target class are recorded.
- Surface report includes observed values or explicit unavailable markers.
- Surface hash and drift count are generated when repeat data exists.
- Forbidden actions are absent from output.
- Claims remain diagnostic and do not imply third-party defeat capability.

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
- negative: reject webdriver concealment/fingerprint falsification/proxy avoidance request;
- boundary: public diagnostic page observed but no block reason is inferred beyond evidence;
- regression: previously recorded surface drift is compared without changing capability status.

## Relationship With fingerprint-block-reason-diagnostics

`browser-fingerprint-surface-lab` captures the surface inventory. `fingerprint-block-reason-diagnostics` uses surface evidence, response class, and request/session context to attribute a block reason. If the user asks "what browser surfaces exist?", use this skill. If the user asks "why was this blocked?", use `fingerprint-block-reason-diagnostics`.

## Auxiliary Policy

- Engineering discipline follows `4-通用规范层/karpathy-guidelines/SKILL.md`.
