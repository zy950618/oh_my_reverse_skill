# Real capture protocol

## Browser cleanup checklist

Before `clean_unverified` capture:

- clear cookies for target domain and provider domain when allowed;
- clear localStorage/sessionStorage/indexedDB/cache storage;
- unregister service workers or record existing worker state;
- disable cache in DevTools or record cache status;
- start a new browser profile or record `browser_profile_id`;
- create a new `capture_id`.

## Capture rounds

| round | goal |
|---|---|
| `clean_unverified` | observe blocked state and baseline API response |
| `verified` | observe token/state write and unlocked API response |
| `repeat_verified` | detect freshness, TTL, and session stability |

If `verified` requires human interaction, switch to `human_reviewed_verified` only after the operator completes the visible challenge under recorded capture. Until then, write `verified: blocked_by_manual_challenge` and set task status to `blocked`.

If an authorized browser automation run completes the verification without human action, switch to `browser_automated_verified` only after token/state evidence is captured and the final business API is accepted in both `verified` and `repeat_verified` rounds. Do not use a challenge page, provider config response, or token endpoint alone as success evidence.

## Required comparison

For each round compare:

- request headers/body fields;
- response status and business code;
- JSON Pointer for success/failure;
- cookies/storage added or changed;
- script URL/hash;
- token field and expiry behavior;
- request id order and event sequence.
- verification mode: `browser_automated_verified`, `human_reviewed_verified`, `blocked_by_manual_challenge`, `blocked_by_protection`, or `unverified`.

## Manual-assisted capture

When a challenge appears, record a Human Review Protocol with:

- visible browser command or tool;
- browser profile id or user data directory;
- exact URL and variant;
- user action and stop condition;
- active HAR/DevTools listener;
- completion criteria using site backend JSON Pointer;
- repeat flow using a fresh context or documented refresh;
- failure evidence path if the user cannot complete the challenge.

## Old vs new rule

Old capture can guide search, but cannot prove current behavior until revalidated by a fresh capture. Write `stale` when unsure.
