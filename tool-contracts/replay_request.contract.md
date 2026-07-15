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
- One ReplayResult JSON document on stdout; diagnostics are written to stderr.
- Successful HTTP responses are written below the selected fixture layout's `actual/` directory.
- Request/response assertions and business-success classification remain downstream work; this command does not implement them.

## Evidence Files
- `request-fixture.redacted.json`
- `replay-result.json`
- `response-assertions.json`
- `failure-classification.md`

## Command Examples
```shell
python3 tools/replayer/snapshot_replay.py \
  --domain <domain> \
  --target https://adapter.example

python3 tools/replayer/snapshot_replay.py \
  --domain <domain> \
  --target https://adapter.example \
  --filter GET_search
```

## ReplayResult

The stable top-level fields are:

| Field | Meaning |
| --- | --- |
| `status` | `PASS`, `PARTIAL_FAILURE`, `FAILURE`, `NO_DATA`, or `REFUSED` |
| `exit_code` | The required CLI process exit code |
| `total` | Request fixtures in the selected snapshots layout before filtering |
| `selected` | Request fixtures selected after `--filter` |
| `replayed` | Selected requests that obtained an HTTP response and wrote an actual artifact |
| `failed` | Selected requests that failed parsing, transport, or artifact writing |
| `expired` | Selected fixtures whose parseable metadata is expired |
| `no_data` | `true` only for `NO_DATA` |
| `actual_artifacts` | Unique, sorted paths relative to the selected fixture root |
| `filtered` | Request fixtures excluded by `--filter`; equals `total-selected` |

Exit codes and invariants:

- `0` / `PASS`: `selected>0`, `failed=0`, and `replayed=selected`.
- `2` / `REFUSED`: CLI syntax/conversion is invalid, `--domain` is unsafe or escapes `SITE_ROOT`, `--target original` lacks `--allow-original`, or an adapter authority is malformed; no fixtures are processed and no actual artifacts are changed. Only the literal `original` sentinel may select captured-origin replay.
- `3` / `PARTIAL_FAILURE`: `selected=replayed+failed` with both counts greater than zero.
- `3` / `FAILURE`: `selected>0`, `replayed=0`, and `failed=selected`.
- `4` / `NO_DATA`: the selected snapshots root is missing or not a directory, it contains no request fixtures, or filtering selects none; `no_data=true` and no actual artifacts are created.

HTTP 4xx and 5xx responses count as replayed transport responses and are written to `actual/`. They are not assertions of business success; downstream consistency checks evaluate their recorded response shape.

Adapter targets use `http` or `https` with a non-empty host. A host without an explicit scheme remains compatible and is normalized to `https`. Whitespace, userinfo, malformed/out-of-range ports, unsupported schemes and empty/invalid authorities are refused before fixture access and never fall back to captured-origin replay.

`--domain` is a single safe path component. Absolute paths, separators, `.`/`..`, whitespace, DEL, and every Unicode `C*` control/format/surrogate/private/unassigned category are refused before path construction or fixture reads. Resolved domain, fixture, snapshot and actual paths must remain contained beneath `SITE_ROOT`; ordinary Unicode/IDN components remain valid when they satisfy these constraints.

Argument parsing does not accept abbreviated option names. Every parser terminal emits exactly one ReplayResult JSON: missing required arguments, invalid conversions, unknown or abbreviated options, and `--help` all return `REFUSED` with exit code `2`. Usage, error, and help detail are written only to stderr, and the process exit always equals JSON `exit_code`.

For attempted requests, actual responses are written to a temporary sibling, flushed and closed, then atomically replaced. Any directory/open/serialization/flush/replace failure invalidates the current endpoint output and removes temporary siblings so stale or truncated data is not reported as current.

The CI ReplayResult consumer uses strict single-document JSON decoding. It rejects `NaN`, `Infinity`, `-Infinity`, and duplicate keys at every object nesting level before applying schema/count/path/process-exit checks; rejected domains never run consistency, later domains still run, and all per-domain JSON documents remain retained artifacts.

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
- Replay status is recorded in ReplayResult and the process exit equals `exit_code`.
- Business assertions, when required, are recorded by the downstream consistency/assertion stage.
- Protected response is not counted as business success.

## Related Skills
- `reverse-js-crawler`
- `web-h5-loop-engineering`
- `website-314-api-delivery`
