# CAPTCHA Model Training Governance

Version: 0.1.1

## Workflow

- Require dataset manifest, train/val/test split, config, checkpoint, and metrics.
- Run leakage audit before benchmark or promotion.
- Feed failure samples back into evals only after labels are separated from solver inputs.

## Success Criteria

- Validation/test metrics compare against a previous baseline.
- Failure samples before/after are recorded.
- Checkpoint path and model registry entry exist.
- Promotion gate confirms leakage audit PASS.

## Boundaries

This skill is not responsible for production CAPTCHA bypass or vendor production capability claims.

## Governance

Known failures and eval backlog must cite run_id, evidence, and split identity. Drift requires rerunning eval and leakage gates.
