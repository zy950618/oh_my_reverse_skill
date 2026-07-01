---
name: captcha-open-source-model-stack
description: >-
  Use this skill only in authorized, local, lab, research, or evaluation environments to select and evaluate local/open-source model families for CAPTCHA OCR, detection, segmentation, embedding matching, and model training. Trigger for model-stack selection, dataset-to-model routing, OCR/detector/segmenter comparison, holdout benchmark planning, and open-source model governance. Do not use for third-party CAPTCHA/WAF/risk-control bypass, token generation, fingerprint spoofing, clearance reuse, remote solver APIs, or action replay validation; route action replay and promotion gates to captcha-model-action-e2e.
---

# CAPTCHA Open-Source Model Stack

## When To Use

Use this skill when the task is about the model stack before action execution:

- choosing OCR, detector, segmenter, embedding, or classifier families for an authorized CAPTCHA lab;
- mapping dataset labels, challenge families, and failure samples to training candidates;
- comparing local/open-source baselines against holdout metrics;
- deciding whether a model family is ready for downstream action replay by `captcha-model-action-e2e`;
- writing local evaluation notes, model registry entries, and benchmark requirements.

## When NOT To Use

- Do not use this skill to operate against unknown or unauthorized third-party CAPTCHA, WAF, or risk-control systems.
- Do not use it to generate or reuse provider tokens, clearance cookies, browser storage, or fingerprint material.
- Do not use it for webdriver hiding, fingerprint spoofing, proxy rotation, rate-limit evasion, or detection avoidance.
- Do not use it to validate user actions, drag/click replay, or end-to-end challenge state transitions; route those to `captcha-model-action-e2e` or `captcha-action-planner`.
- Do not treat local benchmark metrics as proof of third-party CAPTCHA solving capability.

## Precheck

Before selecting a model stack, record:

1. authorization scope: `localhost`, `self_owned`, `public_range_allowlist`, or another explicit approved scope;
2. dataset provenance, label source, split policy, and leakage audit status;
3. challenge family: text/OCR, slide/gap, rotate, click/select, sequence, spatial, or multi-image;
4. target output type: text, box, mask, angle, embedding match, class, or structured action candidate;
5. forbidden capabilities that must remain out of scope.

## Phase 3.12 Model Routes

- source_run_id: `run-20260630-183000-phase3-12-model-flywheel`
- evidence: `datasets/captcha_flywheel/models/run-20260630-183000-phase3-12-model-flywheel/model_registry.json`
- gate evidence: `public-range-evidence/raw/captcha-blackbox-gate/run-20260630-183000-phase3-12-model-flywheel/blackbox-gate.json`
- evals: `evals/phase3-12/`

Use local or open-source models only:

- text/OCR: PaddleOCR or PP-OCRv5, CRNN+CTC, CNN/transformer decoder, OpenCV preprocessing baseline.
- slide/puzzle/gap: OpenCV edge/template baseline, YOLO gap/block detector, segmentation mask refinement, contour/keypoint matching, Siamese/image matching.
- rotate: angle classification/regression, feature correlation, upright semantic cues, self-supervised rotation prediction.
- click/text/icon select: YOLO detection, OCR text detection/recognition, GroundingDINO open vocabulary detection, CLIP/DINOv2 embedding matching, SAM/SAM2 refinement.
- seq_select: OCR, language order parser, target matching, ordered action planner.
- spatial_select: instruction parser, object detection, spatial relation parser, geometric reasoning.
- multi-image-select: classifier, CLIP/DINOv2 embedding, YOLO for object-level targets, hard negative mining.

Do not use paid solver services, copied browser tokens, provider internal tokens, DOM answers, query expected answers, or remote solver APIs.

## Workflow

1. Classify the challenge family and expected model output.
2. Check dataset governance with `captcha-image-dataset-governance`: provenance, split, labels, hard negatives, and leakage audit.
3. Select the smallest local/open-source baseline that can produce the required output.
4. Define benchmark metrics and thresholds with `captcha-algorithm-benchmark`.
5. Record model candidates in the model registry with version, dataset split, feature inputs, and failure categories.
6. Pass only scoped model artifacts, metrics, and failure samples to `captcha-model-action-e2e` for action replay validation.

## Safety Boundary

This skill is limited to authorized, local, lab, research, and evaluation environments. It may describe model families and offline metrics, but it must not provide instructions for bypassing real third-party CAPTCHA, WAF, or risk-control systems. It must not promote token forgery, fingerprint spoofing, stealth automation, remote solver use, clearance reuse, or rate-limit evasion.

## Failure Handling

- If authorization or dataset provenance is missing, stop and mark the result `BLOCKED_AUTHORIZATION_OR_PROVENANCE`.
- If leakage audit fails, do not score the model as usable; record the failed split and route to dataset governance.
- If holdout metrics pass but action replay fails, keep the model as `model_candidate_only` and route failure samples to `captcha-model-action-e2e`.
- If the task asks for third-party bypass or evasion, refuse that part and offer local benchmark or diagnostic alternatives.

## Acceptance Criteria

- Authorization scope and dataset provenance are recorded.
- Model family choice is tied to challenge family and output type.
- Benchmark metric, threshold, split, and failure category are explicit.
- No claim is made about real third-party CAPTCHA/WAF/risk-control success.
- Downstream action validation is delegated to `captcha-model-action-e2e` with clear inputs.

## Success Criteria

Same as Acceptance Criteria; this explicit heading keeps local scoring aligned
with the unified rubric while preserving the existing model-selection workflow.

## Governance

Record model registry changes, benchmark failures, leakage audit results, and
downstream action replay requirements. Do not promote local model metrics into
third-party CAPTCHA/WAF/risk-control capability.

## Test / Eval Requirements

Minimum eval set:

- positive: choose a local OCR/detector/segmenter stack for an authorized dataset;
- negative: reject a request for third-party CAPTCHA bypass or remote solver use;
- boundary: dataset labels exist but leakage audit is missing;
- regression: model metrics improve but action replay remains failed, so capability stays candidate-only.

## Output Format

```yaml
model_stack_decision:
  scope: localhost | self_owned | public_range_allowlist | authorized_lab
  challenge_family: text | slide | rotate | click | sequence | spatial | multi_image
  dataset_provenance: observed | derived | assumed | unverified
  selected_models: []
  benchmark_plan: []
  leakage_status: pass | fail | blocked | unverified
  downstream_route: captcha-model-action-e2e
  capability_claim: local_eval_only | model_candidate_only | blocked
  forbidden_capabilities_confirmed: true
```

## Relationship With captcha-model-action-e2e

`captcha-open-source-model-stack` chooses and evaluates local/open-source model families. `captcha-model-action-e2e` validates whether scoped predictions can drive authorized/local actions, replay failures, and pass promotion gates. Keep them separate unless future evidence shows the same operator consistently needs both stages in one atomic workflow. If merged later, keep `captcha-open-source-model-stack` content as the model-selection section and preserve `captcha-model-action-e2e` as the action-validation entry.
