## Purpose
Inventory observable browser fingerprint surfaces and risk-state signals for diagnostics.

## Allowed Scope
- Observation, hashing, consistency checks, and drift reporting.
- Do not spoof, bypass, or generate stealth fingerprint profiles.

## Inputs
- Authorized target or local lab URL.
- Browser profile description.
- Capture and comparison plan.

## Outputs
- Fingerprint surface inventory, hash, and consistency report.
- Risk-state notes linked to observed responses.

## Evidence Files
- `fingerprint-surface.json`
- `surface-hash.json`
- `profile-consistency-report.json`
- `risk-state-notes.md`

## Command Examples
```powershell
python tools/fingerprint_surface_capture.py --url <url> --out <evidence_dir>
```

## Failure Modes
- Capture changes profile state.
- Dynamic surfaces cause unstable hashes.
- Risk state is inferred without response evidence.

## Retry Strategy
- Repeat capture in isolated profiles and compare drift.
- Mark unstable fields instead of forcing equality.

## Cleanup Rules
- Remove browser profile exports after retaining redacted reports.
- Do not publish unique personal fingerprint values.

## Acceptance Checks
- Surface inventory identifies stable, unstable, and unknown fields.
- Any block reason is tied to observed evidence, not assumption.

## Related Skills
- `browser-fingerprint-surface-lab`
- `fingerprint-block-reason-diagnostics`
- `web-h5-loop-engineering`
