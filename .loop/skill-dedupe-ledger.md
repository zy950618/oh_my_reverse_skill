# Skill Dedupe Ledger

## website-314-api-delivery
Skill: website-314-api-delivery
Current status: active
Role: 完整 Web/API 交付入口
Trigger: new site/pure API/FastAPI/314 optional
Overlaps with: reverse-js-crawler
Decision: Keep external_entry.
Required changes: No change.
Validation: structure/routing gates.
Score impact: none

## reverse-js-crawler
Skill: reverse-js-crawler
Current status: active
Role: 单链路 JS/接口逆向入口
Trigger: JS reverse/API restoration/sign/token/crawler
Overlaps with: website-314-api-delivery
Decision: Keep external_entry, scoped below full delivery.
Required changes: No change.
Validation: structure/routing gates.
Score impact: none

## web-h5-loop-engineering
Skill: web-h5-loop-engineering
Current status: active
Role: Loop/Governance execution入口
Trigger: LOOP/closed loop/multi-agent/repeated validation
Overlaps with: skills-evaluation-governance
Decision: Keep external_entry for execution loop only.
Required changes: No change.
Validation: structure/routing gates.
Score impact: none

## skills-evaluation-governance
Skill: skills-evaluation-governance
Current status: active
Role: 评分/回测/准入治理入口
Trigger: Skill Bench/scoring/evals/backtest
Overlaps with: web-h5-loop-engineering
Decision: Keep external_entry for skill governance only.
Required changes: Added standard_type.
Validation: structure/routing gates.
Score impact: none

## imperva-waf-reese84
Skill: imperva-waf-reese84
Current status: conditional_escalation
Role: Imperva/Reese84 evidence escalation
Trigger: Reese84/Incapsula/x-d-token evidence
Overlaps with: fingerprint diagnostics
Decision: Keep conditional, not generic fingerprint owner.
Required changes: Added standard_type; triggers already split.
Validation: routing gate.
Score impact: none

## authorized-target-adapter
Skill: authorized-target-adapter
Current status: conditional_escalation
Role: 授权边界/scope adapter
Trigger: authorized target/scope/business data assertions
Overlaps with: website delivery
Decision: Keep conditional.
Required changes: Added standard_type.
Validation: structure gate.
Score impact: none

## site-api-adapter
Skill: site-api-adapter
Current status: conditional_escalation
Role: 稳定接口沉淀 adapter
Trigger: adapter/schema/runbook after stable API
Overlaps with: website delivery
Decision: Keep conditional.
Required changes: No change.
Validation: structure gate.
Score impact: none

## browser-fingerprint-surface-lab
Skill: browser-fingerprint-surface-lab
Current status: conditional_escalation
Role: fingerprint surface observation lab
Trigger: fingerprint surface/profile consistency
Overlaps with: block reason diagnostics
Decision: Keep conditional observation/lab.
Required changes: Added standard_type; forbidden wording replaced.
Validation: structure/routing gates.
Score impact: none

## fingerprint-block-reason-diagnostics
Skill: fingerprint-block-reason-diagnostics
Current status: conditional_escalation
Role: block reason attribution
Trigger: fingerprint block reason/risk diagnostics
Overlaps with: surface lab
Decision: Keep conditional attribution.
Required changes: Added standard_type; forbidden wording replaced.
Validation: structure/routing gates.
Score impact: none

## find-crypto-entry
Skill: find-crypto-entry
Current status: internal_tool
Role: atomic crypto entry locator
Trigger: find sign/x-sign/token source
Overlaps with: reverse-js-crawler
Decision: Keep internal_tool.
Required changes: Added standard_type.
Validation: structure/routing gates.
Score impact: none

## ast-deobfuscate
Skill: ast-deobfuscate
Current status: internal_tool
Role: AST deobfuscation tool
Trigger: deobfuscate/string array/control flow
Overlaps with: env-patch
Decision: Keep internal_tool.
Required changes: Added standard_type.
Validation: structure/routing gates.
Score impact: none

## env-patch
Skill: env-patch
Current status: internal_tool
Role: Node env patch for known module
Trigger: env patch/run browser JS in Node
Overlaps with: runtime parity
Decision: Keep internal_tool.
Required changes: Added standard_type.
Validation: structure/routing gates.
Score impact: none

## js-page-runtime-parity
Skill: js-page-runtime-parity
Current status: internal_tool
Role: Browser/Node/V8/PageRuntime parity
Trigger: runtime parity/ruoyiPage
Overlaps with: env-patch/fingerprint lab
Decision: Keep internal_tool.
Required changes: Added standard_type; forbidden wording replaced.
Validation: structure/routing gates.
Score impact: none

## ai-reverse-skill-creator
Skill: ai-reverse-skill-creator
Current status: internal_tool
Role: skill creation support
Trigger: create/update skill resources
Overlaps with: skills governance
Decision: Keep internal_tool.
Required changes: Added standard_type.
Validation: structure/routing gates.
Score impact: none

## karpathy-guidelines
Skill: karpathy-guidelines
Current status: auxiliary_policy
Role: engineering discipline checklist
Trigger: coding/review/refactor support
Overlaps with: all implementation skills
Decision: Keep auxiliary_policy only.
Required changes: Forbidden wording replaced.
Validation: structure/routing gates.
Score impact: none
