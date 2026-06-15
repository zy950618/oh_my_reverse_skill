# _example.com captcha memory

This is a non-production example showing the expected shape. Copy `_templates/captcha-memory.md` for real domains.

## Scope

```yaml
domain: example.com
provider: recaptcha
captcha_type: recaptcha-v3
business_stage: search
market: unverified
locale: unverified
auth_state: anonymous
```

## Fresh Evidence Table

| capture_id | captured_at | browser_profile_id | state_reset | auth_state | network_log_id | script_hash | source_freshness |
|---|---|---|---|---|---|---|---|
| example-clean | 2026-06-12T00:00:00Z | profile-example | cookies/storage/cache cleared | clean_unverified | HAR#1 | unverified | stale-example |

## Note

Do not use this example as evidence for any real site.
