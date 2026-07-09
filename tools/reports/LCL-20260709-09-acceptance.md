{
  "scope": {
    "domain": "none",
    "market": "none",
    "locale": "none",
    "currency": "none",
    "stage": "low_cost_structure",
    "auth_state": "none",
    "target_api": "external-clean-room-fusion-contract"
  },
  "capability_claim": "STRUCTURE_ONLY",
  "fresh_evidence": {
    "run_id": "",
    "capture_id": "",
    "captured_at": "2026-07-09T16:43:32+08:00",
    "browser_profile_id": "",
    "state_reset": "",
    "network_log_id": "",
    "script_hash": "",
    "auth_state": "none",
    "source_freshness": "internal_lcl08_fact_pack"
  },
  "fusion_contract_acceptance": {
    "loop_id": "LCL-20260709-09",
    "state": "structure_contract_and_eval_seed_recorded",
    "structure_only": true,
    "external_source_fact_pack_required": true,
    "license_decision_required": true,
    "prohibited_use_scan_required": true,
    "allowed_fusion_mode_required": true,
    "attribution_plan_required_when_needed": true,
    "validation_ledger_required": true,
    "raw_external_files_fetched": false,
    "external_code_imported": false,
    "external_templates_imported": false,
    "external_prompts_imported": false,
    "active_skill_created": false,
    "skills_manifest_edited": false,
    "allowed_outputs": [
      "abstract_contract",
      "eval_seed_without_verbatim_copy",
      "reference_notes_with_attribution"
    ],
    "risk_policy": "anti-detection, concealment, fingerprint falsification, defeat, hook injection, cookie/token/sign, and WAF/challenge-adjacent markers are observation/lab/evidence-contract only",
    "validation_suite_passed": true
  },
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
    "authorization_scope": "internal_structure_contract_from_lcl08_fact_packs",
    "protected_business_api_acceptance": "not_applicable_structure_only",
    "failure_split": [
      "hello_license_remains_unknown",
      "no_external_raw_files_read"
    ],
    "backoff": "",
    "jitter": "",
    "session_retirement": "",
    "kill_switch": "stop_before_code_template_prompt_import_or_active_skill_creation",
    "human_review_boundary": "license conflict, risk-sensitive capability, evidence conflict, or requested production capability",
    "blocked_as_negative_eval": "",
    "not_allowed": "no external code import, no external template import, no active skill creation, no concealment/falsification/WAF defeat/fingerprint falsification, no production success claim"
  },
  "data_acceptance": {
    "ui_api_parity": "not_applicable_structure_only",
    "json_pointers": [
      "/fusion_contract_acceptance/state",
      "/fusion_contract_acceptance/external_source_fact_pack_required",
      "/fusion_contract_acceptance/license_decision_required",
      "/fusion_contract_acceptance/prohibited_use_scan_required",
      "/fusion_contract_acceptance/allowed_fusion_mode_required",
      "/fusion_contract_acceptance/validation_ledger_required",
      "/fusion_contract_acceptance/raw_external_files_fetched",
      "/fusion_contract_acceptance/active_skill_created"
    ],
    "consistency_rate": null,
    "adapter_target": "",
    "screenshot_or_dom_evidence": ""
  },
  "business_data_status": "NOT_RUN",
  "business_ledger_summary": {
    "server_ledger_path": "",
    "positive_assertion_count": 0,
    "negative_assertion_count": 6
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
      "no external raw repository files read",
      "no external code copied",
      "no external templates or prompts copied",
      "no active skill created",
      "skills-manifest.json not edited",
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
    "source_freshness": "internal_lcl08_fact_pack"
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
      "PYTHONDONTWRITEBYTECODE=1 python3 tools/web_h5/web_h5_loop_runner.py validate --ledger tools/reports/LCL-20260709-09-loop-ledger.json",
      "PYTHONDONTWRITEBYTECODE=1 python3 tools/web_h5/web_h5_acceptance_report.py validate --report tools/reports/LCL-20260709-09-acceptance.md",
      "PYTHONDONTWRITEBYTECODE=1 python3 tools/web_h5/verify_delivery.py --domain none"
    ]
  },
  "cleanup_ledger": {
    "removed": [],
    "kept_as_evidence": [
      "tool-contracts/external_clean_room_fusion.contract.md",
      "1-业务流程层/skills-evaluation-governance/evals/026-external-source-fusion-gate.yaml",
      "tools/reports/LCL-20260709-09-loop-ledger.json",
      "tools/reports/LCL-20260709-09-acceptance.md"
    ],
    "still_unverified": [
      "hello_js_reverse_skill license",
      "raw external file contents by design",
      "no real-domain capability; structure-only scope by design"
    ]
  },
  "decision": {
    "status": "validated_structure_pass",
    "can_claim_concurrency": false,
    "can_claim_stable": false,
    "remaining_gap": "no external raw files were read; no real-domain capability is claimed"
  }
}
