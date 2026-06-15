# find-crypto-entry failure sample and metric seed

任务总数: 3
真实任务下限: 3

This file is a seed corpus for regression governance. It records concrete failure shapes the skill must catch; it is not a claim of production-wide success rate.

| date | sample | observed failure | required regression |
|---|---|---|---|
| 2026-06-12 | header-sign-wrapper | Agent matched `x-sign` in a logger and missed the interceptor assignment frame. | Require stack-frame evidence and graph edge `field -> generator`. |
| 2026-06-12 | stale-scriptid | Agent refreshed the page after setting a breakpoint and reported a stale scriptId. | Require script URL/hash and refreshed source location validation. |
| 2026-06-12 | one-session-generalization | One session produced a stable header and the report claimed all sessions work. | Require boundary label and session-isolation evidence before any concurrency claim. |

Success rate: 0%

The initial success rate is intentionally 0% until these samples are executed by a real eval harness.
