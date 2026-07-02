---
name: captcha-algorithm-benchmark
description: Benchmark CAPTCHA recognition algorithms with class-specific metrics for text, slider, rotate, click, icon-match, multi-image, and action replay without overstating business capability.
triggers: [captcha-benchmark, per-family-metrics, leakage-audit, capability-decision]
license: MIT
platforms: [cross-platform]
category: captcha
version: 0.1.0
---

# CAPTCHA Algorithm Benchmark

Use this skill to score local or authorized CAPTCHA recognition outputs.

## Workflow

Benchmark per family and bucket, then run leakage, blackbox, and promotion gates before writing capability decisions.

## Success Criteria

Each benchmark result must include sample count, success count, success rate, p95 error, failure cases, and baseline comparison where applicable.

## Boundaries

This skill is not responsible for claiming production CAPTCHA/WAF success from synthetic, localhost, or compatible-lab metrics.

## Governance

Write known failures, eval backlog, run_id, and drift notes. Any answer leakage invalidates the benchmark.

## Change Log

- 2026-06-30: Added Phase 3.9 per-family compatible-lab benchmark boundary from `run-20260630-113000-phase3-9-vendor-shield-range`.

## Metrics

- text: `char_accuracy`, `sequence_accuracy`
- slider: `mean_abs_offset_error`, `pass_rate_within_3px`, `pass_rate_within_5px`
- rotate: `mean_abs_angle_error`, `pass_rate_within_3deg`, `pass_rate_within_5deg`
- click: `target_precision`, `target_recall`, `click_distance_mean`, `click_success_rate`
- icon-match: `top1_accuracy`, `confusion_matrix`
- multi-image-select: `precision`, `recall`, `f1`
- action replay: `action_success_rate`, `state_transition_success_rate`, `backend_acceptance_rate`

## Capability Boundary

Benchmark metrics are algorithm evidence, not proof of real-site business success. Keep `business_data_status=NOT_RUN` unless the same run verifies final business data against a server ledger.

## Failure Feedback

Every benchmark with failures must write failure cases and an experience card before updating any SKILL rule.

## Phase 3.1 Benchmark Rules

- Report per-type metrics and per-difficulty metrics.
- Retain per-sample predictions.
- Retain failure cases and error buckets or confusion summaries.
- Include `leakage_check`.
- Include regression thresholds.
- Include previous-run comparison when a prior run exists.
- Metrics below threshold cannot be promoted to positive capability.

Difficulty tiers must include at least easy, medium, and hard. Adversarial samples can be smaller in the first hardening run but must be represented when available.

## Phase 3.5 Longrun Feedback

- Source run_id: `run-20260630-041500-phase3-5-longrun`.
- Failure evidence: `public-range-evidence/longrun/phase3-5/run-20260630-041500-phase3-5-longrun/failure-cases.json`.
- Rule added: benchmark output must include per-type metrics, per-difficulty metrics, per-sample predictions, failure cases, leakage check, and threshold report for longrun acceptance.
- Eval added: `evals/longrun/phase3-5/002-phase3-5-longrun-regression.yaml`.
- Capability impact: metrics below threshold create training targets and cannot be converted into `positive_allowed`.

## Phase 3.6 Model Benchmark Feedback

- Source run_id: `run-20260630-053000-phase3-6-public-model`.
- Metrics: `public-range-evidence/raw/captcha-vision-lab/run-20260630-053000-phase3-6-public-model/benchmark-metrics.json`.
- Rule added: trained model benchmarks must report previous baseline comparison and per-difficulty buckets for text, slider, click, and multi-image when present.
- Eval added: `evals/phase3-6/001-model-training-improves-text-ocr.yaml`.
- Capability impact: text OCR improvement is a real local solver improvement; slider remains training-needed for medium/hard/adversarial.
## Phase 3.12 benchmark boundary

- source_run_id: `run-20260630-183000-phase3-12-model-flywheel`
- evidence: `datasets/captcha_flywheel/models/run-20260630-183000-phase3-12-model-flywheel/`
- evals: `evals/phase3-12/`
- Benchmark metrics must include baseline vs trained, delta, holdout metrics, failure_before, failure_after, action_replay_before, and action_replay_after.
- Benchmark PASS cannot promote a family unless action replay improves and blackbox/leakage/anti-solver/scope gates pass.
