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
- Observation-only hook and runtime trace evidence when permitted by scope.

## Runtime Trace Contract

`runtime-events.json` MUST record trace events with:

| Field | Required value |
|---|---|
| `capture_id` | Stable identifier for the capture run. |
| `run_id` | Stable identifier for the browser run or structure-only fixture. |
| `script_sha256` | Hash of the script associated with the event, or `unknown` with reason. |
| `event_kind` | One of `network`, `console`, `storage`, `call_stack`, `hook_observation`, `user_action`, or `unknown`. |
| `call_stack` or `call_stack_status` | Redacted stack frames, or status such as `not_recorded`, `blocked`, or `manual_review_required`. |
| `input_output_redaction` | Redaction state for observed inputs and outputs. |
| `evidence_level` | One of `observed`, `derived`, `assumed`, `unverified`. |
| `authorization_scope` | Scope label, or `not_applicable_structure_only`. |

Hook-related entries are observation evidence only. They MAY identify where an instrumented observation occurred, but MUST NOT include instructions for concealment, falsification, protected-control circumvention, clearance reuse, or production workflow.

## Evidence Files
- `runtime-trace.har`
- `runtime-events.json`
- `storage-snapshot.redacted.json`
- `action-timeline.md`

## Command Examples
```powershell
python3 tools/js_runtime/js_page_runtime_capture.py --url <url> --out <evidence_dir>
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
- Remove unredacted input/output payloads unless the authorization scope explicitly allows retention.

## Acceptance Checks
- Trace includes request timing, initiator, status, and response shape.
- Redaction is documented before sharing evidence.
- Observation-only trace entries include `capture_id`, `run_id`, script hash, call stack status, input/output redaction, and evidence level.
- The trace report does not convert observation evidence into operational instructions or production success claims.

## Related Skills
- `reverse-js-crawler`
- `js-page-runtime-parity`
- `web-h5-loop-engineering`
