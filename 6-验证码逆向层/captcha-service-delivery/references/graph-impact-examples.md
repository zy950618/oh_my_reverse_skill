# Captcha graph and impact examples

## reCAPTCHA business API unlock

Graph Delta:

```text
node captcha_provider:recaptcha-v3
node captcha_binding:example.com/search
node captcha_token:body.gRecaptchaResponse
node verify_endpoint:/api/verify-captcha
node state:session.captcha_verified
node business_endpoint:/api/search
node eval:captcha-service/verified-vs-unverified

edge captcha_binding:example.com/search -> captcha_provider:recaptcha-v3 uses
edge captcha_token:body.gRecaptchaResponse -> captcha_binding:example.com/search bound_to
edge verify_endpoint:/api/verify-captcha -> captcha_token:body.gRecaptchaResponse verifies
edge state:session.captcha_verified -> verify_endpoint:/api/verify-captcha produced_by
edge business_endpoint:/api/search -> state:session.captcha_verified requires
edge business_endpoint:/api/search -> eval:captcha-service/verified-vs-unverified covered_by
```

Impact Regression:

```text
change: /api/search now requires recaptcha verified state
impacted:
  - business_endpoint:/api/search
  - verify_endpoint:/api/verify-captcha
  - token_field:body.gRecaptchaResponse
  - session replay
  - concurrency claim
must_run:
  - clean_unverified capture
  - verified capture
  - repeat_verified capture
  - token TTL comparison
  - old-vs-new HAR diff
risk:
  - old verified cookie reused as fresh state
  - action/sitekey drift
  - one session generalized to all sessions
```

## Slider verification state

Graph Delta:

```text
node captcha_provider:slider-custom
node challenge_endpoint:/captcha/get
node verify_endpoint:/captcha/check
node state:cookie.slider_verified
node business_endpoint:/api/quote

edge challenge_endpoint:/captcha/get -> captcha_provider:slider-custom issues
edge verify_endpoint:/captcha/check -> state:cookie.slider_verified writes
edge business_endpoint:/api/quote -> state:cookie.slider_verified requires
```

Scope / Evidence Ledger:

```text
scope: map endpoints, fields, verified/unverified deltas, TTL, and session binding
freshness: clean_unverified + verified + repeat_verified captures required
stale_or_unverified: old verified cookie, old provider script hash, old token field, copied session state
```
