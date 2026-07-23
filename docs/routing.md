# Routing

Routing source of truth is `TRIGGERS.md` plus `00-SKILLS索引.md`.

Allowed active roles:

- `external_entry`: user-facing entry skill.
- `conditional_escalation`: evidence-triggered specialist or post-verification handoff.
- `internal_tool`: atomic tool called by an entry skill.
- `auxiliary_policy`: engineering discipline only.

Tools must not steal business entry routing. WAF evidence, fingerprint diagnostics, runtime parity, block reason attribution, loop execution, and scoring each keep separate ownership.
