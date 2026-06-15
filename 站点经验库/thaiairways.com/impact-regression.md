# Thai Airways Impact Regression

每次更新 `thaiairways.com` 的端点、请求头、字段映射、状态、保护观察、adapter 或 eval，都要追加 Impact Record。

## Impact Record

```yaml
change_id:
date:
changed_node:
changed_edge:
change_type: add | modify | remove | deprecate
evidence:
direct_impact:
downstream_impact:
required_regression:
data_validation:
drift_risk:
rollback:
owner_notes:
```

## Regression Results

| Date | Change ID | Commands / Evidence | Result | Remaining Risk |
|---|---|---|---|---|
| | | | pass / warn / fail | |

## Rules

- If no impact is expected, write why and what evidence proves it.
- If a header/cookie/state/protection node changes, rerun the affected endpoint.
- If a response schema changes, run snapshot_diff and schema_alert.
- If a market/stage edge changes, rerun that market/stage only before expanding.

