# CAPTCHA training pipeline

Version: 0.1.0

The training pipeline describes reproducible local model work from dataset to
metrics and package. It is intentionally independent from provider automation.

## Pipeline stages

1. `dataset_audit`: validate manifest, splits, paths, labels, and provenance.
2. `label_audit`: check coordinate spaces, duplicate labels, impossible
   actions, and manual-review status.
3. `train`: run deterministic training with fixed seed, code version, dataset
   id, and model family.
4. `evaluate`: compute per-challenge and per-provider metrics on validation and
   test splits.
5. `failure_review`: save false positives, false negatives, and low-confidence
   samples without secrets.
6. `package`: write a model package manifest with inference contract and
   prohibited claims.

## Training report fields

```json
{
  "manifest_type": "captcha_training_report",
  "schema_version": "0.1.0",
  "run_id": "train-20260701-sample",
  "dataset_id": "captcha-model-lab-sample",
  "model_family": "baseline-template-matcher",
  "pipeline": ["dataset_audit", "label_audit", "train", "evaluate", "package"],
  "reproducibility": {
    "seed": 1337,
    "code_version": "local-sample",
    "python": "standard-library-validator-compatible"
  },
  "metrics": {
    "validation_accuracy": 1.0,
    "test_accuracy": 1.0,
    "mean_action_error_css_px": 0.0
  },
  "capability_boundary": {
    "skills_participation": "memory_only",
    "third_party_positive_claim": false,
    "requires_business_api_repeat_verified": true
  }
}
```

## Rules

- Report metrics separately for validation and test splits.
- Preserve a seed and code version for repeatability.
- Do not promote local model accuracy to third-party provider success.
- A model is packageable only when dataset, training report, pass-rate report,
  and package manifest all validate.
