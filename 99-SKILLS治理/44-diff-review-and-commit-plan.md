# Diff Review and Commit Plan

State:
DIFF_REVIEWED

## Commands

- PASS: `git status --porcelain=v1 -z -uall`
- PASS: `git status --short -uall`
- PASS: `git diff --stat`
- PASS: `git diff --name-only`

## Summary

- file_count: 7187
- tracked_modified: 30
- untracked: 7157
- unknown_file_count: 0
- no_commit: true
- no_push: true

## Reviewed Groups

- routing_docs: 29
- governance_reports: 29
- tool_contracts: 19
- captcha_layer: 58
- fingerprint_layer: 31
- public_range_evidence: 358
- validators: 81
- reviewed_existing_dirty_files: 6581
- unknown: 0

## Group Actions

- routing_docs: keep; routing, top-level contracts, and skill entrypoint changes are covered by `python tools\ci_gate.py .ci-out` and release gate.
- governance_reports: keep; third-loop reassessment, ledgers, stress reports, final report, and gate evidence are covered by release gate plus artifact reference validation.
- tool_contracts: keep; contract artifacts are referenced and covered by artifact reference validation.
- captcha_layer: keep; CAPTCHA skill/eval/reference and lab changes are covered by CAPTCHA validators and 10-run repeat.
- fingerprint_layer: keep; fingerprint skill/eval/reference and lab changes are covered by fingerprint validators and 5-run stress repeat.
- public_range_evidence: keep; public local labs, airline order flow, real-site observation packs, and repeat reports are covered by targeted validators.
- validators: keep; local validator and scoring changes are covered by repeated core validators and release gate.
- reviewed_existing_dirty_files: preserve; these are existing or broad local evidence/dataset/config files in the dirty worktree and were not reverted because the user did not authorize destructive cleanup.

## Commit Plan

- commit 1: routing and governance contracts.
- commit 2: CAPTCHA skill, model lab, negative cases, and repeat reports.
- commit 3: fingerprint risk lab, drift cases, and repeat reports.
- commit 4: airline order-flow lab and real-site observation packs.
- commit 5: validators, scoring, cleanup, and artifact reference tooling.
- commit 6: evidence datasets and longrun artifacts after user review.

## Boundaries

- OBSERVED: worktree remains dirty and large.
- VERIFIED: `unknown_file_count=0` by grouped status review.
- VERIFIED: no commit was performed.
- VERIFIED: no push was performed.
- NOT VERIFIED: user-level approval for staging/commit/push.
