# Provider common flow

This file captures the provider-level abstraction. It is intentionally not a bypass guide.

## Common model

```text
widget_script
  -> provider_config
  -> challenge/config request
  -> token/result callback
  -> site backend verify
  -> session/risk state write
  -> business API check
```

## Provider classes

| provider | common evidence |
|---|---|
| reCAPTCHA | widget script, sitekey, action/mode, token field, backend verify result, score/pass state if visible |
| hCaptcha | widget script, sitekey, rqdata if present, token field, backend verify result |
| Turnstile | widget script, sitekey, managed/invisible mode, token field, backend verify result |
| slider | challenge id, config endpoint, interaction-result field, verify endpoint, state write |
| click-select | challenge image/config, answer/result field, verify endpoint, state write |
| custom-risk-state | risk field names, state endpoint, cookie/storage write, business API dependency |

## Required split

Keep provider common flow separate from site binding:

```text
provider_common_flow: stable pattern shared across sites
site_binding: domain/action/sitekey/token field/session/verify endpoint/business API
```

Do not promote a site binding to provider common flow until at least two independent site bindings are observed.
