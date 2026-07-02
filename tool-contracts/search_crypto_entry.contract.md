## Purpose
Locate likely sign, token, encryption, or request-normalization entry points in collected JavaScript.

## Allowed Scope
- Static search, call-chain mapping, and runtime breakpoint planning.
- Do not produce credential theft, payment abuse, or access-control bypass logic.

## Inputs
- Script inventory and local script snapshots.
- Known request fields, headers, or parameters to trace.
- Target function or endpoint names when available.

## Outputs
- Candidate entry list with file, offset, symbol, and confidence.
- Call-chain notes from request builder to crypto primitive.

## Evidence Files
- `crypto-entry-candidates.json`
- `call-chain.md`
- `search-queries.md`

## Command Examples
```powershell
python tools/js_signature_regression.py --fixtures <fixtures_dir> --out <evidence_dir>
```

## Failure Modes
- Minified names hide intent.
- Crypto values are server-issued instead of client-generated.
- Search matches decoy or unused code.

## Retry Strategy
- Add request-field anchors from a fresh browser trace.
- Compare candidates against runtime call stacks before promoting.

## Cleanup Rules
- Keep only source excerpts required for evidence.
- Remove temporary expanded bundles if hashes are recorded.

## Acceptance Checks
- At least one candidate is linked to an observed request field.
- Confidence level is labeled as observed, derived, or unverified.

## Related Skills
- `find-crypto-entry`
- `reverse-js-crawler`
- `js-page-runtime-parity`
