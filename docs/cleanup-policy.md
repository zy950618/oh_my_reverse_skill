# Cleanup Policy

Keep current rules and evidence; remove process history.

Keep:

- source-of-truth docs, templates, active references, active skill files, current ledgers.

Delete or rewrite:

- old run reports, stale score tables, phase reports, duplicate governance copies, generated reports with stale FAIL status, and process-only notes.

Check before handoff:

```bash
python3 tools/lifecycle/cleanup_workspace.py --check
```
