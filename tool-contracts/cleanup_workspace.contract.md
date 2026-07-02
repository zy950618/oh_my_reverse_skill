## Purpose
Clean temporary task artifacts after required evidence has been preserved and final verification is recorded.

## Allowed Scope
- Remove only task-created temporary files, debug dumps, caches, and superseded staging artifacts.
- Do not delete unique evidence, user changes, or unrelated repository files.

## Inputs
- Cleanup ledger listing created paths.
- Evidence preservation checklist.
- Verification and delivery status.

## Outputs
- Cleanup report with kept, removed, and skipped paths.
- Remaining risk notes for files intentionally left in place.

## Evidence Files
- `cleanup-ledger.md`
- `kept-evidence.md`
- `removed-paths.md`

## Command Examples
```powershell
python tools/post_task_reminder.py
```

## Failure Modes
- Cleanup target includes user-created files.
- Unique failure evidence has not been migrated.
- Generated caches are mixed with delivery artifacts.

## Retry Strategy
- Rebuild the cleanup ledger from git status and task notes.
- Skip ambiguous paths and report them instead of deleting.

## Cleanup Rules
- Preserve evidence before deletion.
- Require explicit approval for broad or irreversible removal.

## Acceptance Checks
- Cleanup report identifies every removed path and reason.
- No unrelated dirty files are modified or reverted.

## Related Skills
- `karpathy-guidelines`
- `web-h5-loop-engineering`
- `skills-evaluation-governance`
