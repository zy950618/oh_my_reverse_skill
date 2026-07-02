---
name: captcha-model-training
description: Train and harden local or authorized CAPTCHA recognition models from labeled datasets, long-run failure cases, regression evals, and capability-boundary evidence without claiming real-site CAPTCHA/WAF success.
triggers: [captcha-training, dataset-split, checkpoint, leakage-audit, model-registry]
license: MIT
platforms: [cross-platform]
category: captcha
version: 0.1.0
---

# CAPTCHA Model Training

Use this skill only for synthetic, localhost, public-lab, owned, or explicitly authorized CAPTCHA datasets.

## Workflow

Use `tools/captcha_leakage_audit.py` before training and keep train/val/test split, checkpoint, metrics, failure samples, and model registry entries together for each run.

## Success Criteria

A model-training claim requires dataset manifest, split manifest, model config, checkpoint path, validation/test metrics, baseline comparison, and failure samples before/after.

## Boundaries

This skill is not responsible for bypassing third-party CAPTCHA/WAF or claiming production success from synthetic/local compatible labs.

## Governance

Write run_id, known failures, eval backlog, and drift notes. Any leakage audit failure invalidates the run and blocks promotion.

## Change Log

- 2026-06-30: Added Phase 3.9 training-boundary linkage to compatible-lab evidence from `run-20260630-113000-phase3-9-vendor-shield-range`.

## Phase 3.10 Realism Hardening Rule

- Source run_id: `run-20260630-163000-phase3-10-realism-hardening`.
- Evidence: `public-range-evidence/raw/challenge-realism-audit/run-20260630-163000-phase3-10-realism-hardening/challenge-realism-audit.json`.
- Scope: local compatible lab failure feedback only unless self-owned official trial config exists.
- Capability level: hard/adversarial compatible lab rows are training data candidates, not verified model capability.
- Boundary: do not train on official demo answers, DOM answers, query expected fields, or server hidden answers.
- Failure cases: use `failure-cases.json` from Shumei/Aliyun compatible labs as the next model backlog.
- Eval: `evals/phase3-10/shumei-compatible-lab-hardening.yaml` and `evals/phase3-10/aliyun-compatible-lab-hardening.yaml`.
- Next training goal: produce checkpoint, train/val/test split, baseline comparison, and before/after failure replay.

## Required Inputs

- dataset manifest with challenge type, difficulty, seed, and label source
- per-sample predictions
- failure cases grouped by root cause
- leakage check result
- regression thresholds
- source run id

## Phase 3.5 Longrun Rule

- Source run_id: `run-20260630-041500-phase3-5-longrun`.
- Failure evidence: `public-range-evidence/longrun/phase3-5/run-20260630-041500-phase3-5-longrun/failure-cases.json`.
- Issue ledger: `public-range-evidence/longrun/phase3-5/run-20260630-041500-phase3-5-longrun/issue-ledger.json`.
- Rule added: model-training work must start from failed longrun samples and retest through `tools/captcha_vision_benchmark.py --run-id <run_id> --require-threshold-report`.
- Eval added: `evals/longrun/phase3-5/001-phase3-5-longrun-regression.yaml`.
- Capability boundary: training success remains `memory_only` until final business API and `business_data_assertions` pass for an authorized target.

## Prohibited

- Do not use DOM labels, answer metadata, query parameters, or human-solved tokens as prediction inputs.
- Do not claim third-party CAPTCHA/WAF capability from synthetic or localhost metrics.
- Do not promote a failed benchmark into a positive SKILL rule.

## Phase 3.9 Vendor-Compatible Training Boundary

- Source run_id: `run-20260630-113000-phase3-9-vendor-shield-range`.
- Evidence: `public-range-evidence/shumei-compatible-lab/run-20260630-113000-phase3-9-vendor-shield-range.json` and `public-range-evidence/aliyun-compatible-lab/run-20260630-113000-phase3-9-vendor-shield-range.json`.
- Evals: `evals/phase3-9/shumei-compatible-lab-compatible-lab.yaml`, `evals/phase3-9/aliyun-compatible-lab-compatible-lab.yaml`.
- Vendor-compatible datasets can improve local algorithms only when leakage audit and blackbox gate pass.
- Do not write compatible-lab metrics as Shumei/Aliyun production capability. Official vendor positive requires official demo permission, self-owned trial, or authorized integration evidence.

## Phase 3.6 Training Feedback

- Source run_id: `run-20260630-053000-phase3-6-public-model`.
- Model checkpoint: `public-range-evidence/raw/captcha-model-training/run-20260630-053000-phase3-6-public-model/checkpoints/text-ocr-centroid.json`.
- Failure evidence: `public-range-evidence/raw/captcha-model-training/run-20260630-053000-phase3-6-public-model/failure-before-after.json`.
- Rule added: a training run is not accepted unless it emits train/val/test split, model config, checkpoint, training log, val/test metrics, baseline comparison, failure before/after, and model registry entry.
- Eval added: `evals/phase3-6/001-model-training-improves-text-ocr.yaml`.
- Capability impact: local text OCR improved versus baseline, but public evidence remains non-positive without final business API data assertions.

## Phase 3.6.1 Scope-Limited Candidate Rule

- Source run_id: `run-20260630-071500-phase3-6-1-candidate`.
- Action replay evidence: `public-range-evidence/local-gocaptcha-compatible-lab/run-20260630-071500-phase3-6-1-candidate.json`.
- Leakage evidence: `public-range-evidence/raw/captcha-leakage-audit/run-20260630-071500-phase3-6-1-candidate/leakage-audit.json`.
- Blackbox evidence: `public-range-evidence/raw/captcha-blackbox-gate/run-20260630-071500-phase3-6-1-candidate/blackbox-gate.json`.
- Failure evidence: `public-range-evidence/raw/local-gocaptcha-compatible-lab/run-20260630-071500-phase3-6-1-candidate/gocaptcha-action-replay-failure-cases.json`.
- Rule added: CAPTCHA terms are not downgrade triggers by themselves inside `configs/range_scope_contract.yaml`; promotion is allowed only as `positive_candidate`, `positive_verified`, or `stable_positive` when target, host, allowed_mode, leakage audit, blackbox gate, action replay, eval, and failure feedback all pass.
- Eval added: `evals/phase3-6/002-gocaptcha-local-action-replay.yaml`.
- Capability impact: the current target is a self-owned compatible lab, not a real GoCaptcha component. Single-run evidence can only become `positive_candidate`; multi-seed/multi-round threshold PASS is required for `positive_verified`, and longrun stability is required for `stable_positive`.
## Phase 3.12 model-based training gate

- source_run_id: `run-20260630-183000-phase3-12-model-flywheel`
- evidence: `datasets/captcha_flywheel/models/run-20260630-183000-phase3-12-model-flywheel/model_registry.json`
- evals: `evals/phase3-12/`
- Training routes must cover YOLO/detection, OCR, open-vocabulary detection, segmentation-assisted refinement, model registry, dataset versioning, failure replay, and model promotion gate.
- A model checkpoint can be local/open-source only. It must record `external_api_used=false`, `third_party_solver_used=false`, and `label_leakage=false`.
- Model metrics never equal action success. Promotion requires holdout metrics, blackbox gate, leakage audit, action replay threshold, failure replay improvement, per-family eval, scope contract, and no third-party site generalization.
