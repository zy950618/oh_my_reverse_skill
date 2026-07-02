# Phase 3.9 Provider Evidence

Version: 0.1.1

Source run_id: `run-20260630-113000-phase3-9-vendor-shield-range`.

Evidence:

- `public-range-evidence/shumei-captcha-demo/run-20260630-113000-phase3-9-vendor-shield-range.json`
- `public-range-evidence/aliyun-captcha-demo/run-20260630-113000-phase3-9-vendor-shield-range.json`
- `public-range-evidence/shumei-compatible-lab/run-20260630-113000-phase3-9-vendor-shield-range.json`
- `public-range-evidence/aliyun-compatible-lab/run-20260630-113000-phase3-9-vendor-shield-range.json`

Known failures:

- Official demos did not promote to positive.
- Aliyun official path requires a self-owned scene/app integration for full verify flow.
- Compatible-lab success is not vendor production success.

Eval backlog:

- Add self-owned vendor trial only with explicit scene/app scope.
- Add failure samples when any family drops below threshold.
