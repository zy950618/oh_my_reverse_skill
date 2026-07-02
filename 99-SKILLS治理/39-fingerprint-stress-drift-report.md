# Fingerprint Stress and Drift Report

## State

- Agent: Agent 4 - Fingerprint Stress & Drift Agent
- State: VERIFIED_LOCAL_FINGERPRINT_STRESS
- Scope: local fingerprint-risk lab evidence only
- No commit: OBSERVED, no commit command was run
- No push: OBSERVED, no push command was run
- Live third-party fingerprint/WAF/CAPTCHA success: NOT VERIFIED

## Changed Paths

- `public-range-evidence/fingerprint-risk-lab/drift_cases/drift_cases.json`
- `public-range-evidence/fingerprint-risk-lab/drift_cases/validate_drift_cases.py`
- `public-range-evidence/fingerprint-risk-lab/drift_cases/run_fingerprint_repeat.py`
- `public-range-evidence/fingerprint-risk-lab/repeat_reports/drift_negative_validation_report.json`
- `public-range-evidence/fingerprint-risk-lab/repeat_reports/fingerprint_repeat_rounds.json`
- `99-SKILLS治理/39-fingerprint-stress-drift-report.md`

## Drift and Negative Cases

All required drift/negative cases are present and classified as expected local-lab rejection cases:

- `missing_webdriver_field`
- `inconsistent_user_agent_platform`
- `timezone_language_mismatch`
- `dirty_storage_leak`
- `reused_context_leak`
- `missing_canvas_surface`
- `missing_webgl_surface`
- `unknown_block_reason`
- `captcha_linkage_missing`
- `browser_vs_pure_api_diff_missing`

Validation result:

- Command: `python public-range-evidence\fingerprint-risk-lab\drift_cases\validate_drift_cases.py --write-report public-range-evidence\fingerprint-risk-lab\repeat_reports\drift_negative_validation_report.json`
- Result: PASS
- Evidence: `case_count=10`, all 10 cases classified, all 10 cases rejected, `failures=[]`
- Note: an initial helper run rejected the first draft because one safe-next-action phrase contained forbidden action language. The case file was corrected and rerun to PASS.

## Five-Round Fingerprint Repeat

Runner command:

```text
python public-range-evidence\fingerprint-risk-lab\drift_cases\run_fingerprint_repeat.py --rounds 5
```

Runner environment:

- `PYTHONDONTWRITEBYTECODE=1`

Commands run per round:

- `python tools\validate_fingerprint_surface_lab.py`
- `python tools\validate_block_reason_lab.py`
- `python tools\validate_browser_context_isolation.py`
- `python tools\validate_captcha_fingerprint_linkage.py`
- `python public-range-evidence\fingerprint-risk-lab\drift_cases\validate_drift_cases.py`

Observed repeat result:

- rounds_requested: 5
- rounds_passed: 5
- rounds_failed: 0
- fingerprint_lab_repeat_stable: true
- report: `public-range-evidence/fingerprint-risk-lab/repeat_reports/fingerprint_repeat_rounds.json`

Round summary:

| Round | Surface | Block reason | Context isolation | CAPTCHA linkage | Drift helper | Result |
|---:|---|---|---|---|---|---|
| 1 | PASS | PASS | PASS | PASS | PASS | PASS |
| 2 | PASS | PASS | PASS | PASS | PASS | PASS |
| 3 | PASS | PASS | PASS | PASS | PASS | PASS |
| 4 | PASS | PASS | PASS | PASS | PASS | PASS |
| 5 | PASS | PASS | PASS | PASS | PASS | PASS |

## Layer-7 Score Regression

Baseline source:

- `.ci-out/7-指纹风控层.json`

Observed scores after fingerprint stress artifacts:

- `browser-fingerprint-surface-lab`: 100
- `fingerprint-block-reason-diagnostics`: 100

Result:

- score_regression: false
- no layer-7 score regression: VERIFIED

## Evidence Boundary

- OBSERVED: local validators passed repeatedly against local evidence and observation packs.
- VERIFIED: drift cases are classified and rejected by the local helper.
- VERIFIED: 5 / 5 fingerprint rounds passed.
- NOT VERIFIED: live production airline, live third-party CAPTCHA, live WAF, or production fingerprint success.
- ASSUMPTION: `.ci-out/7-指纹风控层.json` is the intended score artifact for this Agent 4 regression check because the user allowed checking it instead of rerunning score.

## Remaining

- P0: none for Agent 4 fingerprint stress/drift scope.
- P1: live authorized fingerprint/WAF/CAPTCHA production behavior remains NOT VERIFIED and outside this local-lab task.
- P2: global third-loop final state still depends on other agents' repeated release, core, CAPTCHA, airline, artifact reference, cleanup, and diff-review gates.
