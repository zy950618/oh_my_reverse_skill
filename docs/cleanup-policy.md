# Cleanup Policy

Keep durable rules and evidence; keep per-run cleanup output local.

Keep tracked:

- source-of-truth docs, templates, active references, active Skill files, stable contracts, and unique sanitized evidence required for regression.

Keep local/ignored:

- cleanup classification and run reports under `.ci-out/cleanup/`;
- local orchestration state under `.loop/`;
- regenerable scores, caches, debug output, and temporary reports.

Delete or rewrite:

- old run reports, stale score tables, phase reports, duplicate governance copies, generated reports with stale status, and process-only notes.

Before deleting anything, preserve unique failure evidence in memory, fixture metadata, a stable eval, or another durable evidence surface. Ambiguous or owner-created paths must be skipped and reported rather than removed.

Check before handoff:

```bash
python3 tools/lifecycle/cleanup_workspace.py --check
```

Use `--plan` or `--apply` only when their filesystem effects are authorized. Their reports are written to `.ci-out/cleanup/` and are not repository governance documents.
