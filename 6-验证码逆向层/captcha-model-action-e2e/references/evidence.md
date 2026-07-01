# Evidence Requirements

## Positive Evidence

- model prediction artifact exists.
- action plan maps deterministically to allowed actions.
- local or authorized replay produces expected state transition.
- negative controls fail as expected.
- failure replay is archived.

## Negative Evidence

- stale prediction does not pass.
- copied provider token does not pass.
- cross-session contamination invalidates the run.

## Drift Evidence

- repeated failed families update evals and promotion gates.
- action success metrics remain scoped to local or authorized evidence.
