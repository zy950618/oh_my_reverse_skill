# Provider detection signals

Version: 0.1.0

Provider detection is evidence routing, not a success claim. The detector should
identify likely provider class, challenge type, and required evidence.

## Signals

| provider | signal examples | required follow-up |
|---|---|---|
| `recaptcha` | `google.com/recaptcha`, `grecaptcha`, `g-recaptcha-response` | sitekey, action, token field, backend verify, business API diff |
| `hcaptcha` | `hcaptcha.com`, `h-captcha-response`, `rqdata` | sitekey, rqdata presence, token field, backend verify, business API diff |
| `turnstile` | `challenges.cloudflare.com/turnstile`, `cf-turnstile-response` | sitekey, mode, token field, backend verify, business API diff |
| `slider` | drag handle, gap image, puzzle config endpoint | challenge id, geometry, action schema, verify endpoint |
| `click_select` | image grid, prompt text, selected indexes | prompt, image set id, click labels, verify endpoint |
| `custom_risk_state` | challenge state cookie, risk endpoint, local verifier | token lifecycle, wrong-session/action negative controls |

## Rules

- Use multiple signals when possible: script URL, DOM field, request path, and
  backend field.
- Mark provider as `unknown` when only UI appearance is available.
- Do not store raw tokens or challenge payloads in provider detection output.
