{
  "scope": {
    "domain": "none",
    "market": "none",
    "locale": "none",
    "currency": "none",
    "stage": "low_cost_structure",
    "auth_state": "none",
    "target_api": "install-safe-uninstall"
  },
  "fresh_evidence": {
    "run_id": "",
    "capture_id": "",
    "captured_at": "2026-07-09T05:37:03.768026+00:00",
    "browser_profile_id": "",
    "state_reset": "",
    "network_log_id": "",
    "script_hash": "",
    "auth_state": "none",
    "source_freshness": "unknown"
  },
  "clean_state_retest": {
    "clean_unverified": {
      "status": "unverified",
      "request": "",
      "response": "",
      "state_delta": ""
    },
    "verified": {
      "status": "unverified",
      "request": "",
      "response": "",
      "state_delta": ""
    },
    "repeat_verified": {
      "status": "unverified",
      "request": "",
      "response": "",
      "state_delta": ""
    }
  },
  "anti_flake": {
    "same_scope_observations": [],
    "decision": "unverified"
  },
  "concurrency_ladder": {
    "worker_1": {
      "status": "unverified",
      "total_requests": 0,
      "success_count": 0,
      "failure_count": 0,
      "status_403_429_503_rate": null,
      "p95_ms": null,
      "token_refresh_count": 0,
      "cookie_refresh_count": 0,
      "session_isolated": false,
      "backend_acceptance": false,
      "stop_condition": ""
    },
    "worker_2": {
      "status": "unverified",
      "total_requests": 0,
      "success_count": 0,
      "failure_count": 0,
      "status_403_429_503_rate": null,
      "p95_ms": null,
      "token_refresh_count": 0,
      "cookie_refresh_count": 0,
      "session_isolated": false,
      "backend_acceptance": false,
      "stop_condition": ""
    },
    "worker_5": {
      "status": "unverified",
      "total_requests": 0,
      "success_count": 0,
      "failure_count": 0,
      "status_403_429_503_rate": null,
      "p95_ms": null,
      "token_refresh_count": 0,
      "cookie_refresh_count": 0,
      "session_isolated": false,
      "backend_acceptance": false,
      "stop_condition": ""
    },
    "worker_10": {
      "status": "unverified",
      "total_requests": 0,
      "success_count": 0,
      "failure_count": 0,
      "status_403_429_503_rate": null,
      "p95_ms": null,
      "token_refresh_count": 0,
      "cookie_refresh_count": 0,
      "session_isolated": false,
      "backend_acceptance": false,
      "stop_condition": ""
    }
  },
  "session_cache_isolation": {
    "browser_context": "isolated_by_default",
    "cookie_jar": "isolated_by_default",
    "local_storage": "isolated_by_default",
    "session_storage": "isolated_by_default",
    "token_cache": "isolated_by_default",
    "account_state": "isolated_by_default",
    "sharing_exception_evidence": ""
  },
  "risk_control": {
    "authorization_scope": "",
    "protected_business_api_acceptance": "",
    "failure_split": [],
    "backoff": "",
    "jitter": "",
    "session_retirement": "",
    "kill_switch": "",
    "human_review_boundary": "",
    "blocked_as_negative_eval": "",
    "not_allowed": "no bypass instructions, no fingerprint spoofing, no clearance cookie reuse"
  },
  "data_acceptance": {
    "ui_api_parity": "",
    "json_pointers": [],
    "consistency_rate": null,
    "adapter_target": "",
    "screenshot_or_dom_evidence": ""
  },
  "business_data_status": "NOT_RUN",
  "business_ledger_summary": {
    "server_ledger_path": "",
    "positive_assertion_count": 0,
    "negative_assertion_count": 0
  },
  "negative_eval_side_effect_summary": {
    "all_negative_ledger_delta_zero": false
  },
  "concurrency_data_consistency_summary": {
    "worker_1": {},
    "worker_2": {},
    "worker_5": {},
    "worker_10": {}
  },
  "business_data_assertions": {
    "status": "not_run",
    "server_ledger_path": "",
    "positive_assertions": [],
    "negative_assertions": [],
    "concurrency_assertions": {},
    "final_decision": {
      "data_assertion_pass": false,
      "why_not_pass": [
        "not_run"
      ]
    }
  },
  "fixtures_freshness": {
    "strict_review_exit_code": null,
    "expired_count": null,
    "review_pending_count": null,
    "recent_report": false,
    "source_freshness": "unknown"
  },
  "metrics": {
    "task_count": 0,
    "success_browserless_verified": 0,
    "concurrency_verified": 0,
    "strict_review_pass_count": 0,
    "flaky_count": 0,
    "blocked_by_protection": 0,
    "latest_replay_rate": null
  },
  "decision": {
    "status": "unverified",
    "can_claim_concurrency": false,
    "can_claim_stable": false,
    "remaining_gap": ""
  }
}
