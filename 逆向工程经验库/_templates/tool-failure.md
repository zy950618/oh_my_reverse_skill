# Tool Failure Sample

```yaml
failure_id:
domain:
run_id:
stage:
tool_or_skill:
symptom:
trigger:
observed_evidence:
wrong_ai_behavior:
root_cause:
correct_handling:
regression_eval_needed:
```

## Common Wrong AI Behavior

- Uses old HAR/token/profile as fresh evidence.
- Treats a wrapper/logging frame as the real generator.
- Keeps stale scriptId after refresh.
- Hardcodes a header, token, fingerprint, timestamp, or storage value.
- Generalizes one market/session/route to all flows.
- Changes one endpoint or field without graph and impact regression.
