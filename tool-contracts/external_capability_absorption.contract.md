## Purpose
Define the internal clean-room absorption contract for external capability categories already recorded in LCL-20260709-08 fact packs and gated by LCL-20260709-09. This contract absorbs capability patterns into existing base assets only; it does not import external repository code, templates, prompts, tests, examples, or active skills.

## Scope
- Source base is limited to repository-local LCL-20260709-08 fact packs and LCL-20260709-09 clean-room fusion rules.
- Output base is limited to existing internal skills, tool contracts, governance evals, execution ledgers, and verification reports.
- Capability claim is `STRUCTURE_ONLY`.
- Risk-sensitive markers are observation, lab, or evidence-contract only.

## Internal Base Attachment Rule
Every absorbed pattern must attach to all of the following:
- existing internal base asset: skill, tool contract, eval, or governance ledger
- evidence level: `observed`, `derived`, `assumed`, or `unverified`
- absorption mode: `reference_only`, `clean_room_summary`, `eval_seed_without_verbatim_copy`, `tool_contract_mapping`, or `lab_or_evidence_contract_observation_only`
- prohibited conversion: no implementation import, no prompt/template import, no active skill creation, no manifest edit, no production claim
- validation requirement: structure validator, eval seed, loop ledger, acceptance report, or human review boundary

## Capability Pattern Mapping

| External observed category | Target internal base asset | Absorption mode | Evidence level | Prohibited conversion | Validation required |
|---|---|---|---|---|---|
| Intake, routing, evidence, and scope governance | `99-SKILLS治理/*`, `1-业务流程层/skills-evaluation-governance`, `tool-contracts/external_clean_room_fusion.contract.md` | `tool_contract_mapping` + `eval_seed_without_verbatim_copy` | derived from local fact packs | external prompt or workflow import; active skill creation | eval 027 plus loop and acceptance validators |
| JS runtime trace, script manifest, hash, and freshness | `tool-contracts/collect_scripts.contract.md`, `tool-contracts/extract_runtime_trace.contract.md`, `tool-contracts/fixture_freshness_check.contract.md` | `clean_room_summary` | derived from local fact packs | copied debugging code or external scripts | script hash/freshness evidence required before runtime claims |
| Crypto entry, call chain, and input-output evidence | `tool-contracts/search_crypto_entry.contract.md`, `tool-contracts/replay_request.contract.md` | `lab_or_evidence_contract_observation_only` | derived; no production success | sign/token/cookie success claim or production replay claim | input-output evidence contract and negative boundary seed |
| Environment patch and browser-node parity boundary | `tool-contracts/compare_browser_vs_node.contract.md`, `2-JS逆向工具层/env-patch/references/governance.md` | `tool_contract_mapping` | derived | concealment, falsification, or parity success claim without evidence | browser-node parity evidence and failure split |
| Hook tracing as observation evidence | `tool-contracts/extract_runtime_trace.contract.md`, `99-SKILLS治理/18-证据验证拒答人工复核与监控规约.md` | `lab_or_evidence_contract_observation_only` | observed as marker; operational details unverified | hook-based defeat workflow or stealth instruction | human review boundary and observation-only ledger |
| Eval, onboarding, and negative boundary seeds | `1-业务流程层/skills-evaluation-governance/evals`, `99-SKILLS治理/22-LOW-LOOP-EXECUTION-LOG.md` | `eval_seed_without_verbatim_copy` | derived | copied external tests/examples or active skill onboarding | eval 027 must fail unsafe conversions |
| Foundation/base handling | existing internal skill/tool-contract/eval/governance ledger named in each row | `tool_contract_mapping` | derived | unattached abstract capability or production capability claim | every row must name base asset, evidence level, prohibited conversion, and validator |

## LCL-08 Absorption Matrix

| LCL-08 source fact pack | Target internal base asset | Absorption mode | Prohibited conversion | Validation required | Remaining gap |
|---|---|---|---|---|---|
| `jshook-skill` page-level fact pack with GPL-3.0 status and risk-sensitive markers | runtime trace/evidence contracts, governance eval negative seeds, clean-room fusion contract | `reference_only`, `eval_seed_without_verbatim_copy`, `lab_or_evidence_contract_observation_only` | GPL implementation import; copied hook code; concealment/falsification workflow; active skill | eval 027 and human review for any risk-sensitive expansion | no raw external files read; no implementation detail imported |
| `hello_js_reverse_skill` page-level fact pack with unknown visible license | governance ledger reference only, negative boundary eval seeds, evidence refusal rules | `reference_only`, `lab_or_evidence_contract_observation_only` | clean-room summary before license verification; code/template/prompt import; risk marker upgraded to capability | eval 027 must fail import or operational conversion | license remains unknown; full contents unverified by design |
| `ai-reverse-toolkit` page-level fact pack with MIT status | crypto-entry contract, env-patch parity boundary, eval/onboarding negative seeds, foundation attachment rule | `clean_room_summary`, `eval_seed_without_verbatim_copy`, `tool_contract_mapping`, `lab_or_evidence_contract_observation_only` | copied source/templates/examples; real-site success claim; production sign/token claim | eval 027 plus loop/acceptance validators | only category-level patterns absorbed; no external examples imported |

## Required Evidence Ledger
- source fact pack identifier from LCL-20260709-08
- LCL-20260709-09 clean-room gate decision
- internal base asset receiving the absorption
- evidence level and limitation
- explicit no-import statement
- validation command or human review boundary
- cleanup ledger entry for temporary or rejected material

## Failure Modes
- External repository code, templates, prompts, tests, or examples appear in repository assets.
- `skills-manifest.json` is edited or an active skill is created from external material.
- Risk-sensitive marker is converted into operational capability, production workflow, or success claim.
- Absorbed pattern lacks a named internal base asset, evidence level, or validation path.
- Unknown-license material is summarized beyond reference-only handling.

## Acceptance Checks
- Absorption lands only in internal contracts, evals, ledgers, or verification reports.
- Every absorbed pattern is attached to an existing internal base asset.
- Evidence levels and remaining gaps are explicit.
- No external raw file is fetched, cloned, or read for this loop.
- No real-site success, sign/token success, challenge defeat, concurrency, or production capability is claimed.
