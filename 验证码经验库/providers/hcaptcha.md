# hCaptcha provider memory

Status: seed, provider-common only. Do not treat this as proof for any specific site.

## Common Flow

```text
widget script -> site binding(sitekey/rqdata if present) -> token -> site backend verify -> state/business API decision
```

## Evidence To Collect

- widget script URL and hash;
- sitekey and optional site-provided challenge data;
- token field and backend verify effect;
- verified/unverified response diff;
- TTL/session binding;
- old-vs-new capture comparison.

## Known Pitfalls

- Challenge data may be site/session specific.
- A token observed in a verified session is not reusable evidence for a clean session.
- Provider common flow must be separated from site-specific binding.

## Boundary

No bypass, solver integration, stealth, fingerprint spoofing, proxy rotation, or access-control bypass.
