---
name: fingerprint-block-reason-diagnostics
standard_type: conditional_escalation
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
- Do not use it to conceal webdriver, forge fingerprints, rotate proxies, reuse clearance, or defeat rate limits.
- Do not use it to claim production WAF/challenge success from local diagnostics.

## Boundary

This is an attribution skill. It can classify observed, derived, assumed, and unverified block reasons, then recommend stop/ask/official API fallback/human review. It must not produce concealment patches, falsification recipes, token reuse instructions, or evasion playbooks.

## Boundaries

- Not responsible for browser surface inventory; use `browser-fingerprint-surface-lab`.
- Not responsible for WAF defeat, challenge defeat, webdriver concealment, fingerprint falsification, proxy avoidance, clearance-cookie recycling, or risk token reuse.
- Write reusable failure modes to site memory or eval backlog.

## Precheck

1. Confirm authorization scope and target class.
2. Collect status code, response class, request/session context, and timing.
3. Collect browser surface report if fingerprint attribution is in scope.
4. Identify whether the claim is observed, derived, assumed, or unverified.
5. Confirm no policy-evasion action is requested.

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

Do not generate concealment patches, webdriver concealment, fingerprint forgery, proxy rotation, or rate-limit evasion.

## Failure Handling

- Missing authorization or target context: stop with `BLOCKED_SCOPE`.
- Missing response evidence: mark attribution `unverified` and request capture/ledger evidence.
- Conflicting signals: record each signal separately and avoid a single-root-cause claim.
- User asks for evasion: refuse that part and provide diagnostic-only alternatives.

## Acceptance Criteria

- Diagnostic ledger includes scope, response evidence, observed signals, and attribution level.
- Each block reason is labeled observed, derived, assumed, or unverified.
- Output contains no concealment, falsification, proxy avoidance, token reuse, or rate-limit defeat steps.
- Safe next action is explicit.

## Success Criteria

- Block taxonomy is evidence-backed.
- challenge/fingerprint linkage is diagnostic-only.
- Incomplete evidence remains `unverified`.
- Fresh validation report exists.
- No forbidden action appears in the output.

## Governance

Version and change logs live in `references/governance.md`. Active-ready status requires local/authorized evidence, validator pass, negative/boundary eval coverage, metrics, and observation-only boundaries.

## Test / Eval

- positive: classify a localhost block with status code, response class, and surface report;
- negative: reject webdriver concealment or proxy avoidance request;
- boundary: incomplete evidence produces `unverified` rather than a guessed root cause;
- regression: repeated known block reason maps to the same safe next action.

## Relationship With browser-fingerprint-surface-lab

Use `browser-fingerprint-surface-lab` to capture the surface inventory and drift. Use this skill to explain a block reason from that evidence plus request/session context. This skill consumes surface reports; it does not modify browser surfaces.

## Auxiliary Policy

- Engineering discipline follows `4-通用规范层/karpathy-guidelines/SKILL.md`.
