# Airline Lab Order Flow

Status: local scaffold, structure-only.

This lab is a self-owned localhost order-flow skeleton for future direct
interface, fixture replay, context isolation, and business-ledger validation.
It is not a real airline adapter and does not call real airline sites.

Directories:

- `mock_server/`: standard-library localhost mock server.
- `fastapi_adapter/`: optional FastAPI adapter scaffold.
- `fixtures/`: sanitized request/response fixtures.
- `replay/`: standard-library fixture replay checks.
- `reports/`: scope, graph, and impact notes.
- `sdk_examples/`: local-only client examples.

Boundary:

- no live airline calls
- no account, payment, or PII
- no CAPTCHA/WAF bypass
- no fingerprint spoofing
- no positive capability claim

