# Evidence Requirements

## Positive Evidence

- dataset provenance is recorded.
- challenge family maps to model output type.
- benchmark plan and threshold are explicit.
- leakage status is pass or blocked.
- downstream action validation route is explicit.

## Negative Evidence

- unauthorized target request is blocked.
- remote solver request is refused.
- missing leakage audit prevents promotion.

## Drift Evidence

- model registry changes include version and change log.
- benchmark failures create regression evals.
