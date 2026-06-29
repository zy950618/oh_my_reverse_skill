# Loop Roles

Use at least three roles. They may be separate agents, subagents, threads, or explicit passes in one agent when tool support is limited. The handoff artifacts must still be separate.

## Required Roles

| role | owns | must output | cannot approve |
|---|---|---|---|
| Executor | reconnaissance, capture, JS entry, reproduction, implementation | action log, request/response evidence, code or config diff | its own success |
| Verifier | replay, diff, schema, clean-state retest, concurrency ladder | validation ledger, pass/fail, failure class, remaining gap | unsupported scope expansion |
| Governor | fact level, anti-generalization, memory, impact, cleanup, refusal/human-review | scope ledger, evidence level, graph/impact updates, stop decision | bypass or unverified success |

## Optional Roles

| role | when to use | output |
|---|---|---|
| Human Reviewer | payment, login, PII, CAPTCHA/WAF, production impact, evidence conflict | human review ledger and allowed next action |
| Memory Curator | repeated same-domain lessons | known-failures, test-log-lessons, eval backlog |
| Performance Verifier | batch/concurrency claims | 1/2/5/10 worker ladder and stop condition report |

## Handoff Contract

Each role receives only the previous role's artifacts, not its confidence. Minimum handoff:

```yaml
loop_id:
iteration:
role:
input_artifacts:
action:
evidence:
verification:
decision: pass | fail | blocked | human_review
next_owner:
```

The Verifier must be able to fail the Executor. The Governor must be able to stop the loop.
