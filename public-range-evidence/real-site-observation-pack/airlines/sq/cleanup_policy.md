# SQ Observation Cleanup Policy

- Keep committed artifacts limited to schemas, templates, redacted summaries, and local fixtures.
- Do not commit raw HAR, screenshots with PII, raw cookies, storage values, tokens, account data, booking payloads, or payment data.
- If authorized live evidence is collected later, store raw material outside the repo or archive it under manual review with a manifest before any cleanup.
- Redacted evidence must include `live_observation_status` and the authorization scope.
- Cleanup must not delete the only copy of evidence before a manifest records its location and reason.
