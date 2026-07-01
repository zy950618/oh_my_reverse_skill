---
name: captcha-dataset-flywheel
description: Build a local CAPTCHA dataset flywheel from scoped failures, labels, train/val/test splits, leakage checks, model outputs, action replay results, and SKILLS feedback. No third-party solver platforms.
license: MIT
platforms: [cross-platform]
category: execution
version: 0.1.1
---

# CAPTCHA Dataset Flywheel

Use this skill when a scoped CAPTCHA/risk lab run produces failed or hard samples that should become local training data.

## Boundaries

This skill is responsible for local or authorized dataset feedback loops. It is not responsible for third-party CAPTCHA bypass, remote solver APIs, provider token reuse, fingerprint spoofing, clearance reuse, or action replay promotion. Route action replay to `captcha-model-action-e2e` and model-family selection to `captcha-open-source-model-stack`.

## Phase 3.12 Rules

- source_run_id: `run-20260630-183000-phase3-12-model-flywheel`
- evidence: `datasets/captcha_flywheel/manifests/run-20260630-183000-phase3-12-model-flywheel/dataset_manifest.json`
- gate evidence: `public-range-evidence/raw/anti-solver-platform-audit/run-20260630-183000-phase3-12-model-flywheel/anti-solver-platform-audit.json`
- evals: `datasets/captcha_flywheel/evals/run-20260630-183000-phase3-12-model-flywheel/`
- forbidden_solver_sources: third_party_captcha_solving_platform, remote_solver_api, paid_human_solver_service, leaked_answer_field, dom_answer, query_expected, server_expected, provider_internal_token, copied_browser_token, copied_clearance_cookie.
- allowed_solver_sources: local_open_source_model, locally_trained_model, image_only_solver, screenshot_crop, instruction_text, allowed_action_schema, public_range_dataset, synthetic_dataset, self_owned_authorized_dataset, manually_labeled_training_sample.
- Every sample must record source_run_id, target_id, family, difficulty, image_path or screenshot/crop, instruction, allowed_actions, label, label_source, feedback_state, action_trace, success, failure_reason, split, and leakage_sensitive_fields_removed.

## Workflow

1. Collect scoped failures and hard samples with `tools/captcha_failure_collector.py`.
2. Build label manifest with `tools/captcha_label_manifest_builder.py`.
3. Split with `tools/captcha_dataset_splitter.py`.
4. Train local/open-source models only.
5. Evaluate holdout metrics and replay failed families.
6. Feed remaining failures back into `datasets/captcha_flywheel/failures/`.

Labels are allowed for training and scoring, but inference records must show `label_read_for_prediction=false`.

## Success Criteria

- Dataset manifest records provenance, split, label source, leakage status, failure reason, and feedback state.
- Negative solver-source checks reject remote solver, copied token, DOM answer, expected answer, and clearance-cookie inputs.
- Holdout and replay results are archived as local/authorized lab evidence only.
- Capability status remains `local_dataset_governance` or `memory_only` unless separate business-data gates pass.

## Governance

- Update model/dataset eval backlog when repeated failures appear.
- Record known leakage patterns and failure classes in references or experience cards.
- Do not promote local dataset improvement into real third-party CAPTCHA/WAF/risk-control capability.
