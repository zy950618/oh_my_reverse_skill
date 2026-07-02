## Purpose
Convert CAPTCHA model outputs into scoped local or authorized action plans for replay evaluation.

## Allowed Scope
- Localhost labs, synthetic tasks, or explicitly authorized action replay.
- Do not automate unauthorized third-party CAPTCHA solving.

## Inputs
- Model prediction output.
- Challenge geometry, UI coordinate frame, and action policy.
- Replay scope and stop conditions.

## Outputs
- Action plan with coordinates, timing, confidence, and failure conditions.
- Replay-ready action fixture.

## Evidence Files
- `prediction-output.json`
- `action-plan.json`
- `coordinate-frame.md`
- `stop-conditions.md`

## Command Examples
```powershell
python tools/captcha_action_executor.py --plan <action_plan> --out <evidence_dir>
```

## Failure Modes
- Coordinate frame does not match rendered challenge.
- Predictor overfits to static fixtures.
- Action policy lacks stop conditions.

## Retry Strategy
- Recompute coordinates from fresh rendered state.
- Replay failures into the failure-sample queue.

## Cleanup Rules
- Remove action plans that include live third-party challenge identifiers.
- Retain failed plans when used for model improvement evidence.

## Acceptance Checks
- Action plan references prediction evidence and coordinate frame.
- Replay scope and stop conditions are explicit.

## Related Skills
- `captcha-action-planner`
- `captcha-model-action-e2e`
- `captcha-service-delivery`
