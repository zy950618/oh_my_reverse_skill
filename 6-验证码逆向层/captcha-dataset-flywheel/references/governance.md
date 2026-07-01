# CAPTCHA Dataset Flywheel Governance

Version: 0.1.1

## Scope

This skill governs local, self-owned, public-range, or explicitly authorized CAPTCHA
dataset feedback loops. It keeps labels, failures, splits, leakage checks, model
outputs, and action replay feedback traceable.

## Required Records

- source run id and target id.
- dataset family and difficulty.
- image, crop, or screenshot path.
- instruction and allowed action schema.
- label and label source.
- train/validation/test split.
- leakage audit result.
- model output and action replay feedback when available.
- failure reason and next regression eval.

## Boundary

Dataset improvement is not third-party CAPTCHA/WAF/risk-control success. Positive
capability requires separate execution, control-flow, business-data, and scope
gates. Remote solver services, copied provider tokens, DOM answers, expected
answers, clearance cookies, fingerprint spoofing, and evasion material are
forbidden.
