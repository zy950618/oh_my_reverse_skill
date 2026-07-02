# Fresh Evidence Contract

## Purpose

Define the minimum evidence for active-ready fingerprint surface diagnostics.

## Required Files

- `fingerprint_surface_report.json`
- `context_isolation_report.json`
- `browser_vs_pure_api_diff.json`
- `freshness_manifest.json`
- `validation_report.json`
- `drift_policy.md`

## Acceptance Checks

- clean context observed;
- polluted context observed;
- reused context observed;
- browser-vs-pure API diff exists;
- forbidden actions absent;
- source freshness is fresh.

## Boundary

This contract supports diagnostics only. It does not support stealth, spoofing, proxy evasion, WAF bypass, CAPTCHA bypass, or clearance reuse.
