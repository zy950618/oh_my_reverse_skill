# SKILLS Changelog

## 2026-07-09 — LCL-20260709-11 internal base hardening

```yaml
change_id: LCL-20260709-11
branch: loop/20260709-11-internal-base-hardening
profile: low_cost_structure
capability_claim: STRUCTURE_ONLY
status: structure_hardening_recorded
```

### Changed

- Hardened `tool-contracts/collect_scripts.contract.md` with source fact pack linkage, script hash/freshness, evidence level, `raw_secret_persisted: false`, and `raw_external_imported: false` acceptance.
- Hardened `tool-contracts/extract_runtime_trace.contract.md` with observation-only trace requirements: capture id, run id, script hash, call stack status, input/output redaction, and evidence level.
- Hardened `tool-contracts/search_crypto_entry.contract.md` with observed request field anchor, call chain, input/output evidence, source fact pack linkage, and no copied external snippets.
- Hardened `tool-contracts/compare_browser_vs_node.contract.md` with fixture id, browser run id, Node run id, source freshness, evidence level, and `production_claim: false`.
- Hardened `2-JS逆向工具层/env-patch/references/governance.md` with foundation/base attachment requirements for absorbed categories.
- Added negative eval seeds for find-crypto-entry, env-patch, and js-page-runtime-parity boundary handling.
- Added LCL-11 execution, verification, ledger, and acceptance records.

### Evidence level

- `observed`: only repository-local LCL-10 records and existing internal base assets were used.
- `observed`: no external raw repository file was fetched, cloned, read, copied, or imported in this loop.
- `derived`: LCL-10 absorption categories now require stricter acceptance clauses and negative eval handling before promotion.
- `unverified`: no real-domain capability, sign/token success, protected-control success, concurrency, or production success is claimed.

## 2026-07-09 — LCL-20260709-10 external capability absorption base

```yaml
change_id: LCL-20260709-10
branch: loop/20260709-10-external-absorption-base
profile: low_cost_structure
capability_claim: STRUCTURE_ONLY
status: structure_absorption_recorded
```

### Changed

- Added `tool-contracts/external_capability_absorption.contract.md` to map external observed capability categories into existing internal base assets only.
- Added `1-业务流程层/skills-evaluation-governance/evals/027-external-capability-absorption-base.yaml` to fail external raw file read/import, active skill creation, manifest edits, and risk marker operational upgrades.
- Added absorption matrix for the three LCL-08 source fact packs using only already-recorded repository facts.
- Added foundation/base handling: every absorbed pattern must attach to an existing skill, tool contract, eval, or governance ledger with evidence level, prohibited conversion, validation requirement, and remaining gap.
- Added LCL-10 execution, verification, ledger, and acceptance records.

### Evidence level

- `observed`: only repository-local LCL-08 fact packs and LCL-09 clean-room rules were used.
- `observed`: no external raw repository file was fetched, cloned, read, copied, or imported in this loop.
- `derived`: capability patterns can be absorbed only as internal base mappings, evidence contracts, or negative eval seeds.
- `unverified`: no real-domain capability, sign/token success, challenge defeat, concurrency, or production success is claimed.

## 2026-07-09 — LCL-20260709-09 external clean-room fusion contract

```yaml
change_id: LCL-20260709-09
branch: loop/20260709-09-external-fusion-contract
profile: low_cost_structure
capability_claim: STRUCTURE_ONLY
status: structure_contract_and_eval_seed_recorded
```

### Changed

- Added `tool-contracts/external_clean_room_fusion.contract.md` to define inputs, outputs, evidence, failure modes, retry rules, and acceptance checks for internal clean-room external-source fusion.
- Added `1-业务流程层/skills-evaluation-governance/evals/026-external-source-fusion-gate.yaml` to fail external code/template/prompt import, GPL or unknown-license import, active skill creation, and manifest edits.
- Required fact pack, license decision, prohibited-use scan, allowed fusion mode, attribution plan, and validation ledger before any fusion step.
- Preserved STRUCTURE_ONLY: outputs are abstract contracts, eval seeds, or reference notes only.
- Added LCL-09 execution, verification, ledger, and acceptance records.

### Evidence level

- `observed`: LCL-08 fact packs already exist in this repository and were used as the only source base.
- `observed`: no external raw repository file was fetched, cloned, or read in this loop.
- `derived`: risk-sensitive markers remain observation/lab/evidence-contract only and cannot become concealment, falsification, WAF defeat, fingerprint falsification, or production workflow instructions.
- `unverified`: Claude validation suite is recommended for rerun; `hello_js_reverse_skill` license remains unknown.

## 2026-07-09 — LCL-20260709-08 external-source fact packs

```yaml
change_id: LCL-20260709-08
branch: loop/20260709-08-external-source-facts
profile: low_cost_structure
capability_claim: STRUCTURE_ONLY
status: observed_source_facts_recorded
```

### Changed

- Recorded page-level fact packs for `jshook-skill`, `hello_js_reverse_skill`, and `ai-reverse-toolkit` using public GitHub observations only.
- Preserved clean-room boundaries: no external code/template import and no active skill creation.
- Added license gates: GPL-3.0 source is no-code-import reference/clean-room/eval-seed only; MIT source may be clean-room summarized but not imported in this loop; unknown license remains reference-only.
- Recorded risk-sensitive markers such as concealment, fingerprint falsification, hook injection, dynamic cookie/token/sign workflows, and protocol/WAF-adjacent claims as observation/lab/evidence-contract only.
- Added LCL-08 execution, verification, ledger, and acceptance records.

