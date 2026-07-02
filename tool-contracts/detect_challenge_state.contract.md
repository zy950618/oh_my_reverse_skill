## Purpose
Detect whether a response or browser state is normal business flow, challenge, block, rate limit, or unknown.

## Allowed Scope
- Classification from observed status codes, response bodies, headers, redirects, and UI state.
- Do not implement bypass, stealth, or challenge-solving behavior.

## Inputs
- Network trace, response sample, and UI snapshot notes.
- Target scope and expected business response markers.
- Known provider indicators when available.

## Outputs
- Challenge-state classification with evidence pointers.
- Unknown-state notes when evidence is insufficient.

## Evidence Files
- `challenge-state-report.json`
- `response-samples/`
- `ui-state-notes.md`

## Command Examples
```powershell
python tools/fingerprint_risk_state_report.py --input <trace_or_report> --out <evidence_dir>
```

## Failure Modes
- Business error is misclassified as protection.
- Challenge page is cached from old session state.
- Provider indicators are ambiguous.

## Retry Strategy
- Re-test with clean state and fresh trace.
- Compare normal baseline against challenge sample before classifying.

## Cleanup Rules
- Redact identifiers from response samples.
- Keep negative and unknown examples separate from positive evidence.

## Acceptance Checks
- Classification includes observed markers and confidence.
- Unknown or insufficient evidence is not promoted to observed fact.

## Related Skills
- `captcha-service-delivery`
- `fingerprint-block-reason-diagnostics`
- `imperva-waf-reese84`
