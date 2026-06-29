# Loop Ledgers

## Loop Ledger

```yaml
loop_id:
domain:
scope:
  market:
  locale:
  currency:
  stage:
  auth_state:
  target_api:
max_iterations:
stop_conditions:
human_review_conditions:
roles:
  executor:
  verifier:
  governor:
```

## Iteration Record

```yaml
iteration:
started_at:
executor_action:
executor_evidence:
verifier_checks:
verifier_result: pass | fail | blocked
governor_checks:
governor_result: continue | stop | human_review
learning:
memory_updates:
next_action:
```

## Verification Ledger

```yaml
fresh_evidence:
  run_id:
  capture_id:
  network_log_id:
  script_hash:
  browser_profile_id:
  state_reset:
clean_state_retest:
  clean_unverified:
  verified:
  repeat_verified:
anti_flake:
  observations:
  decision: stable | flaky | blocked | unverified
concurrency_ladder:
  worker_1:
  worker_2:
  worker_5:
  worker_10:
session_cache_isolation:
  cookie_jar:
  storage:
  token_cache:
  account_state:
```

## Runner Execution Ledger

Use `tools/web_h5_loop_runner.py` to create and validate the machine-readable
ledger:

```yaml
loop_id:
created_at:
domain:
scope:
max_iterations:
stop_conditions:
human_review_conditions:
roles:
iterations:
verification:
metrics:
stop_ledger:
cleanup_ledger:
```

Each iteration must record separate Executor, Verifier, and Governor decisions.
Executor output is evidence input, not approval.

## Risk-Control Ledger

```yaml
risk_control:
  authorization_scope:
  protected_business_api_acceptance:
  failure_split:
    - business_error
    - parameter_error
    - sign_or_token_mismatch
    - waf_or_challenge
    - rate_limit
    - implementation_bug
  backoff:
  jitter:
  session_retirement:
  kill_switch:
  human_review_boundary:
  blocked_as_negative_eval:
  not_allowed: no bypass / no fingerprint spoofing / no clearance cookie reuse
```

Risk-control means safe concurrency engineering and evidence. It does not mean
WAF/CAPTCHA bypass.

## Data Acceptance Ledger

```yaml
data_acceptance:
  ui_api_parity:
  visible_fields:
  api_json_pointers:
  tolerance:
  screenshot_or_dom_evidence:
  adapter_target:
  consistency_rate:
```

API 200 is not enough. The verifier must compare the crawler or adapter output
against the webpage-visible data for key fields.

## Fixture Freshness Ledger

```yaml
fixture_freshness:
  strict_review_exit_code:
  expired_count:
  review_pending_count:
  recent_report:
  current_adapter_target:
  source_freshness: fresh | stale | unknown
```

Expired fixtures or review_pending meta cannot be counted as observed evidence.

## Metrics Ledger

```yaml
metrics:
  task_count:
  iterations_total:
  success_browserless_verified:
  concurrency_verified:
  strict_review_pass_count:
  flaky_count:
  blocked_by_protection:
  blocked_by_manual_challenge:
  latest_replay_rate:
  latest_fixture_freshness:
```

Metrics must be updated with zero or blocked counts when the run does not pass.
Do not invent positive counts to improve scoring.

## Stop Ledger

```yaml
stop_reason: complete | max_iterations | repeated_blocker | human_review | scope_risk | cost_limit
evidence:
remaining_gap:
safe_next_step:
```

## Cleanup Ledger

```yaml
removed:
kept_as_evidence:
migrated_to_memory:
still_unverified:
encryption_algorithm_graph_changed: true | false
```
