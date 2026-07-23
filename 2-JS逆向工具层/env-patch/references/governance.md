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
- Runtime Parity Boundary: any parity claim is limited to the named fixture, input, and `run_id`; it does not prove business API acceptance, risk-token validity, WAF/challenge success, clearance-cookie reuse, or production readiness.
- Script Evidence Manifest: linked script evidence must record `sha256`, `captured_at`, `source_freshness`, `redaction_status`, `raw_secret_persisted`, storage policy, authorization scope, script kind, size, and initiator metadata/status.
- Foundation/Base Attachment: every env patch derived from an absorbed external category must name the internal base asset, evidence level, validation command or reason not run, failure split, and cleanup decision.

## Script evidence retention

- `raw_secret_persisted` must be `false` before evidence can be retained long term.
- Entries with raw cookies, tokens, credentials, browser profile state, localStorage, sessionStorage, or other raw secrets must be blocked or sent to manual review.
- `source_freshness` must be one of `fresh`, `stale`, or `unknown`.
- `redaction_status` must be one of `clean`, `redacted`, `blocked`, or `manual_review_required`.
- `stale` and `unknown` sources can document structure, drift, or negative context, but cannot be used as positive capability proof.

## Foundation/base attachment for absorbed categories

Before adding or changing an env patch from an absorbed category, record:

- `base_asset`: existing skill, tool contract, eval seed, governance reference, or loop ledger being hardened.
- `source_fact_pack_id`: local fact pack or loop ledger id; raw external repository files are not used.
- `evidence_level`: `observed`, `derived`, `assumed`, or `unverified`.
- `validation`: focused command run, or exact reason validation could not run.
- `failure_split`: environment gap, fixture freshness gap, script drift, redaction gap, scope gap, or unverified source gap.
- `cleanup`: temporary files removed, evidence retained, and secrets excluded from long-term storage.

If any field is missing, keep the patch as negative context or manual-review material only.

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
