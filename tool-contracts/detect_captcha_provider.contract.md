## Purpose
Identify the CAPTCHA or verification provider and separate provider-state success from business-flow success.

## Allowed Scope
- Provider detection from scripts, iframes, network hosts, sitekeys, and response markers.
- Do not solve third-party CAPTCHA challenges unless the task scope explicitly authorizes a local or permitted test environment.

## Inputs
- Script inventory, runtime trace, and challenge-state report.
- UI snapshot notes and provider-host allowlist when available.

## Outputs
- Provider classification with observed indicators.
- Provider-state versus business-state notes.

## Evidence Files
- `captcha-provider-report.json`
- `provider-indicators.md`
- `challenge-assets/`

## Command Examples
```powershell
python tools/vendor_demo_runner.py --target <target_id> --out <evidence_dir>
```

## Failure Modes
- Multiple providers are present on one page.
- Testing keys or demo widgets are mistaken for production acceptance.
- Provider token success is treated as business API success.

## Retry Strategy
- Re-capture scripts and network evidence from clean state.
- Require downstream business assertion before any positive capability claim.

## Cleanup Rules
- Do not retain provider secrets, live tokens, or account identifiers.
- Separate demo or testing-key evidence from real target evidence.

## Acceptance Checks
- Provider indicators are tied to files, hosts, or DOM markers.
- Business acceptance is explicitly verified or marked not verified.

## Related Skills
- `captcha-provider-diagnostics`
- `captcha-service-delivery`
- `web-h5-loop-engineering`
