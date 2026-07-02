# Impact Regression

change_id: airline-lab-order-flow-scaffold
date: 2026-07-01
changed_node: local airline lab fixtures and validation scaffold
changed_edge: search -> detail -> order fixture flow
change_type: add
evidence: fixture files and replay plan under `public-range-evidence/airline-lab-order-flow/`
direct_impact: adds local scaffold for future validators
downstream_impact: no production or real-site impact
required_regression: run `python public-range-evidence/airline-lab-order-flow/replay/replay.py`
data_validation: JSON Pointer presence checks only
drift_risk: low for scaffold, unknown for future real-site observations
rollback: remove this scaffold if superseded by an authorized lab package
owner_notes: structure-only; no real airline calls

change_id: airline-lab-order-flow-deep-validation
date: 2026-07-01
changed_node: local airline lab mock server and deep validation tests
changed_edge: search -> quote -> passenger -> draft -> confirm -> cancel plus negative states
change_type: add
evidence: `tests/run_order_flow_tests.py` and `reports/deep_validation_report.json`
direct_impact: adds deterministic localhost checks for requested happy-path and rejection states
downstream_impact: no production or real-site impact; local scaffold behavior now rejects duplicate draft orders
required_regression: run `python public-range-evidence/airline-lab-order-flow/tests/run_order_flow_tests.py`
data_validation: response status, error markers, order state, and ledger_delta checks
drift_risk: low for local scaffold, unknown for future real-site observations
rollback: revert local mock behavior and deep validation report if superseded by an authorized lab package
owner_notes: local-only; no live airline calls, no payment, no account, no CAPTCHA/WAF bypass
