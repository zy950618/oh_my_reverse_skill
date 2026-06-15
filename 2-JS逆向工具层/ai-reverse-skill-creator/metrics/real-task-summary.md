# ai-reverse-skill-creator failure sample and metric seed

任务总数: 3
真实任务下限: 3

This file is a seed corpus for regression governance. It records concrete failure shapes the skill must catch; it is not a claim of production-wide success rate.

| date | sample | observed failure | required regression |
|---|---|---|---|
| 2026-06-12 | name-mismatch | Generated folder name, frontmatter name, and display metadata diverged. | Require name consistency checks. |
| 2026-06-12 | placeholder-evals | Generated three eval files with generic TODO-style criteria. | Require 8-12 structured evals with real failure modes. |
| 2026-06-12 | no-impact-gate | Modified endpoint-field behavior but omitted graph/impact updates. | Require delivery gate and impact-regression examples. |

Success rate: 0%

The initial success rate is intentionally 0% until these samples are executed by a real eval harness.
