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

