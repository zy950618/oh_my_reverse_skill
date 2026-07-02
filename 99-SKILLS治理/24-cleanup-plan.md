# Cleanup Plan

## Policy

Cleanup is conservative. This repo already had many modified and untracked files before the standard LOOP work started, so automatic deletion is blocked unless a future user explicitly authorizes removal.

## Candidate Patterns

- `tmp/`, `temp/`, `.tmp/`
- `cache/`, `.cache/`
- `__pycache__/`, `.pytest_cache/`
- `coverage/`, `playwright-report/`
- `dist/`, `build/`
- `*.tmp`, `*.bak`, `*.old`, `*.orig`, `*.log`

## Required Retention

- `SKILL.md`
- `references/`
- `evals/`
- `tool-contracts/`
- `public-range-evidence/`
- manifests, schemas, metrics, model cards, package manifests
- validation reports, release gate report, cleanup ledger, known failures

## Execution

Run:

```bash
python tools/cleanup_workspace.py --check
python tools/cleanup_workspace.py --apply
```

`--apply` writes the cleanup ledger but does not delete files unless `--allow-delete` is added by a human after review.
