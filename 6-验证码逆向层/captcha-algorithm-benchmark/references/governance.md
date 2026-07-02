# CAPTCHA Algorithm Benchmark Governance

Version: 0.1.1

## Workflow

- Separate family and difficulty buckets.
- Reject benchmarks with train/test mixing or answer leakage.
- Record failure cases and capability decision.

## Success Criteria

- Metrics include sample count, success count, success rate, and p95.
- Leakage audit and blackbox solver gate pass.
- Results are scoped to the target contract.

## Boundaries

This skill is not responsible for production vendor capability claims from compatible labs.

## Governance

Known failures and eval backlog must cite run_id and evidence path. Drift requires rerunning per-family metrics.
