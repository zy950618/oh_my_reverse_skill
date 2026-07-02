---
name: js-page-runtime-parity
description: Extract page-level JavaScript runtime dependencies and verify Browser, Node, V8, and PageRuntime output parity for authorized targets or localhost labs without generating risk tokens or bypass behavior.
license: MIT
platforms: [cross-platform]
category: js-reverse
version: 0.1.0
---

# JS Page Runtime Parity

`ruoyiPage` / PageRuntime means an internal page-level runtime shim framework for authorized JavaScript reverse engineering.

It is for:

- Browser, Node, V8, and PageRuntime output parity.
- BOM/DOM/Web API dependency mapping.
- Missing API detection.
- Environment contract generation.
- Signature fixture regression.

It is not:

- an unauthorized bypass tool
- a token forgery tool
- a WAF bypass tool
- a webdriver hiding tool
- a fingerprint spoofing tool

## Required Outputs

- `runtime_dependency_map`
- `runtime_parity_report`
- `environment_contract`
- `runtime_diff_report`
- `regression_fixture`

Canvas, WebGL, AudioContext, WebRTC, Permissions, and client hints are observation-only. Do not add spoofing rules.

## Phase 3.5 Longrun Feedback

- Source run_id: `run-20260630-041500-phase3-5-longrun`.
- Failure evidence: `public-range-evidence/longrun/phase3-5/run-20260630-041500-phase3-5-longrun/issue-ledger.json`.
- Rule added: longrun parity must compare Browser, Node, and PageRuntime outputs repeatedly and write an environment contract plus regression fixture.
- Eval added: `evals/longrun/phase3-5/004-phase3-5-longrun-regression.yaml`.
- Capability impact: localhost JS parity is reproducibility evidence, not token forgery, WAF bypass, or third-party risk-control success.

## Phase 3.8 Runtime Parity Boundary

- Source run_id: `run-20260630-101500-phase3-8-family-hardening`.
- Evidence: `public-range-evidence/raw/capability-promotion-gate/run-20260630-101500-phase3-8-family-hardening/capability-promotion-decision.json`.
- Evals: `evals/phase3-8/008-js-runtime-parity-boundary.yaml`.
- Browser/Node/PageRuntime parity can support authorized replay only when mutation inputs, missing API contracts, and regression fixtures pass.
- JS runtime parity is not real-site token forgery, risk-token capability, fingerprint evasion, or production WAF bypass. Unknown third-party and production_unverified scopes remain observation_only.

## Phase 3.9 Five-Second Shield Route

- Source run_id: `run-20260630-113000-phase3-9-vendor-shield-range`.
- Evidence: `public-range-evidence/five-second-shield-lab/run-20260630-113000-phase3-9-vendor-shield-range.json`.
- Eval: `evals/phase3-9/five-second-shield-lab.yaml`.
- For five-second shield / WAF / JS challenge, first classify scope. Unknown third-party and production-unverified targets are observation-only.
- Local, self-owned, or authorized targets may run challenge parity only when redirect chain, challenge script, cookie write, `expires_at`, business endpoint, Browser/Node/PageRuntime parity, and failure ledger are recorded.
- Do not reuse real-site clearance. Do not treat challenge endpoint success as business success. Final acceptance must be business API plus business ledger.

## Phase 3.10 Dynamic Shield Runtime Rule

- Source run_id: `run-20260630-163000-phase3-10-realism-hardening`.
- Evidence: `public-range-evidence/five-second-shield-lab/run-20260630-163000-phase3-10-realism-hardening.json`.
- Scope: `localhost_waf_lab`; real websites require `self_owned_trial` or `authorized_target`.
- Capability level: local runtime parity supports `positive_candidate` only for the local shield lab.
- Boundary: not production WAF bypass, not risk-token forgery, not fingerprint evasion.
- Failure cases: stale nonce, wrong signature, delay window, reused clearance, JS runtime mismatch, browser-only success not direct repeat.
- Eval: `evals/phase3-10/five-second-shield-lab-dynamic.yaml`.
- Next training goal: repeat dynamic JS parity under soak and mutation regression before verified/stable promotion.
## Phase 3.11 dynamic shield JS parity

- source_run_id: `run-20260630-173000-phase3-11-type-matrix`
- evidence: `public-range-evidence/five-second-shield-lab/run-20260630-173000-phase3-11-type-matrix.json`
- evals: `evals/phase3-11/five-second-shield-profile-matrix.yaml`
- Browser, Node, and PageRuntime parity must be repeated on mutation inputs that bind sid, nonce, ua_hash, script_hash, mutation, and action.
- JS challenge verify success is not enough; the final business API and server ledger assertion must pass before runtime parity can support any candidate decision.
## Phase 3.12 model flywheel JS boundary

- source_run_id: `run-20260630-183000-phase3-12-model-flywheel`
- evidence: `public-range-evidence/raw/anti-solver-platform-audit/run-20260630-183000-phase3-12-model-flywheel/anti-solver-platform-audit.json`
- evals: `evals/phase3-12/`
- JS/runtime evidence must not use copied browser tokens, copied clearance cookies, remote solver APIs, or provider internal tokens as model or replay inputs.
