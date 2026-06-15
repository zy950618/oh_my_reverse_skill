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

## Required comparison

For each round compare:

- request headers/body fields;
- response status and business code;
- JSON Pointer for success/failure;
- cookies/storage added or changed;
- script URL/hash;
- token field and expiry behavior;
- request id order and event sequence.

## Old vs new rule

Old capture can guide search, but cannot prove current behavior until revalidated by a fresh capture. Write `stale` when unsure.
