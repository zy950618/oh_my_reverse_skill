# 7-指纹风控层

Status: advisory

This layer is included in CI scoring output through
`99-SKILLS治理/skill-score-rubric.yaml`, but it is not an active delivery layer
until its Skills reach the active threshold with references, evals, fixtures,
and drift evidence.

## Allowed Scope

- Authorized fingerprint surface diagnostics.
- Block reason diagnostics.
- Runtime parity observation.
- Regression evidence for local, self-owned, public-range, or explicitly
  authorized labs.

## Forbidden Scope

- WAF bypass.
- CAPTCHA bypass.
- Fingerprint spoofing.
- Webdriver hiding.
- Detection evasion.
- Risk token forgery.
- Clearance cookie reuse.
- Unauthorized third-party site breakthrough.

## Promotion Rule

To become active, each Skill in this layer must score at least 70 under
`structure / operational / consistency / drift`, include positive/negative/
regression evals, and preserve the forbidden-scope boundary above.
