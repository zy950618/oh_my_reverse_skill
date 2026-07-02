## Purpose
Train or fine-tune a local CAPTCHA model using governed datasets and reproducible metrics.

## Allowed Scope
- Local, authorized, or benchmark training only.
- Do not claim third-party challenge pass capability from local metrics alone.

## Inputs
- Dataset manifest and splits.
- Training config, model family, and compute limits.
- Evaluation metric requirements.

## Outputs
- Model artifact, training log, metrics, and failure samples.
- Reproducibility notes with config and code version.

## Evidence Files
- `training-config.yaml`
- `training-log.jsonl`
- `metrics.json`
- `failure-samples.jsonl`
- `model-card.md`

## Command Examples
```powershell
python tools/captcha_model_train.py --config <config> --out <run_dir>
```

## Failure Modes
- Training data leakage inflates metrics.
- Metrics omit hard negatives or failure cases.
- Model artifact cannot be reproduced from config.

## Retry Strategy
- Fix dataset governance issues before retraining.
- Re-run evaluation on unchanged holdout splits.

## Cleanup Rules
- Remove failed checkpoints not referenced by the model card.
- Preserve configs, logs, and metrics for accepted runs.

## Acceptance Checks
- Metrics are tied to fixed splits and recorded config.
- Capability claim remains local unless business evidence exists.

## Related Skills
- `captcha-model-training`
- `captcha-open-source-model-stack`
- `captcha-algorithm-benchmark`
