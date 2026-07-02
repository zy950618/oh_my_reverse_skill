# CAPTCHA Repeat and Negative Case Report

## Scope

- Agent: Agent 3 CAPTCHA Repeat & Negative Case Agent.
- Owned evidence paths:
  - `public-range-evidence/captcha-model-lab/negative_cases/`
  - `public-range-evidence/captcha-model-lab/repeat_reports/`
  - `99-SKILLS治理/38-captcha-repeat-and-negative-report.md`
- NO_COMMIT: true.
- NO_PUSH: true.
- Capability boundary: local synthetic CAPTCHA lab only.

## Repeat Run Summary

- VERIFIED: `10 / 10` repeat rounds passed.
- VERIFIED: `0` repeat rounds failed.
- VERIFIED: each round ran with `PYTHONDONTWRITEBYTECODE=1`.
- VERIFIED: each round produced `3` predictions.
- VERIFIED: each round produced pass-rate `1.0`.
- VERIFIED: each round passed the negative-case validator.
- Evidence:
  - `public-range-evidence/captcha-model-lab/repeat_reports/captcha_repeat_rounds.json`
  - `public-range-evidence/captcha-model-lab/repeat_reports/round-01.json` through `round-10.json`

## Commands

Each command below was executed once per round for 10 rounds by
`public-range-evidence/captcha-model-lab/negative_cases/run_repeat.py`.

| command | runs | passed | failed |
|---|---:|---:|---:|
| `python public-range-evidence\captcha-model-lab\inference\sample_infer.py` | 10 | 10 | 0 |
| `python public-range-evidence\captcha-model-lab\eval\evaluate_pass_rate.py` | 10 | 10 | 0 |
| `python tools\validate_captcha_action_schema.py` | 10 | 10 | 0 |
| `python tools\validate_captcha_dataset.py` | 10 | 10 | 0 |
| `python tools\validate_captcha_training_report.py` | 10 | 10 | 0 |
| `python tools\validate_captcha_model_package.py` | 10 | 10 | 0 |
| `python tools\validate_captcha_pass_rate.py` | 10 | 10 | 0 |
| `python public-range-evidence\captcha-model-lab\negative_cases\validate_negative_cases.py` | 10 | 10 | 0 |

## Prediction Stability

- VERIFIED: prediction count was stable: `[3, 3, 3, 3, 3, 3, 3, 3, 3, 3]`.
- VERIFIED: prediction statuses stayed `ok`.
- VERIFIED: valid sample count stayed `3`.
- VERIFIED: no external CAPTCHA provider, remote solver API, provider token, or live challenge was used.

## Pass-Rate Stability

- VERIFIED: pass rates were stable: `[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]`.
- VERIFIED: each round evaluated `3` attempts and `3` passes.
- VERIFIED: valid samples still pass in the negative-case validator.

## Negative Case Detections

| case | expected reason | observed reason | result |
|---|---|---|---|
| `invalid_image_size` | `image_size_invalid` | `image_size_invalid` | PASS |
| `missing_label` | `label_missing` | `label_missing` | PASS |
| `bad_coordinate_out_of_bounds` | `coordinate_out_of_bounds` | `coordinate_out_of_bounds` | PASS |
| `bad_slider_offset` | `slider_offset_out_of_tolerance` | `slider_offset_out_of_tolerance` | PASS |
| `wrong_captcha_type` | `unsupported_captcha_type` | `unsupported_captcha_type` | PASS |
| `low_confidence_prediction` | `confidence_below_threshold` | `confidence_below_threshold` | PASS |
| `missing_model_artifact` | `model_artifact_missing` | `model_artifact_missing` | PASS |
| `broken_package_manifest` | `package_manifest_invalid` | `package_manifest_invalid` | PASS |
| `mobile_h5_dpr_mismatch` | `mobile_h5_dpr_mismatch` | `mobile_h5_dpr_mismatch` | PASS |

## Changed Artifact Index

- `public-range-evidence/captcha-model-lab/negative_cases/cases.json`
  - Records 9 local-lab negative fixtures and expected rejection reasons.
- `public-range-evidence/captcha-model-lab/negative_cases/validate_negative_cases.py`
  - Validates negative fixture rejection reasons and confirms valid samples still pass.
- `public-range-evidence/captcha-model-lab/negative_cases/run_repeat.py`
  - Runs the 10-round command loop with `PYTHONDONTWRITEBYTECODE=1`.
- `public-range-evidence/captcha-model-lab/repeat_reports/captcha_repeat_rounds.json`
  - Machine-readable 10-round summary.
- `public-range-evidence/captcha-model-lab/repeat_reports/round-01.json` through `round-10.json`
  - Per-round command evidence.

## Boundary

- NOT VERIFIED: live third-party CAPTCHA success.
- NOT VERIFIED: third-party WAF success.
- NOT VERIFIED: production fingerprint or token behavior.
- OBSERVED: this report proves only deterministic local synthetic CAPTCHA lab repeat stability and negative-case rejection.

## Result

- Agent 3 result: PASS.
- Reason: 10 / 10 repeat rounds passed, pass-rate stayed stable, negative cases were rejected with explicit expected reasons, and valid samples still passed.
