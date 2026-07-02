## Purpose
Deliver a pure API workflow for an authorized site path after endpoints, state, and response assertions are verified.

## Allowed Scope
- Query, cart, order-lab, or other explicitly authorized non-destructive workflows.
- Do not perform real payment or irreversible production actions without explicit approval.

## Inputs
- Endpoint map and replay evidence.
- State model for cookies, tokens, and generated fields.
- Business assertion requirements.

## Outputs
- API workflow implementation or delivery package.
- Runbook, fixtures, and acceptance evidence.

## Evidence Files
- `endpoint-map.md`
- `api-runbook.md`
- `acceptance-report.json`
- `fixtures/`

## Command Examples
```powershell
python tools/web_h5_acceptance_report.py --evidence <evidence_dir> --out <report>
```

## Failure Modes
- Single endpoint works but full workflow fails.
- Business data assertion is missing.
- Protected response is mistaken for accepted data.

## Retry Strategy
- Re-test from clean state and isolate the failed stage.
- Re-run replay and schema checks for affected endpoints only.

## Cleanup Rules
- Keep reusable fixtures; remove temporary exploratory scripts.
- Do not place delivery project code inside skill capability directories.

## Acceptance Checks
- Each workflow stage has replay evidence and business assertion status.
- Runbook states freshness, scope, and unsupported actions.

## Related Skills
- `website-314-api-delivery`
- `site-api-adapter`
- `authorized-target-adapter`
