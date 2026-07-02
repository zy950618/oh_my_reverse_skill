## Purpose
Check whether fixtures, HAR files, tokens, scripts, and replay evidence are fresh enough for current claims.

## Allowed Scope
- Timestamp, hash, TTL, schema, and replay freshness checks.
- Do not rewrite stale evidence into current observed facts.

## Inputs
- Evidence directory or fixture manifest.
- Freshness policy and TTL thresholds.
- Optional current replay output.

## Outputs
- Freshness report with recent, review-pending, expired, and unknown fixtures.
- Required recapture or replay actions.

## Evidence Files
- `fixture-freshness-report.json`
- `expired-fixtures.md`
- `freshness-policy.md`

## Command Examples
```powershell
python tools/fixture_freshness_report.py --evidence <evidence_dir> --out <report>
```

## Failure Modes
- Fixture lacks capture time or source hash.
- Token freshness is assumed from old success.
- Current script hash differs from fixture metadata.

## Retry Strategy
- Re-capture missing metadata before rerunning the report.
- Mark unknown freshness as review-pending, not accepted.

## Cleanup Rules
- Move expired fixtures out of positive evidence paths.
- Keep stale fixtures only as historical or failure evidence.

## Acceptance Checks
- Every fixture has a freshness state and reason.
- Expired or unknown evidence is excluded from current success claims.

## Related Skills
- `web-h5-loop-engineering`
- `skills-evaluation-governance`
- `reverse-js-crawler`
