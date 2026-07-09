{
  "scope": {
    "domain": "none",
    "market": "none",
    "locale": "none",
    "currency": "none",
    "stage": "low_cost_structure",
    "auth_state": "none",
    "target_api": "score-json-output"
  },
  "capability_claim": "STRUCTURE_ONLY",
  "fresh_evidence": {
    "run_id": "",
    "capture_id": "",
    "captured_at": "2026-07-09T06:53:28+00:00",
    "browser_profile_id": "",
    "state_reset": "",
    "network_log_id": "",
    "script_hash": "",
    "auth_state": "none",
    "source_freshness": "unknown"
  },
  "json_output_acceptance": {
    "command": "PYTHONDONTWRITEBYTECODE=1 python3 tools/governance/score_skills.py --repo . --manifest skills-manifest.json --json-out .ci-out/score-summary.json",
    "exit_code": 0,
    "json_file": ".ci-out/score-summary.json",
    "json_tool_exit_code": 0,
    "single_json_object": true,
    "required_fields_present": [
      "tool",
      "status",
      "strict_score",
      "strict_components",
      "notes",
      "legacy_layer_average",
      "legacy_minimum_skill_total",
      "manifest",
      "layers",
      "skill_count",
      "manifest_skill_count",
      "out_dir"
    ],
    "ci_gate_stdout_mixed_into_json": false
  },
  "stdout_compatibility": {
    "command": "PYTHONDONTWRITEBYTECODE=1 python3 tools/governance/score_skills.py --repo . --manifest skills-manifest.json",
    "exit_code": 0,
    "observed": "stdout retained summary JSON plus ci_gate human-readable report"
  },
  "release_gate": {
    "command": "PYTHONDONTWRITEBYTECODE=1 python3 tools/governance/ci_gate.py .ci-out --manifest skills-manifest.json --release",
    "exit_code": 0,
    "status": "pass",
    "reason": "Release Gate passed on Claude rerun"
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
    "human_review_boundary": "none_after_claude_rerun_release_gate_passed",
    "blocked_as_negative_eval": "",
    "not_allowed": "no bypass instructions, no fingerprint spoofing, no clearance cookie reuse"
  },
  "data_acceptance": {
    "ui_api_parity": "not_applicable_structure_only",
    "json_pointers": [
      "/tool",
      "/status",
      "/strict_score",
      "/strict_components",
      "/notes",
      "/legacy_layer_average",
      "/legacy_minimum_skill_total",
      "/manifest",
      "/layers",
      "/skill_count",
      "/manifest_skill_count",
      "/out_dir"
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
    "status": "pass",
    "can_claim_concurrency": false,
    "can_claim_stable": false,
    "remaining_gap": "structure-only; no real-domain/sign/token/concurrency/WAF production capability claimed"
  }
}
