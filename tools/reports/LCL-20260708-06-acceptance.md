{
  "scope": {
    "domain": "none",
    "market": "none",
    "locale": "none",
    "currency": "none",
    "stage": "low_cost_structure",
    "auth_state": "none",
    "target_api": "js-runtime-evidence-manifest"
  },
  "capability_claim": "STRUCTURE_ONLY",
  "fresh_evidence": {
    "run_id": "",
    "capture_id": "",
    "captured_at": "2026-07-09T07:02:18+00:00",
    "browser_profile_id": "",
    "state_reset": "",
    "network_log_id": "",
    "script_hash": "",
    "auth_state": "none",
    "source_freshness": "unknown"
  },
  "scripts_manifest_acceptance": {
    "contract_file": "tool-contracts/collect_scripts.contract.md",
    "required_source_identity": "url_or_inline_id",
    "required_fields_present": [
      "sha256",
      "captured_at",
      "source_freshness",
      "redaction_status",
      "raw_secret_persisted",
      "storage_policy",
      "authorization_scope",
      "script_kind",
      "size_bytes",
      "initiator_or_initiator_status"
    ],
    "source_freshness_enum": [
      "fresh",
      "stale",
      "unknown"
    ],
    "redaction_status_enum": [
      "clean",
      "redacted",
      "blocked",
      "manual_review_required"
    ],
    "long_term_evidence_requires_raw_secret_persisted_false": true,
    "raw_secret_true_decision": "blocked_or_manual_review_only",
    "stale_unknown_positive_capability_proof_allowed": false,
    "structure_only_no_real_capture": true
  },
  "runtime_boundary_acceptance": {
    "runtime_parity_claim_limited_to": [
      "named_fixture",
      "input",
      "run_id"
    ],
    "does_not_prove": [
      "business_api_acceptance",
      "risk_token_validity",
      "waf_or_challenge_success",
      "clearance_cookie_reuse",
      "production_readiness"
    ]
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
    "failure_split": [],
    "backoff": "",
    "jitter": "",
    "session_retirement": "",
    "kill_switch": "",
    "human_review_boundary": "raw_secret_detected_or_manual_review_required",
    "blocked_as_negative_eval": "",
    "not_allowed": "no bypass instructions, no fingerprint spoofing, no clearance cookie reuse"
  },
  "data_acceptance": {
    "ui_api_parity": "not_applicable_structure_only",
    "json_pointers": [
      "/scripts/0/url",
      "/scripts/0/inline_id",
      "/scripts/0/sha256",
      "/scripts/0/captured_at",
      "/scripts/0/source_freshness",
      "/scripts/0/redaction_status",
      "/scripts/0/raw_secret_persisted",
      "/scripts/0/storage_policy",
      "/scripts/0/authorization_scope",
      "/scripts/0/script_kind",
      "/scripts/0/size_bytes",
      "/scripts/0/initiator",
      "/scripts/0/initiator_status"
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
    "status": "blocked",
    "can_claim_concurrency": false,
    "can_claim_stable": false,
    "remaining_gap": "structure-only; ci_gate --release was blocked by localhost bind PermissionError in current sandbox; no real-domain/script-capture/sign/token/concurrency/WAF production capability claimed"
  }
}
