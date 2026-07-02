# Core Validator Stress Report

## Scope

OBSERVED: Agent 2 first found a real failed gate: `verify_delivery.py --domain none` failed 5 / 5 because `.ci-out` score files were stale.

FIXED: The supervisor refreshed `.ci-out` by rerunning `score_skills.py` for layers 1, 2, 4, 5, 6, and 7. `score_skills.py` was also patched to skip non-object JSON and dedicated lab/internal artifact JSON while scanning public-range evidence.

## Final Repeated Result

State: VERIFIED_LOCAL_CORE_VALIDATORS

- repeated_core_validator_rounds: 5
- full_rounds_passed: 5 / 5
- command_runs_total: 35
- command_runs_passed: 35
- command_runs_failed: 0
- nondeterministic_failures: 0

## Commands

Each of the following commands passed in each of 5 rounds:

- `python tools\verify_delivery.py --domain none`
- `python tools\fixture_freshness_report.py 站点经验库`
- `python tools\validate_web_h5_crawler_gate.py`
- `python tools\validate_web_h5_loop_gate.py`
- `python tools\validate_web_h5_real_execution_gate.py`
- `python tools\validate_pure_api_delivery.py public-range-evidence/pure-api-lab`
- `python tools\validate_pure_api_delivery.py public-range-evidence/airline-lab-order-flow`

## Evidence

OBSERVED: The final repeated loop produced 35 PASS command runs and 0 FAIL command runs.

OBSERVED: `verify_delivery.py --domain none` exits 0 after the score refresh. It still reports the expected honesty boundary that final answers must list unverified items and limitations.

## Boundary

This validates local core validators only. It does not verify live airline production execution or live third-party CAPTCHA/WAF/fingerprint success.
