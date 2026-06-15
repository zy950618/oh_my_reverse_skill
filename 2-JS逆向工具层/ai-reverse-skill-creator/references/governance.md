Version: 0.5.0

# ai-reverse-skill-creator governance

Change log:
- 0.5.0: Added hard delivery gate, structured eval expectations, graph/impact templates, anti-AI-error controls, and fingerprint/risk-control evidence discipline.

## Workflow

Use this reference whenever creating or improving a Web/H5 reverse-engineering skill.

1. Preserve the existing skill name unless the user explicitly asks for a rename.
2. Keep `SKILL.md` concise and move detailed examples to `references/`.
3. Add 8-12 evals for operational skills: positive, negative, scope, regression, no-evidence, graph-update, impact-regression, data-validation, concurrency/session, and risk/fingerprint freshness.
4. Add a metrics/failure-sample seed so recurring AI mistakes become measurable.
5. Update graph/impact examples before claiming the skill is ready.
6. Run score/CI validation or state the exact command that remains.

## Hard delivery gate

Every generated or modified operational skill must require:

- Evidence Map: file path, line number, request URL, HAR/event id, JSON Pointer, stack frame, or command output.
- Graph Delta: changed nodes and edges.
- Impact Regression: downstream skills, endpoints, fields, fixtures, evals, and required checks.
- Validation Commands: scoring, CI gate, replay/diff/schema checks when relevant.
- Fact Labels: observed, derived, assumed, unverified.
- Scope Ledger: in_scope, out_of_scope, auth_state, market/stage/session, freshness status, and unresolved blockers.

## Known failures

- Name mismatch: folder, frontmatter, openai metadata, and docs use different names.
- Stage drift: plan says one stage model but skill body uses another.
- Evals as placeholders: files exist but do not test real behavior.
- Over-generalization: one task or site sample becomes a universal claim.
- Missing impact record: skill changes evals or endpoint behavior without graph/impact updates.

## Drift policy

Treat changed trigger description, renamed skill, changed stage taxonomy, changed eval contract, new dependency, changed endpoint/field semantics, and altered delivery gate as drift.

## Site memory

When a skill affects site behavior, require updates to `站点经验库/<domain>/knowledge-graph.md` and `站点经验库/<domain>/impact-regression.md`. Skill-level governance does not replace site memory.
