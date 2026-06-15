Version: 0.5.0

# env-patch governance

Change log:
- 0.5.0: Added hard delivery gate, structured eval expectations, minimal-stub policy, graph lineage, impact regression, and fingerprint/risk-control evidence discipline.

## Workflow

Use this reference when moving browser JS to Node, writing stubs, patching runtime globals, extracting webpack modules, or wrapping a signing function.

1. Start from a located entry: module id, function name, script URL/hash, and request field.
2. Copy source JS as read-only and put all stubs in `run.js` or `sign.js`.
3. Add the smallest stub that resolves the next diagnostic error. Do not add broad fake browser profiles.
4. Compare browser and Node outputs before request replay.
5. Write graph deltas and impact-regression records before delivery.

## Hard delivery gate

Every final output must include:

- Evidence Map: entry source, runtime dependency, observed browser value, stub source, Node output, and API response pointer if replayed.
- Graph Delta: environment nodes, JS function nodes, request fields, protection nodes, and eval edges.
- Impact Regression: affected stubs, storage keys, cache/session assumptions, endpoints, fields, fixtures, and evals.
- Validation Commands: `node env/run.js`, format comparison, request replay, snapshot diff, schema alert, or a clear reason a check could not run.
- Fact Labels: observed, derived, assumed, unverified.
- Scope Ledger: runtime globals touched, source for every stub value, browser profile, capture freshness, and unresolved blockers.

## Known failures

- Header hardcoding: pasting one observed header into `sign.js` instead of reproducing generation.
- Fingerprint overreach: adding broad fake navigator/screen/webgl values without evidence.
- False Node success: signature length matches but value differs from browser output.
- Storage drift: localStorage key captured from one session is reused in another.
- Missing graph update: an added stub changes runtime dependencies but knowledge graph still shows no environment edge.

## Drift policy

Treat changed bundle hash, new global lookup, storage key movement, signature format mismatch, browser-vs-Node output mismatch, and request schema change as drift.

## Site memory

Write environment findings to `站点经验库/<domain>/knowledge-graph.md` and `站点经验库/<domain>/impact-regression.md`, including observed stubs, unknown values, and required reruns.
