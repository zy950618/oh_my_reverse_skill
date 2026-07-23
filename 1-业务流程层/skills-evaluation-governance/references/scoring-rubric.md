# Scoring Rubric

## Canonical Rubric

Use `99-SKILLS治理/skill-score-rubric.yaml` as the scoring source of truth.

The current executable score is:

- `structure`: 25 points.
- `operational`: 25 points.
- `consistency`: 30 points.
- `drift`: 20 points.

## Score Bands

- 90-100: high available, with strong structure, operational behavior, fresh consistency evidence, and drift controls.
- 80-89: available, but consistency or long-term evidence may still need hardening.
- 70-79: structure-ready candidate for active layers if it meets the configured threshold.
- 50-69: note-like or partially governed.
- below 50: raw material or advisory-only until references/evals/gates are added.

## Required Evidence

- required files exist.
- frontmatter has `name` and `description`.
- description names both task and trigger contexts.
- body is concise and procedural.
- references and evals are present for active Skills.
- active fixtures are fresh when consistency evidence is used.
- validation result is reported honestly.

Do not report an official Skill Bench score unless an official Skill Bench run actually occurred.
