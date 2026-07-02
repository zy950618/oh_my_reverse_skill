# CAPTCHA Action Planner Governance

Version: 0.1.1

## Workflow

- Plan actions only after recognition output is available.
- Verify solver input redaction before replay.
- Store action records with target, family, sample id, observed status, and failure reason.

## Success Criteria

- Action replay metrics are per family.
- Failure cases are written back.
- Leakage and blackbox gates pass.
- Capability status stays within scope.

## Boundaries

This skill is not responsible for production bypass, unapproved vendor demo interaction, or using leaked expected answers.

## Governance

Known failures and eval backlog must cite run_id and evidence path. Drift requires replaying action records.
