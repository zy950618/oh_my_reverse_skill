# Authorized Target Adapter Governance

Version: 0.1.1

This reference binds authorized-target adaptation to explicit scope, final business data, and drift-resistant evidence.

## Workflow

- Read `configs/range_scope_contract.yaml`.
- Use local WAF/shield candidate evidence as the scoped vendor/shield boundary example.
- Require final business API acceptance, repeat direct call, concurrency ladder, stop condition, kill switch, and redaction before any positive adapter claim.

## Success Criteria

- `business_data_status=DATA_ASSERTION_PASS`.
- 1/2/5/10 worker business API ladder passes with isolated session/cookie/token/cache.
- Negative cases have zero ledger delta.
- Capability status stays candidate/verified according to the scope, business-data, real-execution, and public-range evidence gates: `tools/evidence/validate_scope_contract.py`, `tools/evidence/validate_business_data_assertions.py`, `tools/evidence/validate_real_execution_proof.py`, and `tools/evidence/validate_public_range_evidence.py`.

## Boundaries

This skill is not responsible for WAF defeat, fingerprint falsification, challenge defeat, proxy avoidance, token forgery, or clearance-cookie recycling on production-unverified targets.

## Governance

Known failures and eval backlog must cite run_id, evidence path, and scope decision. Drift requires rerunning validators before promotion.
