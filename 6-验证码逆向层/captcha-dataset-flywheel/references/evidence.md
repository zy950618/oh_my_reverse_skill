# Evidence Requirements

## Positive Evidence

- Manifest exists and references every sample.
- Split file proves no sample overlaps across train/validation/test.
- Leakage audit passes.
- Failure samples include replay feedback or explicit reason why replay is not applicable.

## Negative Evidence

- Remote solver source is rejected.
- Copied token or clearance cookie source is rejected.
- Label read during inference invalidates the run.

## Drift Evidence

- Repeated failure categories create regression evals.
- New labels or splits update manifest version and change log.
