# Knowledge Graph

Nodes:

- domain: airline-lab-order-flow, status: observed, evidence:
  `public-range-evidence/airline-lab-order-flow/`
- stage: search, status: observed, evidence: `fixtures/search_response.json`
- stage: detail, status: observed, evidence: `fixtures/detail_response.json`
- stage: order, status: observed, evidence: `fixtures/order_response.json`
- eval: deep_validation, status: observed, evidence: `tests/run_order_flow_tests.py`
- protection: none, status: unverified, evidence: structure-only scaffold
- protection: captcha_required_state, status: observed, evidence:
  `reports/deep_validation_report.json`
- protection: fingerprint_challenge_state, status: observed, evidence:
  `reports/deep_validation_report.json`

Edges:

- airline-lab-order-flow -> search: local fixture stage only.
- search -> detail: `session_id` and `flight_id` connect fixtures.
- detail -> order: `detail_nonce` connects fixtures.
- order -> business-ledger: `ledger_delta` placeholder only; no live ledger run.
- deep_validation -> search/detail/quote/passenger/order: in-process localhost
  mock server checks valid, invalid, duplicate, sign, captcha, and fingerprint states.
