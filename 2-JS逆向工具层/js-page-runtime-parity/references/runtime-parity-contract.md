# Runtime Parity Contract

Use only after an entry skill identifies an authorized JavaScript module or localhost lab fixture.

Success Criteria:
- Browser, Node, V8, and PageRuntime outputs are compared.
- Missing APIs are listed in an environment contract.
- Regression fixtures are written for repeat checks.

Boundaries: not responsible for WAF handling, fingerprint mutation, or unauthorized token generation.

Evidence Limits:
- Runtime parity proves only the named fixture, input, and `run_id` that were compared.
- Runtime parity does not prove business API acceptance, risk-token validity, WAF/challenge success, clearance-cookie reuse, or production readiness.
- `stale` or `unknown` script freshness can support regression context only; it cannot support a positive capability claim.
- If script evidence is linked, its manifest must identify `sha256`, `captured_at`, `source_freshness`, `redaction_status`, and `raw_secret_persisted`; long-term evidence requires `raw_secret_persisted: false`.

Site memory: record parity failures and environment contracts in the caller skill evidence ledger.
