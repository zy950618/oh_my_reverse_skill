# <domain> captcha memory

## Scope

```yaml
domain:
provider:
captcha_type:
business_stage:
market:
locale:
auth_state:
```

## Fresh Evidence Table

| capture_id | captured_at | browser_profile_id | state_reset | auth_state | network_log_id | script_hash | source_freshness |
|---|---|---|---|---|---|---|---|
| TODO | TODO | TODO | TODO | clean_unverified/verified/repeat_verified | TODO | TODO | fresh/stale/unknown |

## Provider Flow

```text
widget_script -> config/challenge -> token/result -> backend verify -> state write -> business API
```

## Site Binding

```yaml
sitekey:
action:
mode:
widget_script:
widget_script_hash:
token_field:
verify_endpoint:
business_endpoint:
success_pointer:
failure_pointer:
```

## Verified vs Unverified Diff

| item | clean_unverified | verified | repeat_verified | conclusion |
|---|---|---|---|---|
| request field | TODO | TODO | TODO | TODO |
| response pointer | TODO | TODO | TODO | TODO |
| cookie/storage | TODO | TODO | TODO | TODO |
| business unlock | TODO | TODO | TODO | TODO |

## Old vs New Diff

```yaml
old_capture:
new_capture:
still_valid:
invalidated:
revalidated_by:
```

## Token and State Lifecycle

```yaml
ttl_observed:
bound_to:
  - domain
  - action
  - session
  - cookie
  - risk_state
expiry_test:
cross_session_test:
concurrency_status:
```

## Known Failures

| date | symptom | root cause | correct handling |
|---|---|---|---|
| TODO | TODO | TODO | TODO |
