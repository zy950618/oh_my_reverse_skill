# Scorecard Rubric

## Source Of Truth

The temporary single scoring standard is `99-SKILLS治理/skill-score-rubric.yaml`.
`score_skills.py`, `ci_gate.py`, `verify_delivery.py`, and the current score
report must use that same file.

Do not maintain a separate 8-dimension scoring model in this document.

## 100-Point Structure

| Category | Points | Included Subitems |
|---|---:|---|
| structure | 25 | `SKILL.md`, frontmatter, `agents/openai.yaml`, references, eval layout, governance reference, maintainability |
| operational | 25 | trigger clarity, workflow behavior, eval quality, routing boundaries, evidence write-back, real-task metrics |
| consistency | 30 | active fixtures, active snapshot count, active expiry, active recent report, replay consistency rate |
| drift | 20 | drift policy, regression coverage, version/change log, historical metrics |

The former 8 dimensions are now subitems under these four categories:

- Structure validity and progressive disclosure -> `structure`.
- Trigger accuracy, execution behavior, backtest quality, and experience capture -> `operational`.
- Fixture/replay evidence and site-memory consistency -> `consistency`.
- CI, drift, versioning, change log, and long-term metrics -> `drift`.

## Required Backtests

For each active Skill:

- 1 positive trigger eval.
- 1 negative trigger eval.
- 1 boundary/regression eval.
- local score script output.
- CI gate result for its layer.

For high-risk crawler/reverse/risk diagnostics Skills:

- stage-specific test.
- protected-response versus business-error distinction.
- site memory or failure-memory write-back.
- version/change-log update.
- explicit refusal of unauthorized bypass, stealth, fingerprint spoofing, token forgery, and clearance reuse.
