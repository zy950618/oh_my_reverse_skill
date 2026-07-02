# public-range-evidence schema

Evidence files live at `public-range-evidence/<target_id>/<run_id>.json` and
are validated by `tools/validate_public_range_evidence.py`.

Minimum required structure:

```json
{
  "schema_version": "public-range-evidence/v1",
  "run_id": "run-YYYYMMDD-HHMMSS-target",
  "capture_id": "cap-YYYYMMDD-HHMMSS-target-mode",
  "captured_at": "ISO-8601",
  "source_freshness": "fresh",
  "execution_status": "REAL_EXECUTION_PASS | STRUCTURE_ONLY | BLOCKED | INVALID",
  "control_flow_status": "CONTROL_FLOW_PASS | CONTROL_FLOW_FAIL | NOT_RUN",
  "business_data_status": "DATA_ASSERTION_PASS | DATA_ASSERTION_FAIL | NOT_RUN",
  "capability_status": "positive_allowed | negative_eval_only | memory_only | prohibited | unverified",
  "target": {
    "id": "target_id",
    "url": "https://example.test/",
    "host": "example.test",
    "type": "official_demo | public_training_range | local_open_source_range | bot_signal_diagnostics | official_provider_testing"
  },
  "skills": ["web-h5-loop-engineering", "skills-evaluation-governance"],
  "scope": {
    "domain": "target_id",
    "stage": "public_range",
    "auth_state": "none | guest | test_account | local",
    "mode": "observation | provider_detect | state_observer | direct_interface_replay | concurrency_ladder | bot_signal_record | backend_verify_boundary",
    "in_scope": [],
    "out_of_scope": []
  },
  "backend_acceptance": {
    "status": "pass | fail | not_run",
    "final_api_endpoint_confirmed": false,
    "endpoint": "",
    "observed_status": 0,
    "content_type": "",
    "json_pointers": [],
    "direct_interface_call": {
      "status": "pass | fail | not_run",
      "browser_dependency": false,
      "uses_browser_profile": false,
      "uses_live_storage": false,
      "uses_manual_cookie_or_token": false,
      "observed_status": 0,
      "content_type": "",
      "json_type": "",
      "json_pointers": []
    },
    "repeat_direct_interface_call": {
      "status": "pass | fail | not_run",
      "browser_dependency": false,
      "uses_browser_profile": false,
      "uses_live_storage": false,
      "uses_manual_cookie_or_token": false,
      "observed_status": 0,
      "content_type": "",
      "json_type": "",
      "json_pointers": []
    }
  },
  "business_data_assertions": {
    "status": "pass | fail | not_run",
    "server_ledger_path": "public-range-evidence/raw/.../server-business-ledger.json",
    "positive_assertions": [
      {
        "name": "list-detail-submit item_id consistency",
        "status": "pass | fail",
        "expected": "risk-item-1",
        "actual": "risk-item-1",
        "evidence_pointer": "/direct_interface_repeat/direct_interface_call/submitted_item_id"
      }
    ],
    "negative_assertions": [
      {
        "name": "missing verify",
        "status": "pass | fail",
        "expected_ledger_delta": 0,
        "actual_ledger_delta": 0,
        "rejection_reason": "challenge_required",
        "evidence_pointer": "/negative_evals/items/..."
      }
    ],
    "concurrency_assertions": {
      "worker_1": {
        "status": "pass | fail",
        "expected_success_count": 2,
        "actual_success_count": 2,
        "expected_ledger_delta": 2,
        "actual_ledger_delta": 2,
        "duplicate_order_count": 0,
        "cross_worker_pollution_count": 0,
        "wrong_owner_count": 0,
        "orphan_order_count": 0
      },
      "worker_2": {},
      "worker_5": {},
      "worker_10": {}
    },
    "final_decision": {
      "data_assertion_pass": true,
      "why_not_pass": []
    }
  },
  "execution_proof": {
    "command": "python tools/run_phase1_local_targets.py",
    "cwd": "E:/SKILLS/oh_my_reverse_skill",
    "exit_code": 0,
    "started_at": "ISO-8601",
    "ended_at": "ISO-8601",
    "stdout_log": "public-range-evidence/raw/...stdout.log",
    "stderr_log": "public-range-evidence/raw/...stderr.log",
    "screenshot_paths": ["public-range-evidence/raw/...png"],
    "network_summary_paths": ["public-range-evidence/raw/...json"],
    "browser_trace_path": "public-range-evidence/raw/...zip",
    "generated_by": "tool or runner name",
    "synthetic": false
  },
  "decision": {
    "positive_allowed": false,
    "skills_participation": "negative_eval_only | memory_only | prohibited | positive_allowed",
    "blocked_reason": "",
    "why_not_positive": []
  }
}
```

