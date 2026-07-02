# Block Taxonomy Contract

## Purpose

Classify observed block reasons without evasion instructions.

## Required Classes

- `no_block`
- `fingerprint_challenge_detected`
- `waf_challenge_detected`
- `pure_api_replay_blocked`
- `pure_api_replay_ready`
- `unknown`

## Evidence

Each classification requires response class, context state, and fact label: observed, derived, assumed, or unverified.

## Boundary

No webdriver hiding, fingerprint spoofing, proxy evasion, clearance reuse, risk-token reuse, WAF bypass, or CAPTCHA bypass.
