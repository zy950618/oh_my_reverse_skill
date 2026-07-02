# Phase 3.9 Benchmark Evidence

Version: 0.1.1

Source run_id: `run-20260630-113000-phase3-9-vendor-shield-range`.

Evidence:

- `public-range-evidence/shumei-compatible-lab/run-20260630-113000-phase3-9-vendor-shield-range.json`
- `public-range-evidence/aliyun-compatible-lab/run-20260630-113000-phase3-9-vendor-shield-range.json`
- `public-range-evidence/five-second-shield-lab/run-20260630-113000-phase3-9-vendor-shield-range.json`

Known failures:

- p95=0 on local compatible labs is not a stable production claim.
- Official vendor demos remain memory_only.
- Promotion remains candidate scoped by local lab contract.

Eval backlog:

- Add medium/hard/adversarial buckets before stable promotion.
- Add failure-case replay after any family metric drop.
