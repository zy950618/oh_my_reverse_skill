# API Replay Drift Lab

This Phase 4 lab is a local synthetic evidence package. It documents solver/parity/drift behavior without live-site credentials or production traffic.

## Files

- `manifest.json`
- `negative_cases.json`
- `validation_report.json`
- `reports/replay_or_trace_report.md`

## Coverage

- schema drift
- field missing
- field renamed
- JSON pointer mismatch
- timestamp drift
- signature drift
- token drift
- response business data drift
- replay diff report

## Validation

- `tools/validate_api_replay_drift_lab.py`
