# Docs Cleanup Ledger

File: `STATE.md`
Category: source_of_truth
Keep reason: Current loop state source with compact fields only.
Delete reason: none.
Migrated content: Rewrote current goal/action for docs cleanup and removed changed-file history.
Action: keep compact.
Validation: structure validator checks field-only shape and rejects long history markers.

File: `LOOP.md`
Category: source_of_truth
Keep reason: Current low-context loop operating rules.
Delete reason: none.
Migrated content: Added current target, score, Codex status, merge decision, and next action.
Action: keep compact.
Validation: linked from docs/loop-engineering.md.

File: `.loop/run-log.md`
Category: active_reference
Keep reason: Recent loop summaries, limited to five rounds.
Delete reason: none while under five summaries.
Migrated content: Compressed current history into recent summaries only.
Action: keep compact.
Validation: structure validator fails if more than five numbered summaries appear.

File: `.loop/score-ledger.md`
Category: stale_score
Keep reason: Only current score row has active value.
Delete reason: Old per-round score rows are process history.
Migrated content: Current active count, minimum active score, strict score, release gate, cleanup gate.
Action: rewrite to current state only.
Validation: structure validator rejects stale score rows and active docs with old score history.

File: `.loop/cleanup-ledger.md`
Category: legacy_report
Keep reason: Latest cleanup evidence belongs in a compact cleanup ledger.
Delete reason: Old phase-by-phase cleanup sections are process history.
Migrated content: Current docs/history cleanup action and workspace cleanup result placeholder.
Action: rewrite to current cleanup entry only.
Validation: cleanup gate plus residue scan.

File: `.loop/codex-review-ledger.md`
Category: active_reference
Keep reason: Only allowed location for the environment-limitation note.
Delete reason: Old phase review entries are process history.
Migrated content: Preserve required sandbox note exactly and add current review placeholder.
Action: rewrite to current ledger plus sandbox note.
Validation: structure validator allows sandbox terms only here and forbids them in public docs.

File: `.loop/skill-dedupe-ledger.md`
Category: active_reference
Keep reason: Current 15 active skill role dedupe evidence remains relevant for Phase 2 final review.
Delete reason: none in this round.
Migrated content: none.
Action: keep.
Validation: structure/routing/score gates.

File: `99-SKILLS治理/05-当前评分与回测结果.md`
Category: source_of_truth
Keep reason: Current score source of truth.
Delete reason: none.
Migrated content: Remove wording that points readers to historical baselines; keep only current score policy.
Action: keep compact.
Validation: structure validator rejects old score history wording in active docs.

File: `docs/scoring.md`
Category: source_of_truth
Keep reason: Current scoring contract.
Delete reason: none.
Migrated content: Current 93 gate, strict score, score command, release command.
Action: keep compact.
Validation: structure validator requires source-of-truth docs and rejects stale score rows.

File: `docs/loop-engineering.md`
Category: source_of_truth
Keep reason: Current loop documentation policy.
Delete reason: none.
Migrated content: Current limits for state, run log, score, Codex blocking, merge_allowed, next_action.
Action: keep compact.
Validation: structure validator checks STATE and run-log shape.

File: `reports/`
Category: delete_candidate
Keep reason: Directory may remain empty.
Delete reason: No markdown reports exist; not an active state source.
Migrated content: none.
Action: no tracked markdown deletion needed.
Validation: structure validator rejects `reports/loop_state` if it reappears.

File: `memory-templates/`
Category: source_of_truth
Keep reason: Listed as expected source-of-truth directory.
Delete reason: Directory missing before this cleanup.
Migrated content: Template docs remain under `站点经验库/_templates` and `逆向工程经验库/_templates`; no duplicate created.
Action: validator accepts either `memory-templates` or the two existing template directories.
Validation: source-of-truth presence check.
