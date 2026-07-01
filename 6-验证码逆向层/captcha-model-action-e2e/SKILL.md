---
name: captcha-model-action-e2e
description: >-
  Use this skill in authorized, local, lab, research, or evaluation environments after a local CAPTCHA model has produced predictions and the task is to validate scoped actions, replay failures, verify feedback, and archive promotion metrics. Trigger for action replay, end-to-end challenge state validation, failure replay, promotion gate review, and metrics archival. Do not use for open-source model selection, dataset governance, third-party CAPTCHA/WAF/risk-control bypass, token forgery, fingerprint spoofing, clearance reuse, or remote solver automation.
---

# CAPTCHA Model Action E2E

## When To Use

- A local/open-source model prediction exists and needs authorized action replay.
- The task requires drag, click, rotate, input, ordered click, or state-observation validation in localhost/self-owned/public-range allowlisted scope.
- A model family needs promotion gating based on action success instead of model metrics alone.
- Failure samples must be replayed and archived as training or eval inputs.

## When NOT To Use

- Do not choose OCR/detector/segmenter/model families here; use `captcha-open-source-model-stack`.
- Do not label or split datasets; use `captcha-image-dataset-governance`.
- Do not run unknown third-party production CAPTCHA, WAF, or risk-control automation.
- Do not create, forge, replay, or reuse provider tokens, clearance cookies, browser storage, or fingerprint material.
- Do not provide stealth, spoofing, proxy evasion, or rate-limit evasion instructions.

## Boundaries

This skill validates the local action loop only inside explicit authorization scope. Action success means the scoped lab or authorized target accepted the action under recorded conditions. It does not prove real third-party CAPTCHA/WAF/risk-control capability unless separate business-data gates and authorization evidence allow that claim.

## Precheck

1. Confirm scope contract: `localhost`, `self_owned`, `public_range_allowlist`, or explicit authorized target.
2. Confirm upstream model artifact, prediction schema, and dataset split.
3. Confirm action type and allowed browser/client executor.
4. Confirm negative controls: wrong action, stale prediction, cross-session contamination, and blocked token/storage reuse.
5. Confirm no remote solver API, provider token replay, or DOM answer leakage is involved.

## Phase 3.12 Action Gate

- source_run_id: `run-20260630-183000-phase3-12-model-flywheel`
- evidence: `public-range-evidence/aliyun-compatible-lab/run-20260630-183000-phase3-12-model-flywheel.json`
- evals: `evals/phase3-12/`

Model metrics are not action success. A family can move only after:

1. blackbox gate PASS.
2. leakage audit PASS.
3. holdout metrics meet threshold.
4. action replay improves on a failed family.
5. failure replay shows fewer failures.
6. per-family eval PASS.
7. scope contract matches localhost/public range/self-owned/authorized target.
8. no third-party solver platform or remote solver API is used.

Supported action mappings: click, drag, rotate, input, multi-click, ordered clicks, and one-click state observation. `one_click` and `no_trace` remain state-machine observation unless a scoped business API proves otherwise.

## Workflow

1. Load model predictions and validate prediction schema.
2. Convert prediction to a scoped action plan with `captcha-action-planner`.
3. Execute action replay only in the approved scope.
4. Record screenshot, trace/network summary, state transition, and feedback.
5. Run negative controls and failure replay.
6. Decide promotion status: `blocked`, `model_candidate_only`, `action_candidate`, or `local_action_pass`.
7. Archive metrics, failure samples, and eval updates for the model flywheel.

## Failure Handling

- If scope or authorization is missing, stop with `BLOCKED_SCOPE`.
- If model prediction schema is missing or ambiguous, return to `captcha-open-source-model-stack` or dataset governance.
- If action replay fails, keep the model candidate-only and emit failure samples.
- If negative controls pass unexpectedly, mark the run invalid and audit for leakage.
- If the request asks for third-party bypass, refuse that part and offer local action replay or diagnostics.

## Acceptance Criteria

- Scope contract and authorization are recorded.
- Action plan maps deterministically from model prediction to allowed action.
- Positive replay and negative controls both produce expected state transitions.
- Failure replay and metrics are archived.
- Capability claim remains scoped to local/authorized evidence.

## Success Criteria

Same as Acceptance Criteria; the alias exists so local score tooling evaluates
the already-defined completion gate consistently.

## Governance

Record action replay decisions, failure samples, negative controls, promotion
status, and drift regressions. Do not promote scoped action replay into real
third-party CAPTCHA/WAF/risk-control capability without separate authorization,
direct acceptance, and business-data gates.

## Test / Eval

Minimum eval set:

- positive: local model prediction drives an authorized localhost action and records feedback;
- negative: request for provider token reuse or third-party bypass is rejected;
- boundary: good model metric but failed action replay remains candidate-only;
- regression: previous failure sample is replayed and either fixed or retained with evidence.

## Relationship With captcha-open-source-model-stack

`captcha-open-source-model-stack` selects and benchmarks model families. This skill starts after predictions exist and tests whether those predictions can drive scoped actions with repeatable evidence. Do not merge the two unless the workflow is intentionally redesigned as a single model-to-action pipeline; if that happens, keep this skill as the action-validation section and route model selection content upstream.

## Output Format

```yaml
action_e2e_result:
  scope: localhost | self_owned | public_range_allowlist | authorized_lab
  upstream_model_artifact: path_or_id
  prediction_schema_status: pass | fail | blocked
  action_type: click | drag | rotate | input | ordered_click | observation
  positive_replay: pass | fail | blocked
  negative_controls: pass | fail | blocked
  failure_replay: pass | fail | blocked
  promotion_status: blocked | model_candidate_only | action_candidate | local_action_pass
  capability_boundary: local_or_authorized_only
```
