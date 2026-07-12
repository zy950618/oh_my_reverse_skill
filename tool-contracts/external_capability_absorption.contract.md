## Purpose
Define the internal clean-room absorption contract for capability categories observed in public external sources. This contract maps patterns into existing base assets only; it does not import external repository code, templates, prompts, tests, examples, or active skills.

## Scope
- Source facts are limited to page-level observations with explicit source identity and license status.
- Outputs are limited to existing internal Skills, tool contracts, governance evals, and stable governance rules.
- Capability claim is `STRUCTURE_ONLY` until fresh internal execution evidence proves more.
- Risk-sensitive markers are observation, lab, or evidence-contract only.

## Internal Base Attachment Rule
Every absorbed pattern must attach to all of the following:
- existing internal base asset: Skill, tool contract, eval, or governance rule
- evidence level: `observed`, `derived`, `assumed`, or `unverified`
- absorption mode: `reference_only`, `clean_room_summary`, `eval_seed_without_verbatim_copy`, `tool_contract_mapping`, or `lab_or_evidence_contract_observation_only`
- prohibited conversion: no implementation import, no prompt/template import, no active Skill creation, no manifest edit, no production claim
- validation requirement: structure validator, eval seed, current product gate, or human review boundary
- remaining gap before any stronger capability claim

## Capability Pattern Mapping

| External observed category | Target internal base asset | Absorption mode | Evidence level | Prohibited conversion | Validation required |
|---|---|---|---|---|---|
| Intake, routing, evidence, and scope governance | `99-SKILLS治理/*`, `1-业务流程层/skills-evaluation-governance`, `tool-contracts/external_clean_room_fusion.contract.md` | `tool_contract_mapping` + `eval_seed_without_verbatim_copy` | derived from recorded source facts | external prompt or workflow import; active Skill creation | governance evals and current structure/routing gates |
| JS runtime trace, script manifest, hash, and freshness | `tool-contracts/collect_scripts.contract.md`, `tool-contracts/extract_runtime_trace.contract.md`, `tool-contracts/fixture_freshness_check.contract.md` | `clean_room_summary` | derived from recorded source facts | copied debugging code or external scripts | script hash/freshness evidence before runtime claims |
| Crypto entry, call chain, and input-output evidence | `tool-contracts/search_crypto_entry.contract.md`, `tool-contracts/replay_request.contract.md` | `lab_or_evidence_contract_observation_only` | derived; no production success | sign/token/cookie success claim or production replay claim | input-output evidence contract and negative boundary eval |
| Environment patch and browser-node parity boundary | `tool-contracts/compare_browser_vs_node.contract.md`, `2-JS逆向工具层/env-patch/references/governance.md` | `tool_contract_mapping` | derived | concealment, falsification, or parity success claim without evidence | browser-node parity evidence and failure split |
| Hook tracing as observation evidence | `tool-contracts/extract_runtime_trace.contract.md`, `99-SKILLS治理/18-证据验证拒答人工复核与监控规约.md` | `lab_or_evidence_contract_observation_only` | observed as marker; operational details unverified | hook-based defeat workflow or stealth instruction | human review boundary and observation-only evidence |
| Eval, onboarding, and negative boundary seeds | `1-业务流程层/skills-evaluation-governance/evals` | `eval_seed_without_verbatim_copy` | derived | copied external tests/examples or active Skill onboarding | evals must fail unsafe conversions |
| Foundation/base handling | existing internal Skill/tool-contract/eval/governance rule named in each row | `tool_contract_mapping` | derived | unattached abstract capability or production capability claim | every row names base asset, evidence level, prohibited conversion, validator, and gap |

## Source Policy Matrix

| Source observation | License status | Allowed handling | Prohibited conversion | Remaining gap |
|---|---|---|---|---|
| `jshook-skill` public page and risk-sensitive feature inventory | GPL-3.0 observed | `reference_only`, negative eval seeds, observation/lab evidence contracts | implementation import, copied hook code, concealment/falsification workflow, active Skill | raw source and implementation details are not imported |
| `hello_js_reverse_skill` public page and feature inventory | unknown | `reference_only` | clean-room summary before license verification; code/template/prompt import; operational upgrade | license and full contents remain unverified |
| `ai-reverse-toolkit` public page and category inventory | MIT observed | `clean_room_summary`, negative eval seeds, internal contract mapping | copied source/templates/examples; real-site or production sign/token claim | only category-level patterns are retained |

## Required Evidence
- source identity and page-level fact reference
- license decision
- prohibited-use scan and allowed handling mode
- internal base asset receiving the pattern
- evidence level and limitation
- explicit no-import statement
- current validation command or human review boundary
- remaining gap

## Failure Modes
- External repository code, templates, prompts, tests, or examples appear in repository assets.
- `skills-manifest.json` is edited or an active Skill is created from external material.
- A risk-sensitive marker becomes operational capability, a production workflow, or a success claim.
- An absorbed pattern lacks a named internal base asset, evidence level, validation path, or remaining gap.
- Unknown-license material is summarized beyond reference-only handling.

## Acceptance Checks
- Absorption lands only in durable internal contracts, evals, or governance rules.
- Every pattern is attached to an existing internal base asset.
- Evidence levels and remaining gaps are explicit.
- No external raw file is fetched, cloned, copied, or imported as part of absorption.
- No real-site, sign/token, challenge-defeat, concurrency, or production capability is claimed without fresh internal evidence.
