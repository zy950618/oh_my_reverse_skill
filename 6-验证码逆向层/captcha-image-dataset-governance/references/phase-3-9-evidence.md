# Phase 3.9 Dataset Evidence Boundary

Version: 0.1.1

Source run_id: `run-20260630-113000-phase3-9-vendor-shield-range`.

Evidence:

- `public-range-evidence/shumei-compatible-lab/run-20260630-113000-phase3-9-vendor-shield-range.json`
- `public-range-evidence/aliyun-compatible-lab/run-20260630-113000-phase3-9-vendor-shield-range.json`

Known failures:

- Compatible-lab server answers are not solver inputs.
- Official demo observations are not training labels.
- Any DOM/query expected leak invalidates solver and benchmark runs.

Eval backlog:

- Add dataset manifest check for future checkpoints.
- Add hard/adversarial split verification before stable promotion.
