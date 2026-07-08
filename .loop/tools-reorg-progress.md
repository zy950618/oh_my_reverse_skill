# tools reorg low-loop progress

## Current state
- task: tools-reorg-low-loop
- base_branch: test
- current_loop: loop-00-ledger-inventory
- current_branch: loop/tools-00-ledger-inventory
- status: in_progress
- next_action: validate Loop 00 ledger files, commit, merge back to test, then start Loop 01.

## Completed loops
- none

## Tool classification

### Keep existing subpackages
- tools/recorder/: cloak/HAR/recording fixture capture helpers.
- tools/replayer/: fixture validation, replay, diff, schema alert, consistency reports.

### Move targets by future loop
- Loop 01 governance: append_drift_history.py, ci_gate.py, scaffold_evals.py, score_skills.py, skill_score_config.py.
- Loop 01 validators: validate_links.py, validate_loop.py, validate_routing.py, validate_skill_frontmatter.py, validate_structure.py.
- Loop 02 evidence: scan_sensitive_evidence.py, validate_artifact_references.py, validate_business_data_assertions.py, validate_evidence_policy.py, validate_large_artifacts.py, validate_public_range_evidence.py, validate_pure_api_delivery.py, validate_real_execution_proof.py, validate_real_site_observation_pack.py, validate_scope_contract.py.
- Loop 03 web_h5: fixture_freshness_report.py, real_website_handling_planner.py, validate_web_h5_crawler_gate.py, validate_web_h5_loop_gate.py, validate_web_h5_real_execution_gate.py, verify_delivery.py, web_h5_acceptance_report.py, web_h5_loop_runner.py.
- Loop 04 js_runtime: js_env_contract_builder.py, js_page_runtime_capture.py, js_page_runtime_parity_runner.py, js_runtime_diff_report.py, js_signature_regression.py.
- Loop 04 fingerprint: fingerprint_profile_consistency_check.py, fingerprint_range_runner.py, fingerprint_risk_state_report.py, fingerprint_surface_capture.py, fingerprint_surface_diff.py, validate_block_reason_lab.py, validate_browser_context_isolation.py, validate_fingerprint_surface_lab.py.
- Loop 05 site_memory: backfill_from_site_memory.py, sync_site_memory.py.
- Loop 05 lifecycle: cleanup_workspace.py, post_task_reminder.py.

## Compatibility entrypoints to preserve initially
- tools/score_skills.py
- tools/ci_gate.py
- tools/verify_delivery.py
- tools/post_task_reminder.py
- tools/sync_site_memory.py
- tools/cleanup_workspace.py
- top-level validate and web_h5 scripts that are referenced by docs, hooks, workflows, or CLAUDE.md.

## Candidate cleanup inventory

### Likely local/generated
- .DS_Store
- .ci-out/*.json
- .loop/*.md from prior loops

### Historical/control artifacts needing confirmation before deletion
- .agent-control/backups/phase2-dirty-test-*.patch|txt
- .agent-control/codex-results/phase2-*.md
- .agent-control/baseline/BASLINE_FINDINGS_LOCAL_ONLY.md
- .agent-control/ohmrs-evolution-pack/**

### Do not delete without migration
- 站点经验库/**
- 逆向工程经验库/**
- public-range-evidence/**
- unique validation/cleanup ledgers under 99-SKILLS治理/**

## Resume rules
1. Run `git status` first.
2. If on `loop/tools-00-ledger-inventory`, finish validation and merge.
3. If on `test`, start the next incomplete loop from this file and `.loop/tools-reorg-ledger.json`.
4. Do not start a new loop branch before the prior loop is merged back into `test`.
