# 低 LOOP Cleanup Ledger — 20260710 skills-experience

## Scope

Single-topic cleanup for low LOOP leftovers:

- retire active `LOOP.md` / `STATE.md` assumptions from docs and structure validation;
- reduce `skills-experience/fingerprint-diagnostics/` from tracked run history to a lightweight representative card index;
- document deleted paths, retained evidence, validation, and rollback notes.

## Non-goals

- Do not change the architecture remediation design content.
- Do not include unrelated existing worktree changes in `低LOOP-Codex执行工程包.md`.
- Do not treat public fingerprint diagnostics as production WAF/challenge bypass capability.
- Do not delete formal evidence under `public-range-evidence/`, evals, or scope contracts.

## Deleted paths

| Path | Decision | Reason | Not unique evidence because | Rollback |
|---|---|---|---|---|
| `skills-experience/fingerprint-diagnostics/run-20260630-053000-phase3-6-public-model/` | delete | Early single-target run card; superseded by later matrix/smoke cards and formal eval/evidence layers. | Only thin `sannysoft.yaml` card; `evals/phase3-6/003-fingerprint-public-diagnostics.yaml` retains the source run id, and formal fingerprint evidence lives under `public-range-evidence/`. | `git restore --source <pre-cleanup-ref> -- skills-experience/fingerprint-diagnostics/run-20260630-053000-phase3-6-public-model` |
| `skills-experience/fingerprint-diagnostics/run-20260630-061500-scope-contract-positive/` | delete | Early single-target scope-contract card; no active reference outside the card itself. | Scope boundary is represented by `configs/range_scope_contract.yaml` and fingerprint diagnostics evals. | `git restore --source <pre-cleanup-ref> -- skills-experience/fingerprint-diagnostics/run-20260630-061500-scope-contract-positive` |
| `skills-experience/fingerprint-diagnostics/run-20260630-071500-phase3-6-1-candidate/` | delete | Intermediate candidate run cards for creepjs/sannysoft; superseded by later multi-target matrix and formal evals. | No active references outside the deleted cards; later representative cards remain. | `git restore --source <pre-cleanup-ref> -- skills-experience/fingerprint-diagnostics/run-20260630-071500-phase3-6-1-candidate` |
| `skills-experience/fingerprint-diagnostics/run-20260630-101500-phase3-8-family-hardening/` | delete | Intermediate run cards duplicated by formal phase3-8 evals and public evidence references. | Active references point to evals and `public-range-evidence/fingerprint-diagnostics/...`, not to these skills-experience YAML files. | `git restore --source <pre-cleanup-ref> -- skills-experience/fingerprint-diagnostics/run-20260630-101500-phase3-8-family-hardening` |

## Retained evidence/cards

| Path | Reason |
|---|---|
| `skills-experience/fingerprint-diagnostics/run-20260630-173000-phase3-11-type-matrix/` | Representative multi-target card set covering browserleaks, creepjs, incolumitas, and sannysoft. |
| `skills-experience/fingerprint-diagnostics/run-20260701-phase4a-smoke/` | Current smoke-style card set retained for now; can be summarized in a future cleanup if redundant. |
| `skills-experience/fingerprint-diagnostics/README.md` | Documents that this directory is only a lightweight card index, not the formal evidence store. |
| `public-range-evidence/` | Formal evidence surface; not touched by this cleanup. |
| `evals/phase3-*` and skill `evals/` | Formal behavior/safety expectations; not touched by this cleanup. |
| `configs/range_scope_contract.yaml` | Scope contract for public diagnostics; not touched by this cleanup. |

## Documentation and validator updates

| Path | Change |
|---|---|
| `docs/loop-engineering.md` | Replaced stale `STATE.md` / `LOOP.md` source-of-truth wording with ledger/report/cleanup-ledger sources. |
| `tools/validators/validate_structure.py` | Removed retired `STATE.md` / `LOOP.md` from source-of-truth docs and now fails if those retired files are recreated as active state sources. |

## Validation record

Planned commands:

```bash
git status --short
git diff --name-status
rg -n 'Current loop state lives in `STATE.md`|Current loop operating rules live in `LOOP.md`|missing source-of-truth doc: STATE.md|missing source-of-truth doc: LOOP.md' docs tools
rg -n 'run-20260630-053000-phase3-6-public-model|run-20260630-061500-scope-contract-positive|run-20260630-071500-phase3-6-1-candidate|run-20260630-101500-phase3-8-family-hardening' .
python3 tools/validators/validate_structure.py
python3 tools/evidence/validate_evidence_policy.py
python3 tools/evidence/validate_scope_contract.py
```

Actual results:

| Command | Result |
|---|---|
| `git status --short` | Shows expected cleanup changes plus pre-existing unrelated `低LOOP-Codex执行工程包.md` modification and untracked `低LOOP-Claude-Codex架构补强规则设计.md`; those unrelated files were not edited by this cleanup. |
| `git diff --name-status` | Shows docs/validator updates, seven skills-experience YAML deletions, and the pre-existing unrelated low LOOP package modification. |
| stale `STATE.md` / `LOOP.md` exact active-source grep | No matches for the retired active-source phrases in `docs` or `tools`. |
| deleted run reference grep | Remaining matches are in this cleanup ledger and formal eval/public-evidence references, not the deleted skills-experience YAML files. |
| `python3 tools/validators/validate_structure.py` | PASS, exit 0. |
| `python3 tools/evidence/validate_evidence_policy.py` | PASS, exit 0. |
| `python3 tools/evidence/validate_scope_contract.py --config configs/range_scope_contract.yaml --evidence-root public-range-evidence` | PASS, exit 0. |

## Known remaining gaps

- Existing unrelated worktree changes are intentionally outside this cleanup ledger.
- `tools/fingerprint/fingerprint_range_runner.py` still writes skills-experience cards; this cleanup only documents retention and prunes historical cards. A future LCL should decide whether to change the generator.
- `1-业务流程层/web-h5-loop-engineering/SKILL.md` still uses `LOOP_STATE.md`; this cleanup focused on `LOOP.md` / `STATE.md` active doc and validator conflicts. A future LCL should align that skill wording if the project wants no root/state file references at all.

## Rollback notes

- Restore deleted run cards with `git restore --source <pre-cleanup-ref> -- skills-experience/fingerprint-diagnostics/<run-dir>`.
- Revert `docs/loop-engineering.md` and `tools/validators/validate_structure.py` together if docs and validator become inconsistent.
- Remove `skills-experience/fingerprint-diagnostics/README.md` if the directory is later deleted entirely.
