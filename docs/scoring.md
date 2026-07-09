# Scoring

Current scoring contract:

- Active skill inventory is declared in `skills-manifest.json` and validated by `python3 tools/skills_manifest.py validate`.
- Strict repository score must be at least 93.
- Every active skill must score at least 93.
- Release gate is `python3 tools/governance/ci_gate.py .ci-out --manifest skills-manifest.json --release`.
- Thresholds live in `99-SKILLS治理/skill-score-rubric.yaml`.

Release scoring docs must stay current-state only. Process score runs and earlier baselines do not belong in source-of-truth docs.
