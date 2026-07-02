# Real Site Observation Pack Reference

Real-site observation packs are structure-only until an authorized fresh run
adds evidence. They may store target metadata, planned observation surfaces,
expected artifacts, and safety boundaries.

Allowed pack status values:

- STRUCTURE_ONLY
- BLOCKED
- OBSERVED_AUTHORIZED

For a structure-only pack:

- observed facts must be empty
- live_capture_performed must be false
- execution_status must be STRUCTURE_ONLY
- capability_status must be memory_only or unverified
- business_data_status must be NOT_RUN

Forbidden:

- marking assumed airline routes, endpoints, protections, or tokens as observed
- claiming WAF/CAPTCHA/fingerprint bypass
- recording live cookies, tokens, account data, PII, payment data, or order data
- reusing old browser profiles or clearance values

