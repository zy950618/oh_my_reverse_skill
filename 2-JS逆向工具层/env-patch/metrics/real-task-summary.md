# env-patch failure sample and metric seed

任务总数: 3
真实任务下限: 3

This file is a seed corpus for regression governance. It records concrete failure shapes the skill must catch; it is not a claim of production-wide success rate.

| date | sample | observed failure | required regression |
|---|---|---|---|
| 2026-06-12 | hardcoded-header | Agent pasted one browser `x-sign` header into Node output. | Require generator call evidence and browser-vs-Node comparison. |
| 2026-06-12 | broad-fingerprint-stub | Agent added large fake navigator/screen profile without observed reads. | Require minimal-stub policy, capture source, and freshness evidence. |
| 2026-06-12 | false-format-success | Signature length matched but value differed from browser output. | Require value comparison on representative inputs before replay claim. |

Success rate: 0%

The initial success rate is intentionally 0% until these samples are executed by a real eval harness.