### Evidence level

- `observed`: GitHub public pages were visible for all three authorized source URLs.
- `observed`: local `git ls-remote --symref ... HEAD` succeeded for all three authorized source URLs and recorded HEAD hashes.
- `derived`: risk-sensitive capabilities cannot be fused as concealment, falsification, WAF defeat, or production success.
- `unverified`: no raw external files, full repository contents, or real-site success evidence were fetched or imported.

## 2026-07-09 — LCL-20260708-07 external fusion unknown-source ledger

```yaml
change_id: LCL-20260708-07
branch: loop/20260708-07-external-fusion
profile: low_cost_structure
capability_claim: STRUCTURE_ONLY
status: blocked_waiting_source_url_or_path
```

### Changed

- Recorded `ai-reverse-toolkit`, `jshook-skill`, and `hello_js_reverse_skill` as requested external source names only.
- Added unknown-source handling: no guessed GitHub URL, no observed source claim, no code copy, and no active skill creation.
- Defined required evidence before any source can move from `unverified` to `observed`: source URL/path, existence proof, README/SKILL inventory, license status, allowed use, forbidden use, target layer, and validation evidence.
- Added LCL-07 execution, verification, ledger, and acceptance records.

### Evidence level

- `observed`: no user-provided URL/path exists in this run for the three external source names.
- `derived`: external fusion must remain `reference_only` / `clean_room_summary` until source identity and license evidence are collected.
- `unverified`: no external repository content, license, capability, or code was verified; no GitHub project is claimed fused.

## 2026-07-09 — LCL-20260708-06 JS runtime evidence manifest

```yaml
change_id: LCL-20260708-06
branch: loop/20260708-06-js-runtime-evidence
profile: low_cost_structure
capability_claim: STRUCTURE_ONLY
status: structure_contract_recorded
```

### Changed

- Added the required scripts manifest fields to `tool-contracts/collect_scripts.contract.md`.
- Required `raw_secret_persisted: false` for long-term script evidence.
- Added `redaction_status` enum: `clean`, `redacted`, `blocked`, `manual_review_required`.
- Added `source_freshness` enum: `fresh`, `stale`, `unknown`; `stale` and `unknown` cannot be positive capability proof.
- Clarified runtime parity and env-patch boundaries: named fixture/input/run_id only, not business API, risk-token, WAF/challenge, clearance-cookie, or production success.
- Added LCL-06 execution, verification, ledger, and acceptance records.

### Evidence level

- `observed`: structure contracts and low-loop records were updated in the allowed files only.
- `derived`: long-term evidence is safer when raw secret persistence is blocked or forced to manual review.
- `unverified`: no real-domain capture, script snapshot, sign/token, WAF/challenge, concurrency, or production success is claimed for LCL-06.

## 2026-07-09 — LCL-20260708-05 score JSON output stabilization

```yaml
change_id: LCL-20260708-05
branch: loop/20260708-05-score-json-output
profile: low_cost_structure
capability_claim: STRUCTURE_ONLY
status: validated_structure_pass
```

### Changed

- Added `--json-out <path>` to `tools/governance/score_skills.py`.
- Reused the existing aggregate summary object for both stdout and optional JSON file output.
- Kept default stdout behavior compatible: stdout still prints the human-readable summary and then `ci_gate` output.
- Added LCL-05 execution, verification, ledger, and acceptance records.

### Evidence level

- `observed`: `python3 -m json.tool .ci-out/score-summary.json` parsed the generated file successfully.
- `observed`: default `score_skills.py --repo . --manifest skills-manifest.json` exited 0 after the change.
- `observed`: release `ci_gate --release` passed on Claude rerun after the Codex sandbox run reported a transient localhost bind permission failure.
- `unverified`: no real-domain capability, sign/token, concurrency, WAF/challenge, or production success is claimed for LCL-05.

## 2026-07-09 — LCL-20260708-04 install-safe-uninstall consolidation

```yaml
change_id: LCL-20260708-04
branch: loop/20260708-04-install-safe-uninstall-consolidation
profile: low_cost_structure
capability_claim: STRUCTURE_ONLY
status: validated_structure_pass
```

### Changed

- Updated `低LOOP-Codex执行工程包.md` as the current authoritative low-cost loop execution source.
- Recorded `LCL-20260708-03` manifest design as observed merged evidence instead of a planned task.
- Set `LCL-20260708-04` as the active latest objective for INSTALL safe uninstall and execution-surface consolidation.
- Updated `INSTALL.md` uninstall instructions so deletion is gated by manifest membership and target/junction/symlink checks.
- Added LOW LOOP execution and verification records:
  - `99-SKILLS治理/22-LOW-LOOP-EXECUTION-LOG.md`
  - `99-SKILLS治理/23-LOW-LOOP-VERIFICATION-REPORT.md`
  - `tools/reports/LCL-20260708-04-loop-ledger.json`
  - `tools/reports/LCL-20260708-04-acceptance.md`

### Superseded / consolidated

- `低LOOP执行-拉取卸载与再生成方案.md` is no longer an active execution source.
- `SKILLS融合建议与能力缺口处理.md` is no longer an active execution source.
- Historical conflict where `LCL-20260708-04` meant score JSON output is recorded as superseded; score JSON remains a future single-topic task (`LCL-20260708-05`) if still needed.

### Evidence level

- `observed`: LCL-03 manifest design exists in git history and current manifest tooling/docs.
- `derived`: LCL-04 safe uninstall should rely on manifest membership plus target checks.
- `unverified`: completion remains pending until validation report records all required command results.
