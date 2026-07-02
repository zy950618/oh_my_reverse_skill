---
name: captcha-visual-recognition-lab
description: Build and evaluate local or authorized CAPTCHA visual recognition for text, slider, rotate, click, icon-match, and multi-image tasks with metrics, failure samples, and Phase 2.1 evidence boundaries.
triggers: [visual-captcha, screenshot-recognition, compatible-lab, failure-cases]
license: MIT
platforms: [cross-platform]
category: captcha
version: 0.1.0
---

# CAPTCHA Visual Recognition Lab

Use this skill only for localhost, public labs, synthetic datasets, owned targets, or explicitly authorized test targets.

## Workflow

Use screenshots/images as solver input, run redaction and leakage audits, and keep per-family recognition metrics separate from action replay and business API proof.

## Success Criteria

Recognition evidence must include target family, sample count, success count, success rate, p95 error, failure samples, and scoped capability decision.

## Boundaries

This skill is not responsible for production CAPTCHA bypass or vendor production claims from compatible labs.

## Governance

Write known failures, eval backlog, run_id, and drift notes. Any answer leak invalidates the visual-recognition run.

## Change Log

- 2026-06-30: Added Phase 3.9 compatible-lab recognition boundary from `run-20260630-113000-phase3-9-vendor-shield-range`.

## Phase 3.10 Realism Hardening Rule

- Source run_id: `run-20260630-163000-phase3-10-realism-hardening`.
- Evidence: `public-range-evidence/shumei-compatible-lab/run-20260630-163000-phase3-10-realism-hardening.json` and `public-range-evidence/aliyun-compatible-lab/run-20260630-163000-phase3-10-realism-hardening.json`.
- Scope: `localhost_vendor_compatible_lab` with easy/medium/hard/adversarial buckets.
- Capability level: visual/action families can be `positive_candidate` only when realism, leakage, and blackbox gates pass.
- Boundary: not a verified vendor solver and not stable_positive.
- Failure cases: top failures are in each target `failure-cases.json`; use them for hard/adversarial replay.
- Eval: `evals/phase3-10/shumei-compatible-lab-hardening.yaml` and `evals/phase3-10/aliyun-compatible-lab-hardening.yaml`.
- Next training goal: reduce hard/adversarial failures without reading answer, label, DOM answer, or query expected fields.

## Scope

- Generate or consume labeled CAPTCHA images.
- Run local recognition baselines for text, slider, rotate, click, icon-match, and multi-image challenges.
- Produce metrics, failure cases, evidence JSON, eval YAML, and experience cards.
- Feed observed failure modes back into this skill and related evals.

## Phase 3 Rule

Algorithm benchmark success is not real-site CAPTCHA/WAF positive capability. A result can be treated as `local_lab_positive` only inside the local lab run, and public-range evidence must remain governed by:

- `execution_status`
- `control_flow_status`
- `business_data_status`
- `capability_status`

Do not set `capability_status=positive_allowed` unless Phase 2.1 business data assertions also pass against a final business API and server-side ledger.

## Required Outputs

Each challenge type run must produce:

- evidence JSON under `public-range-evidence/captcha-vision-lab/`
- metrics JSON
- failure cases JSON
- experience card under `skills-experience/`
- eval YAML
- SKILL rule update or rule confirmation

## First-Round Local Lessons

- Text CAPTCHA baseline is expected to expose OCR weakness before optimization; low sequence accuracy is valid failure evidence.
- Slider baseline must report pixel offset error, not just pass/fail.
- Rotate baseline must report angular error with wraparound handling.
- Action replay must execute on a localhost page and record screenshot, trace/network summary when browser automation is used.

## Phase 3.1 Hardening Rules

- Synthetic easy pass cannot be generalized to real sites.
- Hard and adversarial tiers are required before claiming algorithm robustness.
- `text-captcha` with very low OCR metrics remains `training_needed`; it must not be written as mature OCR capability.
- Solvers must not read label files, DOM state, query parameters, or metadata answers for predictions.
- Recognition evidence must record the challenge difficulty and the transform pipeline.

## Capability Levels

- `L0_structure_only`: samples or schemas exist only.
- `L1_synthetic_easy_baseline`: easy synthetic samples run with baseline metrics.
- `L2_synthetic_hard_benchmark`: hard synthetic samples meet thresholds.
- `L3_local_action_replay`: localhost action replay succeeds for the same challenge instance.
- `L4_authorized_sample_benchmark`: owned or authorized sample benchmark meets thresholds.
- `L5_authorized_target_positive`: authorized target passes final business API and business data assertions.

Current Phase 3.1 evidence remains synthetic/local. It can support `L1` or `L3` depending on challenge type, but not `L5`.

## Phase 3.5 Longrun Feedback

- Source run_id: `run-20260630-041500-phase3-5-longrun`.
- Failure evidence: `public-range-evidence/longrun/phase3-5/run-20260630-041500-phase3-5-longrun/failure-cases.json`.
- Rule added: visual recognition must cover `text-captcha`, `slider-captcha`, `rotate-captcha`, `click-captcha`, and `multi-image-select` in one longrun before capability promotion is considered.
- Eval added: `evals/longrun/phase3-5/001-phase3-5-longrun-regression.yaml`.
- Capability impact: Phase 3.5 remains `memory_only`; it can harden local baselines but does not prove third-party CAPTCHA/WAF handling.

## Phase 3.7 Public Range Feedback

