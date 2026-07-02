# Airline Lab Stress Report

## Scope

- Agent: Agent 5 - Airline Lab Deep Stress Agent
- Owned paths changed:
  - `public-range-evidence/airline-lab-order-flow/negative_cases/`
  - `public-range-evidence/airline-lab-order-flow/repeat_reports/`
  - `public-range-evidence/airline-lab-order-flow/tests/`
  - `99-SKILLS治理/40-airline-lab-stress-report.md`
- Commit/push/revert: NOT PERFORMED
- Live airline calls: NOT PERFORMED
- Browser dependency: NOT OBSERVED

## Evidence Labels

- OBSERVED: Local fixture replay command returned PASS.
- OBSERVED: Local in-process order-flow test command returned PASS with 13 cases.
- OBSERVED: Pure API delivery validator returned PASS for `public-range-evidence/airline-lab-order-flow`.
- OBSERVED: Negative-case checker returned PASS with 12 cases.
- VERIFIED: 10 repeated airline stress rounds passed with `PYTHONDONTWRITEBYTECODE=1`.
- NOT VERIFIED: Any real airline production endpoint behavior.
- NOT VERIFIED: Any live CAPTCHA, WAF, or production fingerprint behavior.

## Negative Cases

Source manifest:

- `public-range-evidence/airline-lab-order-flow/negative_cases/manifest.json`

Validation report:

- `public-range-evidence/airline-lab-order-flow/repeat_reports/negative_case_report.json`

| case | detection_mode | expected_result | observed_result |
|---|---|---|---|
| invalid_route | localhost_http | 422 invalid_route | PASS |
| invalid_date | local_preflight_classifier | rejected_before_http invalid_date | PASS |
| expired_token | localhost_http | 409 expired_or_invalid_detail_token | PASS |
| invalid_sign | localhost_http | 403 invalid_sign | PASS |
| missing_passenger | localhost_http | 422 invalid_passenger | PASS |
| invalid_passenger_doc | localhost_http | 422 invalid_passenger | PASS |
| duplicate_draft | localhost_http_sequence | 409 duplicate_order | PASS |
| confirm_without_draft | localhost_http | 409 invalid_order_state | PASS |
| cancel_nonexistent_order | localhost_http | 404 order_not_found | PASS |
| captcha_required_state | localhost_http | 403 captcha_required | PASS |
| fingerprint_challenge_state | localhost_http | 403 fingerprint_challenge | PASS |
| replay_mismatch | fixture_pointer_mismatch | rejected_by_fixture_check replay_mismatch | PASS |

Boundary note:

- `invalid_date` is classified by local preflight logic because `mock_server/server.py` is outside Agent 5 owned paths and does not currently model date parsing.
- `replay_mismatch` is classified by fixture pointer mismatch detection without changing the passing replay plan.

## Repeated Stress

Repeat report:

- `public-range-evidence/airline-lab-order-flow/repeat_reports/airline_repeat_stress_report.json`

Settings:

- rounds_requested: 10
- rounds_passed: 10
- rounds_failed: 0
- `PYTHONDONTWRITEBYTECODE`: 1
- live_site_calls_performed: false
- browser_dependency: false

Commands per round:

```text
python public-range-evidence\airline-lab-order-flow\replay\replay.py
python public-range-evidence\airline-lab-order-flow\tests\run_order_flow_tests.py
python tools\validate_pure_api_delivery.py public-range-evidence/airline-lab-order-flow
python public-range-evidence\airline-lab-order-flow\tests\run_negative_case_checks.py
```

Result:

- replay: 10 / 10 PASS
- order-flow tests: 10 / 10 PASS
- pure API delivery validator: 10 / 10 PASS
- negative-case checker: 10 / 10 PASS

## Valid Flow Evidence

Source report:

- `public-range-evidence/airline-lab-order-flow/reports/deep_validation_report.json`

Observed valid cases:

- `valid_search`: 200, `status=ok`, non-empty `flights`, first `flight_id=LAB-MH-001`
- `quote_success`: 200, `quote_id=LAB-QUOTE-001`
- `passenger_valid`: 200, `passenger_validation_id=LAB-PAX-001`
- `draft_order_success`: 200, `order_state=draft`
- `confirm_order_success`: 200, `order_state=confirmed`, `ledger_delta=1`, `payment_required=false`
- `cancel_order_success`: 200, `order_state=cancelled`, `ledger_delta=-1`

## Invalid Flow Evidence

Observed invalid behavior:

- Invalid request paths returned expected non-2xx responses or local classifier rejection.
- HTTP negative cases returned explicit `error` fields.
- Negative ledger delta expectation remained `0` for rejection paths in the deep validation report.

## Cancel State Consistency

- OBSERVED: `cancel_order_success` returned `order_state=cancelled`.
- OBSERVED: `cancel_order_success` returned `ledger_delta=-1`.
- VERIFIED: The above was checked in all 10 repeated `run_order_flow_tests.py` rounds.

## Browser Dependency

- OBSERVED: `deep_validation_report.json` reports `browser_profile_dependency=false`.
- OBSERVED: `airline_repeat_stress_report.json` reports `browser_dependency=false`.
- OBSERVED: `validate_pure_api_delivery.py public-range-evidence/airline-lab-order-flow` passed in 10 / 10 rounds.

## Commands Actually Run

Initial scoped checks:

```text
PYTHONDONTWRITEBYTECODE=1 python public-range-evidence\airline-lab-order-flow\tests\run_negative_case_checks.py
PASS: 12 cases

PYTHONDONTWRITEBYTECODE=1 python public-range-evidence\airline-lab-order-flow\replay\replay.py
PASS: failures=[]

PYTHONDONTWRITEBYTECODE=1 python public-range-evidence\airline-lab-order-flow\tests\run_order_flow_tests.py
PASS: 13 cases

PYTHONDONTWRITEBYTECODE=1 python tools\validate_pure_api_delivery.py public-range-evidence/airline-lab-order-flow
PASS
```

Repeated stress:

```text
PYTHONDONTWRITEBYTECODE=1 python public-range-evidence\airline-lab-order-flow\tests\run_airline_repeat_stress.py --rounds 10
PASS: rounds_passed=10, rounds_failed=0
```

## Result

- Airline stress runs: 10
- Test cases per `run_order_flow_tests.py`: 13
- Negative cases in manifest: 12
- Valid flows pass: VERIFIED_LOCAL
- Invalid flows rejected or classified with expected reason: VERIFIED_LOCAL
- Cancel state consistency: VERIFIED_LOCAL
- No browser dependency appears: VERIFIED_LOCAL

## Remaining

- P0: none for Agent 5 owned airline lab stress scope.
- P1: live airline production execution remains NOT VERIFIED.
- P2: `invalid_date` is classification-only unless a future owner updates `mock_server/server.py` to model date parsing.
