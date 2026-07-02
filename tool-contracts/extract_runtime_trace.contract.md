## Purpose
Extract browser runtime traces that connect user actions, network requests, scripts, storage, and generated parameters.

## Allowed Scope
- Passive capture of authorized traffic and runtime events.
- Do not automate real purchases, credential actions, or destructive account changes.

## Inputs
- Target URL and permitted action path.
- Clean-state profile description.
- Evidence output directory.

## Outputs
- Network trace, console trace, storage snapshot, and action timeline.
- Runtime notes identifying request builders and dynamic state.

## Evidence Files
- `runtime-trace.har`
- `runtime-events.json`
- `storage-snapshot.redacted.json`
- `action-timeline.md`

## Command Examples
```powershell
python tools/js_page_runtime_capture.py --url <url> --out <evidence_dir>
```

## Failure Modes
- Trace includes stale session state.
- Required interaction is outside authorized scope.
- Dynamic challenge state changes during capture.

## Retry Strategy
- Re-run with a new profile and separate evidence path.
- Record challenge or block state before continuing.

## Cleanup Rules
- Redact cookies, bearer tokens, and personal data.
- Keep raw trace only when allowed by the task scope.

## Acceptance Checks
- Trace includes request timing, initiator, status, and response shape.
- Redaction is documented before sharing evidence.

## Related Skills
- `reverse-js-crawler`
- `js-page-runtime-parity`
- `web-h5-loop-engineering`
