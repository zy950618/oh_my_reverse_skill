Version: 0.5.0

# find-crypto-entry governance

Change log:
- 0.5.0: Added hard delivery gate, structured eval expectations, graph lineage, impact regression, anti-generalization, and fingerprint/risk-control evidence discipline.

## Workflow

Use this reference when the task touches a request field, header, body parameter, token, signature, endpoint, SDK call, request wrapper, or eval.

1. Collect evidence before reasoning: request URL, final observed API response, script URL, source location, call stack, JSON Pointer, or command output.
2. Locate the assignment/call site with static search, XHR/fetch breakpoint, stack frame inspection, or source-map evidence.
3. Classify the entry shape: business-code assignment, interceptor/wrapper injection, external SDK, or still unverified.
4. Write graph deltas before changing field mapping, endpoint mapping, implementation, or eval coverage.
5. Write impact-regression before claiming delivery.

## Hard delivery gate

Every final output must include:

- Evidence Map: source file/URL, line/column or offset, stack frame, request URL, and response pointer.
- Graph Delta: added/changed nodes and edges.
- Impact Regression: downstream endpoints, fields, scripts, evals, fixtures, and required checks.
- Validation Commands: replay, diff, schema alert, or reason a command could not run.
- Fact Labels: observed, derived, assumed, unverified.
- Scope Ledger: target field, auth_state, market/stage/session, capture freshness, handoff skill, and unresolved blockers.

## Known failures

- False entry: matching the parameter name in a logging wrapper instead of the assignment frame.
- Stale bundle: keeping an old scriptId after page refresh and reporting a dead source location.
- Header hardcoding: copying an observed header value instead of finding its generator.
- Over-generalization: one session or one market works, then the report claims global coverage.
- Missing graph update: entry point changed but downstream endpoint/eval nodes still point to the old function.

## Drift policy

Treat bundle hash changes, function rename, request wrapper replacement, field move, and endpoint version changes as drift. Mark prior mappings stale until replay/diff evidence proves they still work.

## Site memory

Write durable findings to `站点经验库/<domain>/knowledge-graph.md` and `站点经验库/<domain>/impact-regression.md`. Do not hide important evidence only in the final chat response.
