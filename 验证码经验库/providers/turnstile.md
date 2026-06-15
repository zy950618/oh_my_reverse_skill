# Cloudflare Turnstile provider memory

Status: seed, provider-common only. Do not treat this as proof for any specific site.

## Common Flow

```text
widget script -> site binding(sitekey/mode) -> token -> site backend verify -> session/business state
```

## Evidence To Collect

- widget script URL and hash;
- sitekey and mode(managed/invisible/explicit if observed);
- token field and backend verify endpoint/effect;
- business API before/after verification;
- cookie/storage state changes;
- repeat capture after browser restart or state reset.

## Known Pitfalls

- Managed mode may blur challenge and risk state.
- Business endpoint may return HTTP 200 while payload remains denied.
- Service worker/cache can hide script drift.

## Boundary

No clearance cookie generation, bypass, stealth, fingerprint spoofing, proxy rotation, or access-control bypass.
