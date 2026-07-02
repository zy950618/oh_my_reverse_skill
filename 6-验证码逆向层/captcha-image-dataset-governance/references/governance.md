# CAPTCHA Image Dataset Governance

Version: 0.1.1

## Workflow

- Store manifests and split manifests.
- Keep labels away from solver input.
- Redact screenshots and action records before benchmark.

## Success Criteria

- Train/val/test identities are separated.
- Failure samples are retained.
- Leakage audit passes.
- Dataset version is linked to run_id.

## Boundaries

This skill is not responsible for production bypass or answer extraction from official demos.

## Governance

Known failures and eval backlog must cite run_id and evidence path. Drift requires split and leakage revalidation.
