## Purpose
Compare browser-generated values with Node.js execution to verify runtime parity for extracted JavaScript logic.

## Allowed Scope
- Local parity checks for authorized signatures, encoders, and deterministic helpers.
- Do not spoof protected browser fingerprints or forge risk tokens.

## Inputs
- Browser runtime fixture.
- Node harness or environment contract.
- Expected fields and comparison rules.

## Outputs
- Parity report with matched, mismatched, and unsupported fields.
- Environment gap list.
- Named-fixture boundary for any parity statement.

## Parity Boundary Contract

`runtime-parity-report.json` MUST include:

| Field | Required value |
|---|---|
| `fixture_id` | Named browser fixture used for the comparison. |
| `browser_run_id` | Browser run that produced the fixture, or `not_applicable_structure_only`. |
| `node_run_id` | Node run that produced comparison output. |
| `script_sha256` | Script hash from the linked manifest, or `unknown` with reason. |
| `source_freshness` | One of `fresh`, `stale`, `unknown`, or `structure_only_internal_record`. |
| `comparison_rules` | Deterministic fields, dynamic fields, tolerance, and excluded fields. |
| `evidence_level` | One of `observed`, `derived`, `assumed`, `unverified`. |
| `production_claim` | Boolean. MUST be `false` for parity-only and structure-only runs. |

Browser-vs-Node parity is limited to the named fixture, inputs, script hash, and run ids. It does not prove live service acceptance, risk-token validity, challenge handling, concurrency, or production readiness.

## Evidence Files
- `browser-fixture.json`
- `node-output.json`
- `runtime-parity-report.json`
- `environment-gaps.md`

## Command Examples
```powershell
python3 tools/js_runtime/js_page_runtime_parity_runner.py --fixture <fixture> --out <evidence_dir>
```

## Failure Modes
- Browser-only APIs are missing in Node.
- Non-deterministic fields lack normalization rules.
- Fixture was captured with stale state.

## Retry Strategy
- Rebuild the environment contract from observed browser APIs.
- Re-capture fresh fixtures before changing comparison tolerances.

## Cleanup Rules
- Remove temporary Node shims not used by the final harness.
- Do not store live session values in fixtures.

## Acceptance Checks
- Report separates deterministic mismatches from expected dynamic fields.
- Unsupported fields have explicit evidence and next action.
- Every parity claim names fixture id, browser run id, Node run id, source freshness, evidence level, and `production_claim: false`.
- Freshness gaps are reported as drift or negative context, not as positive capability proof.

## Related Skills
- `js-page-runtime-parity`
- `env-patch`
- `find-crypto-entry`
