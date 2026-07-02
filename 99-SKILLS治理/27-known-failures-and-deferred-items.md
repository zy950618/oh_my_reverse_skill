# Known Failures And Deferred Items

## Known Failures

- `rg --files` failed with Windows access denied in this environment; PowerShell enumeration was used as fallback.
- The worktree was dirty before this task; unrelated existing changes were not reverted.
- Real external target execution was intentionally not performed.
- Cleanup deletion is blocked without explicit approval.
- Layer-7 fingerprint skills are still reported by `ci_gate` as ADVISORY, with observed scores below the 70 active threshold: `browser-fingerprint-surface-lab=54/70`, `fingerprint-block-reason-diagnostics=50/70`.

## Deferred Items

- Official Skill Bench run.
- Real authorized target collection for MH, 5J, TG, Scoot, VN, CZ, SQ.
- Verified real-site CAPTCHA/WAF/fingerprint backend acceptance.
- Promote layer-7 fingerprint skills from ADVISORY to active-ready by improving skill score evidence, references, eval coverage, and governance integration until each reaches `score >= 70`.
- Production-grade package distribution for any trained model.
- Human review before deleting any pre-existing candidate temp evidence.
