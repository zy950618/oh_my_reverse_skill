# CAPTCHA Open-Source Model Stack Governance

Version: 0.1.1

## Scope

This skill selects and evaluates local or open-source model families for
authorized CAPTCHA labs before action execution.

## Required Gates

- authorization scope.
- dataset provenance and split policy.
- leakage audit status.
- challenge family and output type.
- benchmark metrics and thresholds.
- downstream route to action replay.

## Boundary

Model selection and offline metrics are not third-party CAPTCHA/WAF/risk-control
success. The skill must not provide token generation, clearance reuse, remote
solver automation, fingerprint spoofing, webdriver hiding, or evasion guidance.
