# Pre-Commit Hardening Report

State:
COMMIT_READY_GROUPED

## File Counts

- tracked_modified: 30
- untracked_before: 7161
- untracked_after: 1235
- ignored_by_gitignore: 5926
- manual_review: 0
- delete: 0
- archive: 0
- stage_candidates: 1265

## Sensitive Scan

- secret_count: 0
- cookie_count: 0
- token_count: 0
- har_count: 0
- profile_count: 0
- result: PASS
- evidence: `47-secret-and-live-evidence-scan.md`

## Large Artifact Scan

- large_files: 5
- gt_5mb_files: 0
- model_artifacts: 0
- dataset_artifacts: 0
- ignore_recommendations: 0
- manual_review_count: 0
- result: PASS
- evidence: `49-large-artifact-scan.md`

## Stage Plan

- commit_groups: 6
- files per group:
  - commit 1 routing and governance reports: 65
  - commit 2 tool contracts and pure API gates: 81
  - commit 3 CAPTCHA model delivery lab and validators: 827
  - commit 4 fingerprint risk lab and validators: 53
  - commit 5 airline lab and real-site observation packs: 109
  - commit 6 release gate, artifact reference, cleanup tools: 130
- validators per group: recorded in `48-stage-plan.md`
- no_git_add_dot: true
- no_commit: true
- no_push: true

## Validation

- release_gate: PASS
- artifact_reference: PASS; artifact_count=531, unreferenced_artifact_count=0, unknown_file_count=0
- cleanup: PASS; candidate_count=0
- sensitive_scan: PASS
- large_artifact_scan: PASS
- git_status_short: PASS; no ignored raw/checkpoint/model garbage appears in normal status
- git_diff_stat: PASS; 30 tracked modified files

## Remaining

- P0: none for commit readiness gates.
- P1: no staging was performed; staged batches still require explicit user instruction.
- P2: live production/third-party execution remains NOT VERIFIED and outside this pre-commit loop.
