# Authorized Target Adapter Governance

Version: 0.1.1

This reference binds authorized-target adaptation to explicit scope, final business data, and drift-resistant evidence.

## Workflow

- Read `configs/range_scope_contract.yaml`.
- Use `public-range-evidence/five-second-shield-lab/run-20260630-113000-phase3-9-vendor-shield-range.json` as the Phase 3.9 local WAF/shield candidate example.
- Require final business API acceptance, repeat direct call, concurrency ladder, stop condition, kill switch, and redaction before any positive adapter claim.

## Success Criteria

- `business_data_status=DATA_ASSERTION_PASS`.
- 1/2/5/10 worker business API ladder passes with isolated session/cookie/token/cache.
- Negative cases have zero ledger delta.
- Capability status stays candidate/verified according to `tools/capability_promotion_gate.py`.

## Boundaries

This skill is not responsible for WAF bypass, fingerprint spoofing, CAPTCHA bypass, proxy evasion, token forgery, or clearance reuse on production-unverified targets.

## Governance

Known failures and eval backlog must cite run_id, evidence path, and scope decision. Drift requires rerunning validators before promotion.
