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
- Script inventory with URL, type, hash, size, and capture time.
- Local script snapshots when allowed by scope.

## Evidence Files
- `scripts-inventory.json`
- `scripts/`
- `capture-notes.md`

## Command Examples
```powershell
python tools/js_page_runtime_capture.py --url <url> --out <evidence_dir>
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

## Related Skills
- `reverse-js-crawler`
- `find-crypto-entry`
- `web-h5-loop-engineering`
