# CAPTCHA Pass-Rate Report

- OBSERVED: evaluated `3` synthetic local-lab samples.
- VERIFIED: `3` predictions passed within label tolerance.
- VERIFIED: pass_rate = `1.000000`.
- NOT VERIFIED: third-party CAPTCHA, WAF, or managed challenge success.

| sample_id | split | expected | predicted | error | tolerance | status |
|---|---:|---:|---:|---:|---:|---|
| sample-slider-001 | train | 135 | 135 | 0 | 3 | PASS |
| sample-slider-002 | validation | 135 | 135 | 0 | 3 | PASS |
| sample-slider-003 | test | 135 | 135 | 0 | 3 | PASS |

