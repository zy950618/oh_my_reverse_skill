# LOOP

## Current low-context mode
- current_phase: Phase 2
- current_target: old docs / loop / score history cleanup
- current_score: local gates PASS
- codex_blocking: 0
- merge_allowed: no
- next_action: validate cleanup, then run final subround Codex review

## Rules
- Process one minimal target per round.
- Locate with file names and line numbers before reading.
- Patch only target files.
- Keep `STATE.md` as current status only.
- Keep `.loop/run-log.md` to at most five recent summaries.
- Keep score docs on current gates only, not historical baselines.
