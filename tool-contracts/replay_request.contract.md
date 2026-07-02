## Purpose
Replay an observed authorized request to confirm required headers, body, state, and response mapping.

## Allowed Scope
- Replay captured requests within the approved target, rate, and data scope.
- Do not run real payment, destructive, or unauthorized account actions.

## Inputs
- Redacted request fixture.
- Session requirements and freshness notes.
- Expected response schema or assertions.

## Outputs
- Replay result with status, timing, request diff, and response assertions.
- Failure classification for route, state, schema, or protection issues.

## Evidence Files
- `request-fixture.redacted.json`
- `replay-result.json`
- `response-assertions.json`
- `failure-classification.md`

## Command Examples
```powershell
python tools/replayer/snapshot_replay.py --fixture <fixture> --out <evidence_dir>
```

## Failure Modes
- Fixture depends on expired token or cookie.
- Server returns protected or business-error response.
- Response schema drifts from fixture expectations.

## Retry Strategy
- Refresh fixture from a clean capture before changing request logic.
- Run schema diff after any response-shape change.

## Cleanup Rules
- Redact credentials and session secrets.
- Archive failed evidence separately from successful replay evidence.

## Acceptance Checks
- Replay status and business assertion are both recorded.
- Protected response is not counted as business success.

## Related Skills
- `reverse-js-crawler`
- `web-h5-loop-engineering`
- `website-314-api-delivery`