`positive_allowed` is stricter than structural validity and control-flow
success. It requires all four layers:

1. `execution_status: REAL_EXECUTION_PASS`.
2. `control_flow_status: CONTROL_FLOW_PASS`.
3. `business_data_status: DATA_ASSERTION_PASS`.
4. `capability_status: positive_allowed`.

Fresh evidence, final API confirmation, direct non-browser JSON acceptance,
repeat direct non-browser JSON acceptance, non-empty JSON Pointers, no copied
browser profile/live storage/manual cookie/manual token, and passing
`business_data_assertions` are all required. Provider testing keys, CAPTCHA
widgets, challenge/config endpoints, verify endpoints, and browser-only captures
remain boundary or negative evidence unless a final business API is accepted,
repeat verified, and server-side business ledger assertions pass.

`execution_proof` is required before an evidence file can count as a real local
or public-range run. Files without it are `STRUCTURE_ONLY`: they may remain valid
boundary or historical evidence, but they do not prove that the target was
started, opened in a browser, network-captured, or replayed in the current run.
For CAPTCHA/WAF/risk-control evidence, `execution_proof` still cannot make the
result `positive_allowed` unless final protected business API acceptance and
repeat direct non-browser acceptance are present.

Status fields are deliberately split:

- `execution_status` answers whether the target actually ran and produced
  command/log/artifact proof. `REAL_EXECUTION_PASS` means "executed for real",
  not "capability succeeded".
- `control_flow_status` answers whether the chain and state machine ran through
  the expected control-flow path. `CONTROL_FLOW_PASS` means the endpoint/state
  path worked, not that business data is correct.
- `business_data_status` answers whether business data consistency passed.
  `DATA_ASSERTION_PASS` requires a server-side business ledger, positive
  assertions, negative assertions with `ledger_delta=0`, concurrency assertions,
  unique orders, and order/session/worker ownership checks.
- `capability_status` answers whether the result may improve positive skill
  capability. Only `positive_allowed` means positive capability. Local dummy
  labs, provider testing keys, standalone siteverify responses, and boundary
  evals can be `REAL_EXECUTION_PASS` while still being `negative_eval_only` or
  `memory_only`.
- `high_concurrency_positive` is prohibited unless a full 1/2/5/10 ladder runs
  against an authorized business API with per-worker session/cache/token
  isolation, backend acceptance, and business ledger consistency. HTTP 200,
  `failure_rate`, and p95 are insufficient without order/session/worker
  ownership, duplicate-order checks, orphan-order checks, and cross-worker
  pollution checks. Localhost dummy concurrency does not prove production high
  concurrency.

Business data assertions must prove at minimum:

1. `list -> detail -> submit` data consistency.
2. Submitted `item_id` came from the current session's list.
3. Submit was preceded by current-session detail.
4. `detail_nonce` came from the current session.
5. `item_version` matched.
6. Risk token was bound to session/action/worker/nonce.
7. Challenge-before-submit failed with `ledger_delta=0`.
8. Verify-after-submit succeeded with `ledger_delta=1`.
9. Negative evals had `ledger_delta=0`.
10. Concurrency success count matched ledger order delta.
11. `order_id` values were unique or matched an explicitly documented idempotency rule.
12. No orphan orders.
13. No cross-worker pollution.
14. No wrong owner.
15. No unrecorded business side effects.
