# ast-deobfuscate failure sample and metric seed

任务总数: 3
真实任务下限: 3

This file is a seed corpus for regression governance. It records concrete failure shapes the skill must catch; it is not a claim of production-wide success rate.

| date | sample | observed failure | required regression |
|---|---|---|---|
| 2026-06-12 | pretty-print-false-positive | Agent formatted minified code and called it deobfuscated. | Require feature classification and before/after transform evidence. |
| 2026-06-12 | string-offset-drift | Decoder offset changed but old index math was reused. | Require sampled string recovery and parser validation. |
| 2026-06-12 | dead-branch-side-effect | Transform deleted an apparently dead branch with side effects. | Require side-effect check and preserve uncertain code. |

Success rate: 0%

The initial success rate is intentionally 0% until these samples are executed by a real eval harness.
