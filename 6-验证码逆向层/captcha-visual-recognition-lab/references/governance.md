# CAPTCHA Visual Recognition Lab Governance

Version: 0.1.1

## Workflow

- Use image or screenshot evidence only.
- Run solver input redaction.
- Record per-family metrics and failures.

## Success Criteria

- Sample count and success rate are per family.
- p95 error is recorded.
- Failure cases are available for replay.
- Capability decision is scoped.

## Boundaries

This skill is not responsible for vendor production bypass or DOM/query answer extraction.

## Governance

Known failures and eval backlog must cite run_id and evidence path. Drift requires rerunning recognition gates.
