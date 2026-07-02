---
name: captcha-action-planner
description: Convert CAPTCHA recognition results into localhost or authorized-target browser actions such as typing, clicking, dragging, and rotation replay with state-transition evidence.
triggers: [captcha-action, action-replay, vendor-compatible-lab, blackbox-gate]
license: MIT
platforms: [cross-platform]
category: captcha
version: 0.1.0
---

# CAPTCHA Action Planner

Use this skill after recognition produces text, coordinates, offsets, or angles.

## Workflow

Use `tools/captcha_blackbox_solver_gate.py` and `tools/public_range_answer_leakage_audit.py` before accepting action replay. Actions must be derived from screenshot/image inputs, not expected answers.

## Success Criteria

Action planning passes only when replay records include input redaction, action payload, observed success/failure, family metrics, failure cases, and capability decision for the same run_id.

## Boundaries

This skill is not responsible for production vendor CAPTCHA bypass, WAF bypass, token forging, or replay on unapproved targets.

## Governance

Write run_id, known failures, eval backlog, and drift notes. Compatible-lab candidates must stay scoped and not generalize to vendor production.

## Change Log

- 2026-06-30: Added Phase 3.9 Shumei/Aliyun compatible-lab action boundary from `run-20260630-113000-phase3-9-vendor-shield-range`.

## Phase 3.10 Realism Hardening Rule

- Source run_id: `run-20260630-163000-phase3-10-realism-hardening`.
- Evidence: `public-range-evidence/shumei-compatible-lab/run-20260630-163000-phase3-10-realism-hardening.json`, `public-range-evidence/aliyun-compatible-lab/run-20260630-163000-phase3-10-realism-hardening.json`, and action records under `public-range-evidence/raw/*/run-20260630-163000-phase3-10-realism-hardening/`.
- Scope: local compatible labs only.
- Capability level: `positive_candidate` for passing visual/action families; `memory_only` for no_trace/one_click state flows.
- Boundary: no official vendor action replay, no third-party production CAPTCHA handling, no stable_positive from one run.
- Failure cases: hard/adversarial wrong_prediction rows are required feedback, not noise to hide.
- Eval: `evals/phase3-10/shumei-compatible-lab-hardening.yaml` and `evals/phase3-10/aliyun-compatible-lab-hardening.yaml`.
- Next training goal: add replay fixes for failure rows while preserving blackbox/leakage PASS.

## Allowed Actions

- Type recognized text into a localhost or authorized challenge page.
- Drag slider handles in localhost or authorized pages.
- Click target points in local or authorized pages.
- Set or replay rotation controls in local or authorized pages.

## Required Evidence

- action input
- browser state before action
- browser state after action
- challenge instance id or equivalent expected-answer binding
- screenshot
- network summary or explicit local no-network record
- action success and state-transition success metrics

## Phase 3 First-Round Lesson

Recognition output must be replayed against the same challenge instance that produced the label or observation. A correct slider offset can still fail when replayed into a different page state with a different expected gap. Record expected-answer binding, page URL/query/state, and action input together.

## Phase 3.1 Action Rules

- Action replay must carry `challenge_instance_id` or `sample_id`.
- The action input must come from solver prediction over the challenge image.
- Page initialization may use an expected answer only to create a localhost challenge instance; this is not solver input.
- Action success cannot be detached from backend or state-transition acceptance.
- Localhost action replay cannot be generalized to real providers.

## Prohibited Uses

- Do not automate unknown third-party production challenges.
- Do not reuse clearance cookies or human-solved tokens.
- Do not use third-party solver APIs.
- Do not call browser-only success a direct interface positive.

## Phase 3.5 Longrun Feedback

- Source run_id: `run-20260630-041500-phase3-5-longrun`.
- Failure evidence: `public-range-evidence/longrun/phase3-5/run-20260630-041500-phase3-5-longrun/issue-ledger.json`.
- Rule added: action replay must remain bound to the same `sample_id` or `challenge_instance_id`; browser-only action success is not business API success.
- Eval added: `evals/longrun/phase3-5/003-phase3-5-longrun-regression.yaml`.
- Capability impact: action-planner evidence remains `memory_only` unless final business API acceptance and business-data assertions pass.

## Phase 3.6 Public Range Action Replay Feedback

