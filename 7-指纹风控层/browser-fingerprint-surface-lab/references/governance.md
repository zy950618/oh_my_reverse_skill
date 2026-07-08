# Browser Fingerprint Surface Lab Governance

## Active-Ready Evidence

- Fresh evidence root: `public-range-evidence/fingerprint-risk-lab/fresh-evidence/`.
- Required validators: `tools/validate_fingerprint_surface_lab.py`, `tools/validate_browser_context_isolation.py`.
- Known failures: public diagnostics are observation-only and must not become evasion.
- Eval backlog: add negative tests for webdriver concealment, fingerprint falsification, proxy avoidance, clearance-cookie recycling, and risk-token reuse.
- Market matrix: not applicable; this is local/authorized diagnostics.

## Change Log

| 2026-07-01 | second LOOP active-ready | Added fresh local evidence, context isolation, drift policy, and validator coverage. |

## Drift

Drift policy requires repeat surface snapshots, clean/polluted/reused context separation, and no forbidden action output.

任务总数: 4
成功率: 100%
