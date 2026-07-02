# CZ Observation Runbook

Status: authorized-live-ready.

1. Confirm written authorization for public homepage observation.
2. Set `AUTHORIZED_LIVE_OBSERVATION=1` and provide approved target URL if live observation is allowed.
3. Capture only public, non-login, non-payment, non-order surfaces.
4. Redact cookies, tokens, PII, order identifiers, and full payloads.
5. Stop on CAPTCHA, WAF, login, booking, payment, or account flow.
6. Keep final business delivery browserless; browser capture is analysis-only.

Without authorization input, live status remains `NOT_RUN_NO_AUTHORIZATION_INPUT`.
