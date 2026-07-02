# Routing Contract

## Purpose

This contract fixes the entry order for Web/H5 reverse-engineering skills so business delivery, loop orchestration, pure API delivery, CAPTCHA model delivery, and fingerprint risk diagnostics do not compete for the same trigger.

## Standard Skill Types

| type | role | examples |
|---|---|---|
| `external_entry` | user-facing business entry | `website-314-api-delivery`, `reverse-js-crawler`, `web-h5-loop-engineering`, `skills-evaluation-governance` |
| `conditional_escalation` | used only after evidence or explicit user request | `imperva-waf-reese84`, `captcha-service-delivery`, `site-api-adapter` |
| `internal_tool` | atomic helper called by an entry skill | `find-crypto-entry`, `ast-deobfuscate`, `env-patch`, runtime parity tools |
| `auxiliary_policy` | engineering/governance checklist only | `karpathy-guidelines` |
| `captcha_model_delivery` | dataset/training/action/pass-rate/model package delivery | `captcha-service-delivery` model references and validators |
| `fingerprint_risk_delivery` | observation-only risk lab and block reason diagnostics | `browser-fingerprint-surface-lab`, `fingerprint-block-reason-diagnostics` |
| `pure_api_delivery` | browserless final API delivery gate | `website-314-api-delivery`, `reverse-js-crawler`, `site-api-adapter` |
| `lab_delivery` | local self-owned executable lab | `public-range-evidence/pure-api-lab`, `public-range-evidence/airline-lab-order-flow` |
| `real_site_observation` | authorized observation task pack, not a production lab | `public-range-evidence/real-site-observation-pack/*` |

## Priority

1. Explicit LOOP, closed-loop, multi-agent, repeated validation, execution ledger: `web-h5-loop-engineering`.
2. Complete pure-interface/FastAPI/service/314 delivery: `website-314-api-delivery`.
3. Focused single route/stage JS reverse, sign/token, request replay: `reverse-js-crawler`.
4. Skill scoring/governance/eval/drift: `skills-evaluation-governance`.
5. CAPTCHA/WAF/fingerprint/site-adapter only escalate after evidence or explicit user request.

## Hard Delivery Rule

Final business delivery must be pure API: browser use is allowed for analysis only, and final business flow must not depend on Playwright, Puppeteer, Camoufox, copied cookies, browser storage, browser profiles, or manual cookie copy.

## Evidence Labels

Routing decisions must use `observed`, `derived`, `assumed`, or `unverified`. If the repo only has structure and validators, report `STRUCTURE-ONLY` instead of real-site capability.
