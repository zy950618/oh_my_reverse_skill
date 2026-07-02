## Purpose
Build a small FastAPI adapter around verified pure API behavior for local testing and delivery.

## Allowed Scope
- Local service wrapper, schemas, health checks, and non-destructive endpoints.
- Do not hardcode live secrets, tokens, or protected session state.

## Inputs
- Verified API client or workflow functions.
- Request and response schemas.
- Runtime configuration plan.

## Outputs
- FastAPI app files or adapter package.
- Local run instructions and smoke-test evidence.

## Evidence Files
- `adapter-runbook.md`
- `openapi-check.json`
- `smoke-test-result.json`

## Command Examples
```powershell
python -m pytest <tests_path>
```

## Failure Modes
- Adapter diverges from verified replay behavior.
- Config requires undeclared environment variables.
- Schema accepts invalid or unsafe input.

## Retry Strategy
- Add focused tests around the failing adapter route.
- Compare adapter output to replay fixture before widening scope.

## Cleanup Rules
- Remove temporary debug endpoints.
- Keep generated OpenAPI evidence only if it matches the final adapter.

## Acceptance Checks
- Local smoke test passes against verified fixtures or authorized sandbox.
- Public route behavior is documented and schema-validated.

## Related Skills
- `website-314-api-delivery`
- `site-api-adapter`
- `karpathy-guidelines`
