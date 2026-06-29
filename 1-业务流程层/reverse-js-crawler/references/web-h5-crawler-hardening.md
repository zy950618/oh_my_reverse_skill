# Web/H5 Crawler Hardening

This reference is scoped to Web/H5 crawler reverse engineering. It does not add CAPTCHA/WAF bypass tactics. It only defines proof gates for repeatability, capture freshness, session isolation, concurrency, risk-control engineering, UI/API parity, fixture freshness, and anti-overgeneralization.

## External Patterns Reviewed

- Ponytail: reuse existing code and platform capability before adding new code; small diffs still require root-cause reading and one runnable check for non-trivial logic. Use this as a governance style, not as crawler-specific code.
- Playwright BrowserContext: use isolated clean-slate contexts so cookies, local storage, and session storage do not leak between runs or workers.
- Scrapy AutoThrottle: concurrency must be coupled with delay/backoff evidence; non-200 responses must not make the crawler speed up.
- Crawlee SessionPool and BrowserPool: session/cookie/proxy/browser lifecycle is explicit; blocked or doubtful sessions are marked bad or retired instead of reused silently.

## Mandatory Proof Gates

### 1. Packet Evidence Gate

Every key conclusion must point to current-run evidence:

```text
run_id:
capture_id:
captured_at:
browser_profile_id:
state_reset:
network_log_id:
script_url_or_hash:
auth_state:
source_freshness:
```

Without these fields, the conclusion is at most `unverified`.

### 2. Clean-State Retest Gate

Run at least these groups or record an explicit blocker:

| Group | State rule | Purpose |
|---|---|---|
| `clean_unverified` | new context or cleared cookie/storage/cache/service worker | prove the unauthenticated baseline |
| `verified` | authorized or human-reviewed state when allowed | prove what changed after verification |
| `repeat_verified` | fresh context or restarted browser after verification | prove the state is repeatable |

Each group records request fields, response JSON Pointers, cookie/storage changes, token TTL/binding, and script hash. One lucky 200 does not pass this gate.

### 3. Anti-Flake Gate

For the same scope, require at least 3 same-class observations before saying stable:

```text
same_scope:
  domain:
  market:
  locale:
  currency:
  stage:
  auth_state:
  session_scope:
runs:
  - status_class:
  - status_class:
  - status_class:
decision: stable | flaky | blocked | unverified
```

Mixed results such as `200, 403, 200` are `flaky`, not success.

### 4. Concurrency Ladder Gate

Batch or concurrency claims require staged evidence:

| Stage | Required result |
|---|---|
| 1 worker | baseline repeatability and failure split |
| 2 workers | no session/cache cross-contamination |
| 5 workers | success/failure rates and P95 remain acceptable |
| 10 workers | only after previous stages pass |

Record total requests, success count, failure count, 403/429/503 rates, P95, token refresh count, cookie refresh count, stop condition, and rollback.

### 5. Session/Cache Isolation Gate

Workers do not share these by default:

- browser context
- cookie jar
- localStorage/sessionStorage
- token/risk/session cache
- account state
- browser profile

Any sharing requires evidence that the cache key includes domain, host, market, locale, currency, stage, auth state, UA/client hints, profile scope, and session scope. The protected business API must accept the request, not only a challenge or token endpoint.

### 6. Risk-Control Concurrency Gate

Risk-control is an implementation gate for safe concurrency, not a bypass gate.
Record:

- authorization scope
- protected business API backend acceptance
- failure split: business error, parameter error, sign/token mismatch, WAF/challenge, rate limit, data unavailable, implementation bug
- delay/backoff/jitter policy
- session retirement rule for doubtful workers
- kill switch thresholds for 403/429/503, failure rate, P95, and repeated blocker
- human review boundary
- blocked_as_negative_eval path

Allowed actions are isolation, measured backoff, stopping concurrency, retiring
bad sessions, re-recording fresh fixtures, and human review. Do not document WAF
or CAPTCHA bypass, webdriver hiding, fingerprint spoofing, proxy rotation, or
clearance cookie reuse.

### 7. Data Acceptance Gate

The crawler must prove data matches the real webpage, not only that an API
returns 200. Record:

- visible webpage field or selector
- API JSON Pointer
- tolerance rule
- screenshot or DOM evidence
- adapter target or script output
- consistency rate

If webpage UI, API response, replay, or schema diff disagree, the result is
`flaky`, `blocked`, or `unverified` until the mismatch is resolved.

### 8. Fixture Freshness Governance Gate

Use `tools/fixture_freshness_report.py` and strict fixture review before using
fixtures as current evidence.

Freshness requires:

- `strict-review` exit code 0
- expired_count = 0
- review_pending_count = 0
- recent replay/diff report for the current adapter target
- source_freshness = fresh

Historical replay rate is stale when fixtures are expired, review is pending,
or the current adapter target has not been replayed.

### 9. Quantitative Metrics Gate

Every real run updates metrics without inventing success:

```yaml
task_count:
success_browserless_verified:
concurrency_verified:
strict_review_pass_count:
flaky_count:
blocked_by_protection:
blocked_by_manual_challenge:
latest_replay_rate:
latest_fixture_freshness:
```

`success_browserless_verified` requires final business API backend acceptance
and repeat_verified evidence. `concurrency_verified` requires the 1/2/5/10
worker ladder with session isolation and backend acceptance.

## Fit With Existing Repository Tools

- Use `tools/recorder/*` to turn fresh captures into fixtures.
- Use `tools/replayer/validate_fixtures.py` before treating fixtures as evidence.
- Use `tools/replayer/snapshot_replay.py`, `snapshot_diff.py`, `schema_alert.py`, and `consistency_report.py` for replay and drift.
- Use `tools/web_h5_acceptance_report.py` to generate and validate the crawler acceptance report.
- Use `tools/fixture_freshness_report.py` to expose expired/review_pending fixtures.
- Use `tools/validate_web_h5_crawler_gate.py` to check that the skill package still contains this hardening structure.

## Not Allowed

- Do not claim stability from a single request.
- Do not claim concurrency without the ladder.
- Do not reuse old HAR/token/scriptId/profile as current evidence.
- Do not share cookie/token/cache across workers without current backend acceptance evidence.
- Do not claim stable data when strict fixture freshness or UI/API parity has not passed.
- Do not write CAPTCHA/WAF bypass instructions into this Web/H5 crawler hardening reference.
