## Purpose
Evaluate CAPTCHA model or action replay pass rates with reproducible metrics and failure accounting.

## Allowed Scope
- Local lab, authorized benchmark, or approved public-range evidence.
- Do not equate local pass rate with real third-party business acceptance.

## Inputs
- Prediction or action replay results.
- Evaluation config and metric thresholds.
- Dataset or challenge manifest.

## Outputs
- Pass-rate report, metric trends, and failure-case ledger.
- Promotion or rejection recommendation with evidence class.

## Evidence Files
- `pass-rate-report.json`
- `metric-trends.json`
- `failure-cases.json`
- `promotion-decision.md`

## Command Examples
```powershell
python tools/captcha_model_eval.py --config <config> --out <evidence_dir>
```

## Failure Modes
- Evaluation samples overlap with training data.
- Pass metric ignores retries or partial failures.
- Promotion decision exceeds evidence scope.

## Retry Strategy
- Re-run on clean holdout or fresh challenge set.
- Recompute metrics after fixing failure classification.

## Cleanup Rules
- Keep raw metrics needed to reproduce aggregate results.
- Remove duplicate reports from superseded runs.

## Acceptance Checks
- Report includes denominator, retry policy, and failure taxonomy.
- Promotion status matches the evidence boundary.

## Related Skills
- `captcha-algorithm-benchmark`
- `captcha-model-action-e2e`
- `skills-evaluation-governance`
