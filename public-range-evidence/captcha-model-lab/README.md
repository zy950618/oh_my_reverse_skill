# CAPTCHA model lab evidence

This directory contains sanitized local sample evidence for the
`captcha-service-delivery` model-delivery references and validators.

Scope:
- OBSERVED: files in this directory are synthetic local lab samples.
- VERIFIED: validators can check structure, paths, split counts, and metric
  arithmetic.
- NOT VERIFIED: these files do not prove third-party CAPTCHA, WAF, or managed
  challenge success.

Run:

```bash
python tools/validate_captcha_action_schema.py public-range-evidence/captcha-model-lab/manifests/action_manifest.json
python tools/validate_captcha_dataset.py public-range-evidence/captcha-model-lab/manifests/dataset_manifest.json
python tools/validate_captcha_training_report.py public-range-evidence/captcha-model-lab/manifests/training_report.json
python tools/validate_captcha_pass_rate.py public-range-evidence/captcha-model-lab/manifests/pass_rate_report.json
python tools/validate_captcha_model_package.py public-range-evidence/captcha-model-lab/manifests/model_package_manifest.json
```
