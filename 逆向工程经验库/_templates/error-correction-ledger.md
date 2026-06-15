# Error Correction Ledger Template

```yaml
error_id:
detected_at:
domain:
stage:
original_claim:
original_level: observed | derived | assumed | unverified
corrected_level: observed | derived | assumed | unverified
why_wrong:
evidence_that_disproved_it:
files_changed:
memory_updates:
graph_updates:
wrong_code_removed:
kept_as_failure_evidence:
regression_added:
validation_command:
validation_result:
remaining_legacy_debt:
owner_notes:
```

## Rules

- Do not silently fix an error without updating memory or regression evidence.
- Delete wrong code only after preserving any unique failure evidence.
- If the error affected endpoint, field, state, protection, implementation, or eval, update knowledge graph and impact regression.

