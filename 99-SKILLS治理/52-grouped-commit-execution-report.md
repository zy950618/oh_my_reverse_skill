# Grouped Commit Execution Report

status: GROUPED_COMMITS_CREATED

created_at: 2026-07-02T01:27:29.468935+00:00

push_performed: NO

## Before Reset Snapshot

before_reset_staged_files: 1264

before_reset_insertions: 635189

before_reset_deletions: 33

snapshot_files:
- `.ci-out/final-staged-diff-stat-before-reset.txt`
- `.ci-out/final-staged-files-before-reset.txt`
- `.ci-out/final-staged-status-before-reset.txt`

## Group Plan

commit_count_planned: 6

planned_group_file_counts:
- group 1: 66
- group 2: 81
- group 3: 824
- group 4: 53
- group 5: 109
- group 6: 132

planned_total_files_after_report: 1265

## Commits

commit_count: 6

commit_hashes:
- group 1: `aad67ed` governance: standardize loop routing and reports
- group 2: `61fe016` contracts: add pure API and tool execution contracts
- group 3: `618dc01` captcha: add model delivery lab and validators
- group 4: `861e578` fingerprint: add risk lab active-ready validation
- group 5: `721086b` airline: add local order-flow lab and observation packs
- group 6: self-referential hash recorded in final response after commit creation

## Commands Run

- snapshot current staged state before reset
- update group 6 pathspec to include this report
- `git reset`
- `git add --pathspec-from-file=.ci-out/stage-groups/group-1-files.txt`
- `python tools\scan_sensitive_evidence.py --staged`
- `python tools\validate_large_artifacts.py --staged`
- `python tools\validate_artifact_references.py`
- `python tools\cleanup_workspace.py --check`
- `python tools\ci_gate.py .ci-out`
- `python tools\ci_gate.py .ci-out --release`
- `python tools\verify_delivery.py --domain none`
- `git commit -m "governance: standardize loop routing and reports"`
- `git commit --amend --no-edit`
- `git add --pathspec-from-file=.ci-out/stage-groups/group-2-files.txt`
- `python tools\validate_pure_api_delivery.py public-range-evidence/pure-api-lab`
- `python tools\validate_pure_api_delivery.py public-range-evidence/airline-lab-order-flow`
- `git commit -m "contracts: add pure API and tool execution contracts"`
- `git add --pathspec-from-file=.ci-out/stage-groups/group-3-files.txt`
- `python public-range-evidence\captcha-model-lab\inference\sample_infer.py`
- `python public-range-evidence\captcha-model-lab\eval\evaluate_pass_rate.py`
- `python tools\validate_captcha_action_schema.py`
- `python tools\validate_captcha_dataset.py`
- `python tools\validate_captcha_training_report.py`
- `python tools\validate_captcha_model_package.py`
- `python tools\validate_captcha_pass_rate.py`
- `git commit -m "captcha: add model delivery lab and validators"`
- `git add --pathspec-from-file=.ci-out/stage-groups/group-4-files.txt`
- `python tools\validate_fingerprint_surface_lab.py`
- `python tools\validate_block_reason_lab.py`
- `python tools\validate_browser_context_isolation.py`
- `python tools\validate_captcha_fingerprint_linkage.py`
- `git commit -m "fingerprint: add risk lab active-ready validation"`
- `git add --pathspec-from-file=.ci-out/stage-groups/group-5-files.txt`
- `python tools\validate_real_site_observation_pack.py public-range-evidence/real-site-observation-pack`
- `python public-range-evidence\airline-lab-order-flow\replay\replay.py`
- `python public-range-evidence\airline-lab-order-flow\tests\run_order_flow_tests.py`
- `git commit -m "airline: add local order-flow lab and observation packs"`
- `git add --pathspec-from-file=.ci-out/stage-groups/group-6-files.txt`
- `python tools\ci_gate.py .ci-out`
- `python tools\ci_gate.py .ci-out --release`
- `git commit -m "release: add gates, artifact checks, and cleanup hardening"`
- `git status --short`
- `python tools\ci_gate.py .ci-out --release`
- `python tools\validate_artifact_references.py`
- `python tools\cleanup_workspace.py --check`
- `python tools\scan_sensitive_evidence.py`
- `python tools\validate_large_artifacts.py`

## Validation Result

validation_result: PASS_FINAL_LOCAL

remaining_untracked: 0

remaining_modified: 0

staged_files: 0

push_performed: NO
