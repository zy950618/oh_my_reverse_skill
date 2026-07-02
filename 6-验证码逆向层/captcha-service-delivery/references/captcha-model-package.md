# CAPTCHA model package

Version: 0.1.0

A model package is the handoff artifact for local/authorized CAPTCHA model
delivery. It contains file inventory, inference input/output contract, metrics
references, and explicit safety boundaries.

## Package manifest

```json
{
  "manifest_type": "captcha_model_package",
  "schema_version": "0.1.0",
  "model_package_id": "captcha-model-lab-sample-package",
  "package_version": "0.1.0",
  "dataset_ref": "manifests/dataset_manifest.json",
  "training_report_ref": "manifests/training_report.json",
  "pass_rate_report_ref": "manifests/pass_rate_report.json",
  "files": [
    {"role": "model", "path": "../model/sample-model.json"},
    {"role": "inference_contract", "path": "../model/inference-contract.json"}
  ],
  "inference_contract": {
    "input": "redacted captcha image plus coordinate metadata",
    "output": "captcha_action_schema@0.1.0",
    "error_modes": ["low_confidence", "unsupported_challenge", "invalid_geometry"]
  },
  "allowed_use": ["local_lab", "owned_authorized_target"],
  "prohibited_claims": [
    "third_party_captcha_bypass",
    "managed_challenge_auto_pass",
    "provider_success_without_business_repeat_verified"
  ]
}
```

## Rules

- The package manifest references the dataset, training report, and pass-rate
  report that produced the model.
- Every file path is relative to the manifest and must exist.
- The inference contract outputs the action schema, not raw provider tokens.
- Prohibited claims are part of the package and travel with the artifact.
