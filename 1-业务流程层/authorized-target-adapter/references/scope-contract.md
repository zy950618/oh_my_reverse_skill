# Scope Contract Reference

Authorized target adaptation requires explicit scope before any site-specific replay or adapter work.

## Required Inputs

- authorization statement and owner/contact
- allowed hosts and disallowed hosts
- allowed modes such as observation, direct replay, or adapter delivery
- rate limit, stop condition, and kill switch
- redaction rules for credentials, cookies, tokens, and business data
- final business API success criteria

## Positive Promotion Gates

A target can move from candidate to positive adapter evidence only when the same run records:

- final business API acceptance
- repeat direct interface acceptance without browser profile or manual token reuse
- business-data assertions against an authoritative ledger or equivalent source
- concurrency ladder with isolated session, cookie, token, cache, and worker ownership
- negative cases with zero business ledger delta
- cleanup and redaction completion

## Boundaries

Unknown third-party and production-unverified targets stay observation-only. This adapter does not authorize WAF defeat, fingerprint falsification, challenge defeat, proxy avoidance, token forgery, or clearance-cookie recycling.
