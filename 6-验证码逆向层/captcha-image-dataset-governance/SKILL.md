---
name: captcha-image-dataset-governance
description: Govern synthetic and authorized CAPTCHA image datasets, label schemas, splits, redaction, failure-sample feedback, and dataset versioning for local/authorized reverse-engineering labs.
triggers: [captcha-dataset, train-val-test, leakage-audit, failure-samples]
license: MIT
platforms: [cross-platform]
category: captcha
version: 0.1.0
---

# CAPTCHA Image Dataset Governance

Use this skill when a CAPTCHA run creates, labels, splits, imports, redacts, or reuses visual samples.

## Workflow

Keep labels, metadata answers, DOM answers, and query expected fields out of solver input. Maintain dataset manifests and split manifests for each run.

## Success Criteria

Dataset governance passes when input redaction, split separation, failure sample writeback, and leakage audit PASS are recorded.

## Boundaries

This skill is not responsible for production CAPTCHA bypass or using public/official demo answers as labels without explicit authorization.

## Governance

Write known failures, eval backlog, run_id, and drift notes. Any leakage audit failure invalidates dependent solver results.

## Change Log

- 2026-06-30: Added Phase 3.9 compatible-lab dataset boundary from `run-20260630-113000-phase3-9-vendor-shield-range`.

## Allowed Data

- Synthetic samples from local generators.
- Owned-site samples.
- Explicitly authorized test-site samples.
- Official demo samples only as boundary or negative evidence unless final business API assertions exist.

## Required Label Fields

Each sample record must include:

- `image_path`
- `label_path`
- `challenge_type`
- `answer`
- one of `bounding_boxes`, `click_points`, `offset`, or `angle`
- `seed`
- `difficulty`
- `generated_at`

## Dataset Rules

- Keep sample provenance and generation command with the run.
- Keep train/val/test split deterministic when used.
- Do not import unknown third-party production challenge images without authorization.
- Failure samples must be kept with metrics and root-cause notes before they are used to change SKILLS.

## Phase 3.1 Manifest Rules

Each dataset manifest must record per sample:

- `sample_id`
- `challenge_type`
- `difficulty`
- `image_path`
- `label_path`
- `seed`
- `generator_version`
- `transform_pipeline`
- `answer_source`
- train/val/test `split`
- `synthetic`
- `authorized_sample`
- `source_scope`

The benchmark must run a leakage check. If solver output uses label, DOM, query parameter, or metadata answer access, mark the run `invalid_leakage`.
