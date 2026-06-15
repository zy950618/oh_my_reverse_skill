# Captcha impact regression template

## Impact Record

```yaml
change:
direct_impact:
  - provider:
  - binding:
  - token_field:
  - verify_endpoint:
  - business_endpoint:
downstream_impact:
  - replay:
  - field_mapping:
  - session_cache:
  - concurrency:
  - final_api_parity:
required_regression:
  - clean_unverified_capture
  - verified_capture
  - repeat_verified_capture
  - old_vs_new_diff
  - ttl_check
  - session_binding_check
data_validation:
  success_pointer:
  failure_pointer:
  business_payload_pointer:
remaining_risk:
  - unverified:
```
