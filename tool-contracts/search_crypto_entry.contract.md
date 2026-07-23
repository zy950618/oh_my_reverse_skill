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
- Input/output evidence map for each promoted candidate.

## Crypto Entry Absorption Contract

Any candidate promoted from external-absorption or prior-loop evidence MUST include:

| Field | Required value |
|---|---|
| `observed_request_field_anchor` | Request field, header, or body JSON Pointer observed in an authorized trace. |
| `script_sha256` | Hash from the linked script manifest. |
| `call_chain` | Request builder to candidate function path, with unknown frames labeled. |
| `input_evidence` | Redacted input shape, fixture id, or reason unavailable. |
| `output_evidence` | Redacted output shape, fixture id, or reason unavailable. |
| `evidence_level` | One of `observed`, `derived`, `assumed`, `unverified`. |
| `source_fact_pack_id` | Required when the candidate came from an external-source absorption record. |
| `raw_external_snippet_copied` | Boolean. MUST be `false`. |

The contract can record sign/token/encryption field structure, candidate location, and evidence gaps. It MUST NOT claim production sign/token success, live request acceptance, or copied external snippet equivalence from static search alone.

## Evidence Files
- `crypto-entry-candidates.json`
- `call-chain.md`
- `search-queries.md`

## Command Examples
```powershell
python3 tools/js_runtime/js_signature_regression.py --fixtures <fixtures_dir> --out <evidence_dir>
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
- Promoted candidates include observed request field anchor, call chain, input/output evidence, script hash, and no copied external snippets.
- Production success claims are absent unless a separate authorized acceptance artifact proves them; structure-only loops must keep that status false.

## Related Skills
- `find-crypto-entry`
- `reverse-js-crawler`
- `js-page-runtime-parity`
