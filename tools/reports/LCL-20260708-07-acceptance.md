{
  "scope": {
    "domain": "none",
    "market": "none",
    "locale": "none",
    "currency": "none",
    "stage": "low_cost_structure",
    "auth_state": "none",
    "target_api": "external-fusion-unknown-source-ledger"
  },
  "capability_claim": "STRUCTURE_ONLY",
  "fresh_evidence": {
    "run_id": "",
    "capture_id": "",
    "captured_at": "2026-07-09T07:13:30+00:00",
    "browser_profile_id": "",
    "state_reset": "",
    "network_log_id": "",
    "script_hash": "",
    "auth_state": "none",
    "source_freshness": "unknown"
  },
  "external_fusion_acceptance": {
    "source_inventory_complete_for_unknown_source_mode": true,
    "source_names_recorded": [
      "ai-reverse-toolkit",
      "jshook-skill",
      "hello_js_reverse_skill"
    ],
    "all_sources_fact_level": "unverified",
    "source_url_or_path_present": false,
    "license_gate_status": "unknown",
    "allowed_use_restricted": true,
    "forbidden_use_recorded": true,
    "target_layer_justified_after_evidence_only": true,
    "validation_required_recorded": true,
    "no_code_copied": true,
    "no_active_skill_created": true,
    "blocker": "user must provide source URL/path or explicit public repo search authorization"
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
    "authorization_scope": "not_applicable_structure_only",
    "protected_business_api_acceptance": "not_applicable_structure_only",
    "failure_split": [
      "source_identity_missing",
      "license_unknown"
    ],
    "backoff": "",
    "jitter": "",
    "session_retirement": "",
    "kill_switch": "stop_before_fetch_or_import_without_url_or_path",
    "human_review_boundary": "source URL/path or explicit search authorization required",
    "blocked_as_negative_eval": "",
    "not_allowed": "no guessed GitHub URL, no code copy, no active skill creation, no WAF defeat, no fingerprint falsification"
  },
  "data_acceptance": {
    "ui_api_parity": "not_applicable_structure_only",
    "json_pointers": [
      "/external_fusion_acceptance/source_names_recorded",
      "/external_fusion_acceptance/all_sources_fact_level",
      "/external_fusion_acceptance/license_gate_status",
      "/external_fusion_acceptance/blocker"
    ],
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
        "not_run_structure_only"
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
    "task_count": 1,
    "success_browserless_verified": 0,
    "concurrency_verified": 0,
    "strict_review_pass_count": 1,
    "flaky_count": 0,
    "blocked_by_protection": 0,
    "latest_replay_rate": null
  },
  "decision": {
    "status": "blocked_waiting_source_url_or_path",
    "can_claim_concurrency": false,
    "can_claim_stable": false,
    "remaining_gap": "external repository identity, license, content, and capability remain unverified until URL/path or explicit search authorization is provided"
  }
}
