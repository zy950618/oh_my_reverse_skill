---
name: js-page-runtime-parity
standard_type: internal_tool
description: Extract page-level JavaScript runtime dependencies and verify Browser, Node, V8, and PageRuntime output parity for authorized targets or localhost labs without generating risk tokens or defeat behavior.
license: MIT
platforms: [cross-platform]
category: js-reverse
version: 0.1.1
trigger: runtime parity, PageRuntime, Browser Node V8 parity, environment contract
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

- an unauthorized defeat tool
- a token forgery tool
- a WAF defeat tool
- a webdriver concealment tool
- a fingerprint falsification tool

## Required Outputs

- `runtime_dependency_map`
- `runtime_parity_report`
- `environment_contract`
- `runtime_diff_report`
- `regression_fixture`

Canvas, WebGL, AudioContext, WebRTC, Permissions, and client hints are observation-only. Do not add fingerprint-alteration rules.

## Auxiliary Policy

- Engineering discipline follows `4-通用规范层/karpathy-guidelines/SKILL.md`.

## Workflow

1. Confirm the caller skill and authorized scope before use.
2. Execute only the atomic/internal task owned by this skill.
3. Return evidence to the caller skill for final routing and delivery.

## Success Criteria

- The task output is reproducible from the recorded input.
- The caller skill can validate or reject the result without this tool becoming a business entry.

## Boundaries

This skill is not a public business entry and must not claim full-site delivery ownership.

## Governance

Changes require route-boundary validation, eval coverage, and score gate replay.

## Routing Handoff

Use `reverse-js-crawler` or `website-314-api-delivery` as the orchestrator when final business delivery is needed. This tool is not responsible for public entry routing, WAF handling, fingerprint mutation, or full delivery claims.

## Drift And Evidence Writeback

Drift checks cover runtime API changes, environment contract changes, and signature fixture changes. Site memory handoff and known failures must record missing APIs, mismatched outputs, and unsupported scopes.
