# Governance

## Version

Current version: 0.2.2

## Change Log

- 0.1.0: Initial website-to-314 delivery Skill with intake, routing, 314 integration, delivery checklist, and evals.
- 0.2.0: Added site memory, market-specific handling, test-log mining, GitHub CI workflow guidance, and regression evals for repeated same-site mistakes.
- 0.2.1: Added Qatar Airways regression for HTTP 200 Akamai challenge responses that must not be counted as successful 314 business-interface delivery.
- 0.2.2: Added Qatar Airways sec_cpt/AkamaiGHost regression so detailed Akamai challenge fingerprints remain classified as protection, not 314 success.

## Drift Tests

Run evals when:

- a new website category is added
- 314 framework assumptions change
- payment/order semantics change
- a real task exposes a missed trigger or false trigger
- a WAF or anti-bot flow changes behavior

Track:

- trigger pass rate
- negative trigger pass rate
- stage coverage
- test coverage
- real-task completion rate

## Long-Term Governance

Every completed website should feed at least one of:

- a new reference note
- a new eval
- a trigger description update
- a route classification rule
- a known failure pattern
