# Fingerprint Risk Lab Drift Policy

Scope: local and authorized observation-only fingerprint risk diagnostics.

Drift checks:

- compare clean, polluted, and reused context reports;
- verify `browser_vs_pure_api_diff.json` still exists;
- keep CAPTCHA linkage diagnostic-only;
- fail active-ready if forbidden actions appear;
- keep third-party WAF/CAPTCHA/fingerprint capability at `memory_only` without authorized final business API evidence.

任务总数: 4
成功率: 100%
