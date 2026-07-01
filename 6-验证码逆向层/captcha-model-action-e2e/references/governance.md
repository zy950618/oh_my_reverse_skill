# CAPTCHA Model Action E2E Governance

Version: 0.1.1

## Scope

This skill validates whether local or open-source model predictions can drive
authorized action replay inside localhost, self-owned, public-range allowlisted,
or explicitly authorized lab scopes.

## Required Gates

- scope contract.
- upstream model artifact and prediction schema.
- deterministic action plan.
- positive replay and negative controls.
- failure replay.
- leakage audit.
- promotion decision.

## Boundary

Action replay success is scoped evidence only. It is not third-party CAPTCHA,
WAF, or risk-control bypass. Provider token reuse, clearance-cookie reuse,
remote solver automation, fingerprint spoofing, webdriver hiding, and proxy
evasion are prohibited.
