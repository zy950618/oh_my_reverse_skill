# Reverse Memory

Domain:
Owner:
Last updated:

## Read First

- Must-read old runs:
- Known stale evidence:
- Known stable evidence:
- First checks before opening browser:

## Run Ledger

| run_id | captured_at | auth_state | browser_profile_id | state_reset | script_hash | result | freshness_decision |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |

## Delivery Confirmation

```yaml
delivery_status: success_browserless_verified | blocked_by_protection | blocked_by_auth | blocked_by_manual_challenge | partial_adapter_only | negative_baseline_only | unverified
verification_mode: browser_automated_verified | human_reviewed_verified | blocked_by_manual_challenge | blocked_by_protection | not_applicable | unverified
completed_confirmations:
  - <真实接口测试已完成确认>
incomplete_confirmations:
  - <仍未完成/阻塞/未验证>
next_skip_paths:
  - <下次不再重复处理的错误路径>
knowledge_graph_path:
impact_regression_path:
```

## Current Working Facts

| fact | label | evidence | last_revalidated_by |
|---|---|---|---|
|  | observed/derived/assumed/unverified |  |  |

## Stale Or Invalidated Facts

| old_fact | old_evidence | invalidated_by | correct_handling |
|---|---|---|---|
|  |  |  |  |

## Tool Failure Samples

| symptom | tool/stage | root_cause | next_handling |
|---|---|---|---|
|  |  |  |  |

## Data Drift And Offset Notes

| field/json_pointer | old_shape | new_shape | impact | required_regression |
|---|---|---|---|---|
|  |  |  |  |  |

## Next Task Checklist

- [ ] Read this file before capture.
- [ ] Create a fresh `run_id`.
- [ ] Record browser profile and reset state.
- [ ] Compare old HAR/token/script hash against fresh evidence.
- [ ] Write graph and impact changes before final output.
- [ ] Record completed and incomplete confirmations.
- [ ] Keep raw data in local project artifacts; write only redacted reusable lessons here.
