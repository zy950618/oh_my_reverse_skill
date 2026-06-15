# Provider flow template

## Provider

```yaml
provider:
captcha_type:
versions_seen:
common_widget_scripts:
common_token_fields:
common_verify_shape:
```

## Common Flow

```text
load widget -> load challenge/config -> produce token/result -> site verify -> state write -> business API check
```

## Evidence Requirements

- widget script URL/hash;
- site binding fields;
- challenge/config request;
- token/result field;
- backend verify endpoint;
- verified/unverified business API diff;
- TTL/session binding evidence.

## Not Provider-Common Until Proven

Do not promote these to common flow from a single site:

- action name;
- score/pass threshold;
- token TTL;
- cookie/storage write target;
- business endpoint unlock rule;
- concurrency behavior.
