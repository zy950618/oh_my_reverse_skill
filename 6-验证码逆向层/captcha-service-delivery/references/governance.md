Version: 0.1.0

# captcha-service-delivery governance

## Why this exists

CAPTCHA reverse work fails when the agent treats an old token, old HAR, old browser profile, or old script hash as current evidence. This skill requires real capture freshness and repeated comparison before any delivery claim.

## Mandatory sequence

1. Read prior experience.
2. Create a fresh capture plan.
3. Clear browser state or record why it cannot be cleared.
4. Capture `clean_unverified`.
5. Complete verification through authorized/manual flow.
6. Capture `verified`.
7. Restart/refresh and capture `repeat_verified`.
8. Compare all three captures plus any old evidence.
9. Update graph and impact regression.

## Fresh evidence fields

Use the exact fields from `99-SKILLS治理/16-实战复测与证据新鲜度规约.md`:

```yaml
capture_id:
captured_at:
browser_profile_id:
state_reset:
network_log_id:
script_hash:
auth_state:
session_id_hint:
source_freshness:
```

## Failure modes to catch

- Old token reused as fresh token.
- Verified cookie confused with anonymous cookie.
- Browser cache served old script.
- Service worker kept stale response.
- Same HAR replayed after provider changed sitekey/action.
- Single successful verified session generalized to concurrency.
- Captcha challenge classified by UI only, without backend verify endpoint evidence.

## Known failures and test log

Write real failures to `站点经验库/<domain>/known-failures.md` and test lessons to `站点经验库/<domain>/test-log-lessons.md`. CAPTCHA-specific details also go to `验证码经验库/domains/<domain>/captcha-memory.md`.

## Drift policy

Treat provider script hash changes, sitekey/action drift, token field movement, verify endpoint changes, response JSON Pointer drift, cache/service-worker effects, and changed business unlock behavior as drift. Drift must invalidate old mappings until fresh capture revalidates them.

## Delivery gate

Do not claim success unless:

- provider common flow is mapped;
- site binding is mapped;
- verified/unverified API delta is shown;
- token/state lifecycle is measured or marked unverified;
- old evidence is invalidated or revalidated;
- graph and impact records are updated;
- scope ledger is present, and every reused old capture is explicitly revalidated or marked stale.
