## Purpose
Collect page scripts and script metadata for an authorized Web/H5 target so later analysis can map runtime sources to requests.

## Allowed Scope
- Capture script URLs, inline script hashes, initiators, and local snapshots.
- Do not execute protected actions, bypass access controls, or store secrets.

## Inputs
- Target URL and authorization scope.
- Browser profile or clean-state capture plan.
- Output evidence directory.

## Outputs
- Script inventory with source identity, hash, freshness, redaction, storage, and authorization scope.
- Local script snapshots when allowed by scope.
- External-absorption fact linkage when a script pattern is used to harden an internal base asset.

## Scripts Manifest Contract

`scripts-inventory.json` MUST be a manifest object with one `scripts` array. Each script entry MUST include:

| Field | Required value |
|---|---|
| `url` or `inline_id` | Exactly one source identity. Use `url` for external scripts and a stable capture-local `inline_id` for inline scripts. |
| `sha256` | SHA-256 of the retained script bytes after allowed redaction, encoded as lowercase hex. |
| `captured_at` | Capture timestamp in ISO 8601 format. |
| `source_freshness` | One of `fresh`, `stale`, `unknown`. |
| `redaction_status` | One of `clean`, `redacted`, `blocked`, `manual_review_required`. |
| `raw_secret_persisted` | Boolean. MUST be `false` for any script to enter long-term evidence. |
| `storage_policy` | Retention rule for the script body, for example `hash_only`, `redacted_snapshot`, `blocked_no_snapshot`, or `ephemeral_manual_review`. |
| `authorization_scope` | Scope label proving the capture was authorized, or `not_applicable_structure_only` for structure-only fixtures. |
| `script_kind` | Script class, for example `external`, `inline`, `module`, `worker`, `dynamic`, or `unknown`. |
| `size_bytes` | Retained byte length after allowed redaction. |
| `initiator` or `initiator_status` | Either observed initiator metadata, or a status such as `unknown`, `blocked`, or `not_recorded`. |
| `source_fact_pack_id` | Required when the entry is used for external absorption; links to the local fact pack or loop ledger that recorded the source at page level. |
| `evidence_level` | One of `observed`, `derived`, `assumed`, `unverified`; `assumed` and `unverified` cannot support positive capability claims. |
| `raw_external_imported` | Boolean. MUST be `false`; external raw files, code, templates, prompts, tests, and examples are not imported through this contract. |

`redaction_status` semantics:

- `clean`: no secret-like material was detected and no redaction was applied.
- `redacted`: secret-like material was removed before persistence; `sha256` covers the retained redacted bytes.
- `blocked`: persistence was refused because the content cannot be safely retained.
- `manual_review_required`: automated classification was insufficient; do not promote to long-term evidence until review resolves to `clean` or `redacted`.

`source_freshness` semantics:

- `fresh`: captured in the named run from the current authorized source.
- `stale`: copied from an older capture or cache.
- `unknown`: freshness cannot be proven.

`stale` and `unknown` entries MAY document structure or negative context, but MUST NOT be used as positive proof of a reusable capability.

Long-term evidence rule: `raw_secret_persisted` MUST be `false`. If a capture would persist raw cookies, tokens, credentials, browser profile state, localStorage, sessionStorage, or other raw secrets, the entry MUST be `blocked` or `manual_review_required` and MUST NOT be retained as long-term positive evidence.

## External Absorption Boundary

When this contract absorbs a pattern from an external-source fact pack, the entry MUST:

- Name the internal base asset being hardened, such as this contract, an eval seed, a governance reference, or a loop ledger.
- Link the local `source_fact_pack_id` and never depend on raw external repository contents.
- Record script manifest identity, `sha256`, `captured_at`, `source_freshness`, `redaction_status`, `raw_secret_persisted: false`, `evidence_level`, and `raw_external_imported: false`.
- Treat `stale`, `unknown`, `assumed`, or `unverified` as structure or negative context only.
- Refuse promotion when source freshness, source fact pack linkage, raw-secret status, or evidence level is missing.

## Evidence Files
- `scripts-inventory.json`
- `scripts/`
- `capture-notes.md`

## Command Examples
```powershell
python3 tools/js_runtime/js_page_runtime_capture.py --url <url> --out <evidence_dir>
```

## Failure Modes
- Page blocks script loading.
- Scripts are generated dynamically after user interaction.
- Capture stores stale or partial script content.

## Retry Strategy
- Retry from a clean browser state and fresh evidence directory.
- Record block state separately before retrying.

## Cleanup Rules
- Remove temporary browser exports after preserving inventory and hashes.
- Do not keep cookies, tokens, or credentials in script snapshots.

## Acceptance Checks
- Inventory lists every observed script source or inline hash.
- Each saved script has a matching hash in the inventory.
- Every manifest entry includes the required fields in the Scripts Manifest Contract.
- No long-term evidence entry has `raw_secret_persisted: true`.
- `stale` or `unknown` freshness is not counted as positive capability proof.
- External-absorption entries include source fact pack linkage, internal base asset, evidence level, and `raw_external_imported: false`.

## Related Skills
- `reverse-js-crawler`
- `find-crypto-entry`
- `web-h5-loop-engineering`
