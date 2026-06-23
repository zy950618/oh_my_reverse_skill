# Impact Regression Template

每次更新站点规则、端点、请求头、字段映射、adapter、eval、保护观察或经验库，都要追加一条记录。

## Impact Record

```yaml
change_id:
date:
changed_node:
changed_edge:
change_type: add | modify | remove | deprecate
evidence:
delivery_status:
verification_mode:
completed_confirmation:
incomplete_confirmation:
direct_impact:
downstream_impact:
required_regression:
data_validation:
drift_risk:
rollback:
memory_update:
skills_participation:
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
- If WAF/CAPTCHA/risk state changes, verify the final business API backend acceptance; provider/challenge HTTP 200 is not enough.
- If `skills_participation` is `positive_allowed`, the record must link to successful endpoint evidence, graph nodes/edges, and regression output.
