# CAPTCHA Model Lab Sample Model Card

## Scope

This package is local-lab evidence only. It uses three owned synthetic slider samples and does not claim third-party CAPTCHA bypass, managed challenge success, or production solver capability.

## Model

- Family: baseline-template-matcher
- Package: captcha-model-lab-sample-package
- Dataset: captcha-model-lab-sample
- Inference entrypoint: `inference/sample_infer.py`
- Evaluation entrypoint: `eval/evaluate_pass_rate.py`

## Metrics

The local fixture evaluation currently reports 3 attempts, 3 passes, and pass_rate 1.0 with tolerance 3 CSS pixels. This is a fixture pass rate, not a third-party pass rate.

## Boundary

No provider token, remote solver API, user data, or live third-party protected target is used by this sample package.
