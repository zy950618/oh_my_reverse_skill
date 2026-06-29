# Crawler Acceptance Pack

This pack defines the minimum evidence for Web/H5 crawler delivery. Acceptance Report and risk-control evidence are mandatory for concurrency claims. It is
generic across sites, but every result must still be scoped to the current
domain, market, locale, currency, stage, auth state, and target API.

## Required Artifact

Create or validate an acceptance report:

```bash
python tools/web_h5_acceptance_report.py template --out acceptance-report.json --domain <domain> --stage <stage> --target-api <method:url>
python tools/web_h5_acceptance_report.py validate --report acceptance-report.json
```

Use `--require-complete` only when claiming completion, concurrency, or stable
operation.

## Standard Gates

1. Fresh Evidence: current run_id, capture_id, network_log_id, script_hash,
   profile, state_reset, and source_freshness.
2. Clean State Retest: `clean_unverified`, `verified`, and `repeat_verified`
   with a new context or cleared cookie/storage/cache/service worker.
3. Anti-Flake: at least three same-scope same-class observations; mixed
   `200/403/200` is flaky.
4. Concurrency Ladder: 1/2/5/10 worker stages, each with request counts,
   success/failure counts, 403/429/503 rate, P95, refresh counts, stop
   condition, session isolation, and backend acceptance.
5. Risk-control: authorization scope, protected business API acceptance,
   failure split, backoff, jitter, session retirement, kill switch, human review
   boundary, and negative eval path for blocked protection.
6. UI/API parity: visible webpage fields mapped to API JSON Pointer fields with
   tolerance rules and screenshot or DOM evidence.
7. strict freshness: strict fixture review passes, no expired snapshots, no
   review_pending placeholders, and recent replay/diff report for the current
   adapter target.
8. Metrics: task_count, success_browserless_verified, concurrency_verified,
   strict_review_pass_count, flaky_count, blocked_by_protection, and latest
   replay/freshness state.

## Risk-Control Concurrency

Allowed engineering actions:

- isolated browser context and storage per worker
- no shared cookie jar or token cache by default
- delay, backoff, and jitter based on observed failure class
- retire doubtful sessions instead of reusing them silently
- stop concurrency on configured 403/429/503, failure-rate, or P95 thresholds
- record blocked protection as blocked/human-review/negative eval

Not allowed:

- WAF or CAPTCHA bypass instructions
- webdriver hiding or fingerprint spoofing
- proxy rotation guidance
- copying clearance cookies, device IDs, risk tokens, or old profile state as
  fresh evidence

## Delivery Decision

The acceptance report can decide:

```yaml
status: complete | flaky | blocked | human_review | stale | unverified
can_claim_concurrency: true | false
can_claim_stable: true | false
remaining_gap:
```

If `can_claim_concurrency` is true, every worker stage must pass with session
isolation and protected business API backend acceptance. If `can_claim_stable`
is true, anti-flake must be stable and fixture freshness must be fresh.