- Source run_id: `run-20260630-083000-phase3-7-real-public-range`.
- Public range evidence:
  - `public-range-evidence/opencaptchaworld/run-20260630-083000-phase3-7-real-public-range.json`.
  - `public-range-evidence/gocaptcha-official/run-20260630-083000-phase3-7-real-public-range.json`.
- Failure evidence:
  - `public-range-evidence/raw/opencaptchaworld/run-20260630-083000-phase3-7-real-public-range/failure-cases.json`.
  - `public-range-evidence/raw/gocaptcha-official/run-20260630-083000-phase3-7-real-public-range/failure-cases.json`.
- Rule added: public/open-source ranges may promote only to `positive_candidate` unless blackbox gate, leakage audit, per-family thresholds, failure-case feedback, and repeat evidence all pass. A range-specific validation weakness such as OpenCaptchaWorld `Hold_Button` must not be counted as CAPTCHA vision maturity.
- GoCaptcha official lesson: slide/drag image-only replay can pass on the official local service, but rotate/click failures block verified promotion for the whole target.
- OpenCaptchaWorld lesson: Connect_icon, Image_Matching, and Coordinates expose real visual relation failures; leaked `correct_option_index`/`hold_time` fields must be recorded as payload risk and must not be used for predictions.
- Evals added: `evals/phase3-7/001-opencaptcha-answer-field-leakage.yaml`, `evals/phase3-7/002-connect-icon-visual-relation.yaml`, `evals/phase3-7/003-hold-button-validation-weakness.yaml`.
- Capability impact: Phase 3.7 can add scoped public-range `positive_candidate` evidence for GoCaptcha official slide/drag and OpenCaptchaWorld action replay. It does not prove stable solver capability, production CAPTCHA handling, WAF bypass, fingerprint evasion, or third-party site success.

## Phase 3.8 Family-Level Recognition Rule

- Source run_id: `run-20260630-101500-phase3-8-family-hardening`.
- Evidence: `public-range-evidence/opencaptchaworld/run-20260630-101500-phase3-8-family-hardening.json`, `public-range-evidence/gocaptcha-official/run-20260630-101500-phase3-8-family-hardening.json`, and failure images under `public-range-evidence/raw/*/run-20260630-101500-phase3-8-family-hardening/failure-case-images/`.
- Evals: `evals/phase3-8/002-opencaptcha-family-visual-failures.yaml`, `evals/phase3-8/005-gocaptcha-rotate-training-needed.yaml`, `evals/phase3-8/006-gocaptcha-click-training-needed.yaml`.
- Capabilities must be split by challenge_family/challenge_type. GoCaptcha slide/drag candidates cannot mask rotate/click training_needed. OpenCaptchaWorld Hold_Button cannot mask Connect_icon, Image_Matching, or Coordinates failures.
- OCR remains `memory_only` while sequence accuracy is low, even if char accuracy improves. Low sequence accuracy must be recorded as a downgrade reason, not a positive capability.
- Every solver input must be a screenshot/challenge image/crop, instruction text, and allowed action schema only. `solver_input_payload` must be redacted by `tools/solver_input_redactor.py`; leaked public range fields make the run INVALID.

## Phase 3.9 Vendor-Compatible Visual Rule

- Source run_id: `run-20260630-113000-phase3-9-vendor-shield-range`.
- Evidence: `public-range-evidence/shumei-compatible-lab/run-20260630-113000-phase3-9-vendor-shield-range.json` and `public-range-evidence/aliyun-compatible-lab/run-20260630-113000-phase3-9-vendor-shield-range.json`.
- Evals: `evals/phase3-9/shumei-compatible-lab-compatible-lab.yaml`, `evals/phase3-9/aliyun-compatible-lab-compatible-lab.yaml`.
- Compatible vendor labs may train slide/select/icon/sequence/spatial families, but evidence must include `compatible_lab=true`, `official_vendor=false`, and `not_generalizable_to_vendor_production=true`.
- Positive candidate is family scoped and local only; unknown third-party Shumei/Aliyun challenges remain observation-only.
## Phase 3.11 visual replay gate

- source_run_id: `run-20260630-173000-phase3-11-type-matrix`
- evidence: `public-range-evidence/shumei-compatible-lab/run-20260630-173000-phase3-11-type-matrix.json`, `public-range-evidence/aliyun-compatible-lab/run-20260630-173000-phase3-11-type-matrix.json`
- evals: `evals/phase3-11/vendor-compatible-type-matrix.yaml`
- A solver may use only challenge image/screenshot, instruction text, and allowed action schema. It must not read label_path, metadata answer, DOM answer, query expected, server expected, or action replay expected fields.
- The per-family metrics must include easy/medium/hard/adversarial sample_count, success_rate, mean_error, p95_error, failure_cases, action_trace, blackbox_gate, leakage_audit, and realism_audit.
- A local compatible lab can be positive_candidate at most; it is not official vendor production capability.
## Phase 3.12 local model input boundary

- source_run_id: `run-20260630-183000-phase3-12-model-flywheel`
- evidence: `datasets/captcha_flywheel/predictions/run-20260630-183000-phase3-12-model-flywheel/prediction_manifest.json`
- evals: `evals/phase3-12/`
- Allowed inference inputs are challenge image/screenshot crop, instruction text, allowed action schema, and local model checkpoint output.
- Forbidden inference inputs are third-party CAPTCHA solving platforms, remote solver API, paid human solver service, leaked answer fields, DOM answers, query expected values, server expected values, provider internal tokens, copied browser tokens, and copied clearance cookies.
- Every prediction must record solver_source with model_id, local_only, external_api_used=false, third_party_solver_used=false, and label_leakage=false.
