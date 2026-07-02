# JS Sign / Token Lab

This Phase 4 lab is a local synthetic evidence package. It documents solver/parity/drift behavior without live-site credentials or production traffic.

## Files

- `manifest.json`
- `negative_cases.json`
- `validation_report.json`
- `reports/replay_or_trace_report.md`

## Coverage

- timestamp sign
- nonce sign
- HMAC-like sign
- AES-like payload encryption
- RSA-like envelope mock
- token lifecycle
- expired token
- invalid token
- replay mismatch
- browser-vs-node diff
- Node/V8 pure solver
- Python pure solver

## Validation

- `tools/validate_js_sign_token_lab.py`
