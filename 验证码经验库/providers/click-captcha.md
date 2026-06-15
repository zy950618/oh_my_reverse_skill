# Click-select CAPTCHA provider memory

Status: seed, provider-common only. Do not treat this as proof for any specific site.

## Common Flow

```text
challenge image/config -> answer/result -> verify endpoint -> token/state write -> business API unlock
```

## Evidence To Collect

- challenge image/config endpoint;
- challenge id and answer/result field;
- verification endpoint;
- state write and business API dependency;
- verified/unverified JSON Pointer diff;
- old-vs-new capture comparison.

## Known Pitfalls

- Challenge images and point answers are per challenge/session.
- A verified session can mask the original blocked response.
- Old challenge ids must never be treated as current.

## Boundary

No automated solving, bypass, fake interaction generation, stealth, fingerprint spoofing, proxy rotation, or token forging.
