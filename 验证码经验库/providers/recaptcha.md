# reCAPTCHA provider memory

Status: seed, provider-common only. Do not treat this as proof for any specific site.

## Common Flow

```text
widget script -> site binding(sitekey/action/mode) -> token -> site backend verify -> state/business API decision
```

## Evidence To Collect

- widget script URL and hash;
- sitekey, action, mode;
- token field name in the site request;
- backend verify endpoint or server-side state effect;
- verified vs unverified business API JSON Pointer diff;
- token TTL and session binding.

## Known Pitfalls

- reCAPTCHA v3/Enterprise often looks invisible; UI absence does not mean no verification.
- HTTP 200 does not prove business unlock.
- action/sitekey may differ by page, stage, market, or auth state.
- Old tokens must be marked stale until revalidated by fresh capture.

## Boundary

No token forging, CAPTCHA bypass, solver integration, stealth, fingerprint spoofing, or proxy rotation.
