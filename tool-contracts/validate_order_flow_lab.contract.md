## Purpose
Validate an authorized order-flow lab path without crossing into real payment or irreversible actions.

## Allowed Scope
- Local lab, sandbox, or explicitly authorized order-flow stages.
- Stop before real charge, irreversible order placement, or production mutation unless approved.

## Inputs
- Flow definition with allowed stages.
- Fixtures, test account constraints, and stop conditions.
- Business assertion requirements.

## Outputs
- Stage-by-stage validation report.
- Business-data assertion status and stop ledger.

## Evidence Files
- `order-flow-ledger.json`
- `stage-results.json`
- `business-assertions.json`
- `stop-ledger.md`

## Command Examples
```powershell
python tools/validate_business_data_assertions.py --evidence <evidence_dir>
```

## Failure Modes
- Flow reaches an unauthorized irreversible stage.
- Stage success is inferred from HTTP status only.
- Fixture state is stale or reused incorrectly.

## Retry Strategy
- Reset lab state and rerun only failed authorized stages.
- Require business assertions before promoting a stage.

## Cleanup Rules
- Remove temporary test orders only when cleanup is approved and reversible.
- Preserve ledgers before any lab-state reset.

## Acceptance Checks
- Every stage has status, assertion, and stop-condition evidence.
- Real payment or irreversible execution is not performed without approval.

## Related Skills
- `authorized-target-adapter`
- `website-314-api-delivery`
- `web-h5-loop-engineering`
