# Challenge State Lab

This Phase 4 lab is a local synthetic evidence package. It documents solver/parity/drift behavior without live-site credentials or production traffic.

## Files

- `manifest.json`
- `negative_cases.json`
- `validation_report.json`
- `reports/replay_or_trace_report.md`

## Coverage

- no_challenge
- captcha_detected
- waf_challenge_detected
- fingerprint_challenge_detected
- login_required
- rate_limited
- forbidden
- token_expired
- manual_review_required
- pure_api_replay_ready
- pure_api_replay_blocked

## Validation

- `tools/validate_challenge_state_lab.py`
