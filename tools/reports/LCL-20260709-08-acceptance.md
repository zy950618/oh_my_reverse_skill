{
  "scope": {
    "domain": "none",
    "market": "none",
    "locale": "none",
    "currency": "none",
    "stage": "low_cost_structure",
    "auth_state": "none",
    "target_api": "external-source-fact-packs"
  },
  "capability_claim": "STRUCTURE_ONLY",
  "fresh_evidence": {
    "run_id": "",
    "capture_id": "",
    "captured_at": "2026-07-09T16:28:20+08:00",
    "browser_profile_id": "",
    "state_reset": "",
    "network_log_id": "",
    "script_hash": "",
    "auth_state": "none",
    "source_freshness": "page_observed_head_hash_observed"
  },
  "external_source_fact_acceptance": {
    "loop_id": "LCL-20260709-08",
    "state": "observed_source_facts_recorded",
    "structure_only": true,
    "source_urls_recorded": true,
    "default_branches_recorded": true,
    "git_ls_remote_attempts_recorded": true,
    "git_ls_remote_head_hashes_verified": true,
    "git_ls_remote_blocker": "",
    "visible_license_status_recorded": true,
    "content_inventory_summary_recorded": true,
    "risk_sensitive_markers_recorded": true,
    "allowed_fusion_mode_recorded": true,
    "prohibited_use_recorded": true,
    "decision_recorded": true,
    "raw_external_files_fetched": false,
    "external_code_imported": false,
    "external_templates_imported": false,
    "active_skill_created": false,
    "clean_room_boundary_recorded": true,
    "risk_policy": "anti-detection, stealth, fingerprint spoofing, bypass, cookie/token/sign, and hook injection markers are observation/lab/evidence-contract only; no concealment, falsification, WAF defeat, or production success claim",
    "validation_suite_passed": true
  },
  "source_decisions": [
    {
      "source_name": "jshook-skill",
      "source_url": "https://github.com/wuji66dde/jshook-skill",
      "default_branch": "main",
      "git_ls_remote_head_hash": "ffbd3e87c4e3f4631a51b45393a919216f38a2ba",
      "visible_license_status": "GPL-3.0",
      "allowed_fusion_mode": [
        "reference_only",
        "clean_room_summary",
        "eval_seed_without_verbatim_copy",
        "lab_or_evidence_contract_observation_only"
      ],
      "decision": "GPL_3_repo_reference_only_no_code_import"
    },
    {
      "source_name": "hello_js_reverse_skill",
      "source_url": "https://github.com/WhiteNightShadow/hello_js_reverse_skill",
      "default_branch": "main",
      "git_ls_remote_head_hash": "e5c3c109ed3a9d4b96d8b1ef4061a618c12a5a38",
      "visible_license_status": "unknown_no_license_badge_or_license_file_visible_on_observed_page",
      "allowed_fusion_mode": [
        "reference_only",
        "lab_or_evidence_contract_observation_only"
      ],
      "decision": "unknown_license_reference_only"
    },
    {
      "source_name": "ai-reverse-toolkit",
      "source_url": "https://github.com/zhizhuodemao/ai-reverse-toolkit",
      "default_branch": "main",
      "git_ls_remote_head_hash": "02799de7420ea78c57bf7af8cc0f2d38fef017bd",
      "visible_license_status": "MIT",
      "allowed_fusion_mode": [
        "reference_only",
        "clean_room_summary",
        "eval_seed_without_verbatim_copy",
        "lab_or_evidence_contract_observation_only"
      ],
      "decision": "MIT_repo_clean_room_summary_allowed_but_no_code_import_in_LCL_08"
    }
  ],
  "clean_state_retest": {
    "clean_unverified": {
      "status": "not_applicable_structure_only",
      "request": "",
      "response": "",
      "state_delta": ""
    },
    "verified": {
      "status": "not_applicable_structure_only",
      "request": "",
      "response": "",
      "state_delta": ""
    },
    "repeat_verified": {
      "status": "not_applicable_structure_only",
      "request": "",
      "response": "",
      "state_delta": ""
    }
  },
  "anti_flake": {
    "same_scope_observations": [],
    "decision": "not_applicable_structure_only"
  },
  "concurrency_ladder": {
    "worker_1": {
      "status": "not_applicable_structure_only",
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
      "status": "not_applicable_structure_only",
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
      "status": "not_applicable_structure_only",
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
      "status": "not_applicable_structure_only",
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
    "authorization_scope": "public_repo_page_observation_authorized_by_user",
    "protected_business_api_acceptance": "not_applicable_structure_only",
    "failure_split": [
      "hello_license_unknown",
      "raw_external_files_not_fetched"
    ],
    "backoff": "",
    "jitter": "",
    "session_retirement": "",
    "kill_switch": "stop_before_code_or_template_import",
    "human_review_boundary": "license conflict, risk-sensitive capability, or source evidence conflict",
    "blocked_as_negative_eval": "",
    "not_allowed": "no external code import, no external template import, no active skill creation, no concealment/falsification/WAF defeat/fingerprint falsification, no production success claim"
  },
  "data_acceptance": {
    "ui_api_parity": "not_applicable_structure_only",
    "json_pointers": [
      "/external_source_fact_acceptance/state",
      "/external_source_fact_acceptance/git_ls_remote_head_hashes_verified",
      "/external_source_fact_acceptance/external_code_imported",
      "/source_decisions/0/visible_license_status",
      "/source_decisions/1/visible_license_status",
      "/source_decisions/2/visible_license_status"
    ],
    "consistency_rate": null,
    "adapter_target": "",
    "screenshot_or_dom_evidence": ""
  },
  "business_data_status": "NOT_RUN",
  "business_ledger_summary": {
    "server_ledger_path": "",
    "positive_assertion_count": 0,
    "negative_assertion_count": 4
  },
  "negative_eval_side_effect_summary": {
    "all_negative_ledger_delta_zero": true
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
    "negative_assertions": [
      "no external code copied",
      "no external templates copied",
      "no active skill created",
      "no production capability claimed"
    ],
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
    "source_freshness": "page_observed_head_hash_observed"
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
  "validation_ledger_placeholders": {
    "claude_should_run_after_changes": [
      "PYTHONDONTWRITEBYTECODE=1 python3 tools/validators/validate_links.py",
      "PYTHONDONTWRITEBYTECODE=1 python3 tools/governance/score_skills.py --repo . --manifest skills-manifest.json",
      "PYTHONDONTWRITEBYTECODE=1 python3 tools/governance/ci_gate.py .ci-out --manifest skills-manifest.json --release",
      "PYTHONDONTWRITEBYTECODE=1 python3 tools/web_h5/web_h5_loop_runner.py validate --ledger tools/reports/LCL-20260709-08-loop-ledger.json",
      "PYTHONDONTWRITEBYTECODE=1 python3 tools/web_h5/web_h5_acceptance_report.py validate --report tools/reports/LCL-20260709-08-acceptance.md",
      "PYTHONDONTWRITEBYTECODE=1 python3 tools/web_h5/verify_delivery.py --domain none"
    ]
  },
  "decision": {
    "status": "validated_structure_pass",
    "can_claim_concurrency": false,
    "can_claim_stable": false,
    "remaining_gap": "hello_js_reverse_skill license requires direct license verification; no raw external file contents were fetched; no real-domain capability is claimed"
  }
}
