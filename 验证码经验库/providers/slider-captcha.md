# Slider CAPTCHA provider memory

Status: seed, provider-common only. Do not treat this as proof for any specific site.

## Common Flow

```text
challenge/config endpoint -> user interaction result -> verify endpoint -> token/state write -> business API unlock
```

## Evidence To Collect

- challenge endpoint and challenge id field;
- verification endpoint and result field;
- token/state write location;
- verified/unverified business API diff;
- TTL/session binding;
- repeat verified capture.

## Known Pitfalls

- UI slider success may not equal backend verification success.
- Interaction result fields are often bound to session/challenge id.
- Do not infer provider behavior from one site.

## Boundary

No fake interaction generation, solver, stealth, fingerprint spoofing, proxy rotation, or token forging.
