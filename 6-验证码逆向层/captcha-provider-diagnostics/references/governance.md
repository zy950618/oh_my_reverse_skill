# CAPTCHA Provider Diagnostics Governance

Version: 0.1.1

## Workflow

- Classify target with `configs/vendor_challenge_matrix.yaml`.
- For official demos, collect readonly screenshot, network, and state observer evidence only.
- For compatible labs, record local action replay as `compatible_lab=true`, `official_vendor=false`, and `not_generalizable_to_vendor_production=true`.

## Success Criteria

- Provider marker evidence exists.
- `execution_status` and `capability_status` are present.
- Official demo evidence stays `memory_only`.
- Compatible-lab candidates pass leakage and blackbox gates.

## Boundaries

This skill is not responsible for solving production vendor CAPTCHA, bypassing WAF, fingerprint spoofing, or using leaked answers.

## Governance

Known failures and eval backlog must cite run_id and evidence paths. Drift requires rerunning diagnostics and capability gates.
