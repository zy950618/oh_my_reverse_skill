# Loop Engineering

Current low LOOP operating context lives in the root low LOOP engineering documents. Per-run execution state is recorded in loop ledgers and reports, not in root state files.

Active sources:

- root `低LOOP-*` documents for current low LOOP planning and execution rules;
- `tools/web_h5/web_h5_loop_runner.py` ledgers for run/iteration records;
- `tools/reports/*-loop-ledger.json` and related acceptance reports for historical run evidence;
- cleanup ledgers for deletion, migration, and rollback decisions.

`LOOP.md` and `STATE.md` are retired and must not be recreated as active state sources. Local scratch state may live under ignored `.loop/` paths, but release-facing claims must point to ledgers, reports, or cleanup records.

Loop records must stay short:

- keep current phase and goal;
- keep current score and Codex blocking status;
- keep merge decision;
- keep at most five recent round summaries.

Long transcripts, generated review output, and old process logs do not belong in active docs.
