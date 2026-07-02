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

## Evidence Files
- `browser-fixture.json`
- `node-output.json`
- `runtime-parity-report.json`
- `environment-gaps.md`

## Command Examples
```powershell
python tools/js_page_runtime_parity_runner.py --fixture <fixture> --out <evidence_dir>
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

## Related Skills
- `js-page-runtime-parity`
- `env-patch`
- `find-crypto-entry`
