# SKILLS Changelog

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