- Source run_id: `run-20260630-071500-phase3-6-1-candidate`.
- Evidence: `public-range-evidence/local-gocaptcha-compatible-lab/run-20260630-071500-phase3-6-1-candidate.json`.
- Blackbox evidence: `public-range-evidence/raw/captcha-blackbox-gate/run-20260630-071500-phase3-6-1-candidate/blackbox-gate.json`.
- Rule added: public/local action replay must solve from browser challenge image, screenshot, or challenge image crop; execute the visible action; record backend verify status; and prove no DOM/query/label/metadata/server expected answer source was used.
- Eval added: `evals/phase3-6/002-gocaptcha-local-action-replay.yaml`.
- Capability impact: the current localhost target is a GoCaptcha-compatible lab, not a real GoCaptcha component. Single-run action replay can only be `positive_candidate`; verified/stable promotion requires multi-sample, multi-difficulty, multi-round blackbox threshold evidence.

## Phase 3.8 Action Planner Rule

- Source run_id: `run-20260630-101500-phase3-8-family-hardening`.
- Evidence: `public-range-evidence/raw/gocaptcha-official/run-20260630-101500-phase3-8-family-hardening/failure-cases.json` and `public-range-evidence/raw/opencaptchaworld/run-20260630-101500-phase3-8-family-hardening/failure-cases.json`.
- Evals: `evals/phase3-8/004-gocaptcha-family-capability-split.yaml`, `evals/phase3-8/005-gocaptcha-rotate-training-needed.yaml`, `evals/phase3-8/006-gocaptcha-click-training-needed.yaml`.
- Action replay must bind prediction to the same `challenge_instance_id` or sample instance. Reusing a prediction across instances is a stale-token/stale-action failure.
- Rotate failures must classify angle prediction, direction, action mapping, coordinate, threshold, and feedback state. Click failures must classify target detection, bbox, click center, page scale, DPR, canvas transform, and timing.
- Canvas/screenshot coordinates must record viewport, DPR, element offset, scale, canvas size, crop box, predicted action list, expected feedback, and actual feedback.

## Phase 3.9 Vendor Action Rule

- Source run_id: `run-20260630-113000-phase3-9-vendor-shield-range`.
- Evidence: `public-range-evidence/shumei-compatible-lab/run-20260630-113000-phase3-9-vendor-shield-range.json` and `public-range-evidence/aliyun-compatible-lab/run-20260630-113000-phase3-9-vendor-shield-range.json`.
- Evals: `evals/phase3-9/shumei-compatible-lab-compatible-lab.yaml`, `evals/phase3-9/aliyun-compatible-lab-compatible-lab.yaml`.
- Action replay must bind challenge instance, instruction, visible image/crop, action schema, and backend feedback. It must not read expected answers, provider tokens, production risk scores, or server-side labels.
- Compatible-lab action success is a local candidate only, never an official vendor service claim.
## Phase 3.11 action replay boundary

- source_run_id: `run-20260630-173000-phase3-11-type-matrix`
- evidence: `public-range-evidence/five-second-shield-lab/run-20260630-173000-phase3-11-type-matrix.json`
- evals: `evals/phase3-11/five-second-shield-profile-matrix.yaml`
- Challenge endpoint success is not business success. Action replay must close through server verify and final business API, with negative eval ledger_delta=0.
- `browser-only success` is memory_only until direct repeat succeeds without a live browser profile, manual cookie, or reused token.
- Required shield profiles include simple_delay_gate, js_signature_gate, redirect_chain_gate, cookie_clearance_gate, browser_state_binding_gate, dynamic_script_mutation_gate, retry_after_gate, rate_limit_gate, and multi_stage_gate.
## Phase 3.12 model-to-action replay

- source_run_id: `run-20260630-183000-phase3-12-model-flywheel`
- evidence: `datasets/captcha_flywheel/failures/run-20260630-183000-phase3-12-model-flywheel/failure_replay.json`
- evals: `evals/phase3-12/`
- Convert model outputs to scoped actions only after blackbox/leakage/anti-solver gates pass.
- Required action replay fields: before_success_rate, after_success_rate, delta, threshold_met, failure_remaining, and promotion_decision.
- Keep failing families as training_needed or negative_eval_only; do not hide failures with aggregate PASS.
