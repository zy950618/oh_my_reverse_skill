# Phase 3.9 Model Training Evidence Boundary

Version: 0.1.1

Source run_id: `run-20260630-113000-phase3-9-vendor-shield-range`.

Evidence:

- `public-range-evidence/shumei-compatible-lab/run-20260630-113000-phase3-9-vendor-shield-range.json`
- `public-range-evidence/aliyun-compatible-lab/run-20260630-113000-phase3-9-vendor-shield-range.json`

Known failures:

- Phase 3.9 compatible labs are solver/action candidates, not production vendor models.
- No production vendor training data was used.
- Any future checkpoint must prove it did not read labels, metadata answers, DOM answers, or query expected fields.

Eval backlog:

- Add checkpoint comparison for text, slider, or click detector before claiming model improvement.
- Keep compatible-lab family results separate from official vendor demos.
