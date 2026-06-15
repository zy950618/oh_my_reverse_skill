# Site binding schema

Use this schema for `验证码经验库/domains/<domain>/captcha-memory.md`.

```yaml
domain:
provider:
captcha_type:
version:
scope:
  market:
  locale:
  auth_state:
  business_stage:
site_binding:
  sitekey:
  action:
  mode:
  widget_script:
  widget_script_hash:
challenge:
  config_endpoint:
  challenge_id_field:
  request_fields:
token:
  token_field:
  ttl_observed:
  bound_to:
    - domain
    - action
    - session
    - cookie
    - risk_state
verify:
  verify_endpoint:
  request_fields:
  success_pointer:
  failure_pointer:
state_write:
  cookies:
  local_storage:
  session_storage:
effects:
  unlocks_endpoint:
  changes_response:
  blocks_replay:
  breaks_concurrency:
captures:
  clean_unverified:
  verified:
  repeat_verified:
freshness:
  old_evidence_invalidated:
  revalidated_by:
```

Any unknown field must be written as `unverified`, not guessed.
