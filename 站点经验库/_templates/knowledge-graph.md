# Knowledge Graph Template

本文件记录当前 domain 的 Web/H5 逆向知识图谱。每个节点和边都必须有证据；没有证据的内容只能标 `assumed` 或 `unverified`。

## Delivery State

```yaml
domain:
last_run_id:
delivery_status: success_browserless_verified | blocked_by_protection | blocked_by_auth | blocked_by_manual_challenge | partial_adapter_only | negative_baseline_only | unverified
verification_mode: browser_automated_verified | human_reviewed_verified | blocked_by_manual_challenge | blocked_by_protection | not_applicable | unverified
skills_participation: positive_allowed | negative_eval_only | memory_only | prohibited
completed_confirmations:
  - <真实接口测试已确认事项>
incomplete_confirmations:
  - <仍 blocked / incomplete / unverified 的事项>
next_skip_paths:
  - <下次不再重复尝试的错误路径>
```

## Nodes

| Node ID | Type | Scope | Status | Evidence | Notes |
|---|---|---|---|---|---|
| | domain / market / stage / endpoint / request-field / response-field / state / protection / implementation / eval | domain / market / stage / auth_state / session | observed / derived / assumed / unverified | request id / HAR summary / JSON Pointer / file path / eval path | |

## Edges

| From | Relation | To | Status | Evidence | Regression |
|---|---|---|---|---|---|
| | domain->market / market->stage / stage->endpoint / endpoint->field / field->state / endpoint->protection / implementation->endpoint / eval->node | | observed / derived / assumed / unverified | | |

## Minimum Graph For Delivery

| Situation | Required Nodes | Required Edges |
|---|---|---|
| real business endpoint found | `stage`, `endpoint` | `stage -> endpoint` |
| request depends on headers/cookies/body/query/storage | `request-field`, optional `state` | `endpoint -> request-field`, `request-field -> state` |
| deliverable response field exists | `response-field` | `endpoint -> response-field` |
| WAF/CAPTCHA/risk observed | `protection` | `endpoint -> protection` |
| implementation or adapter exists | `implementation` | `implementation -> endpoint` |
| eval or negative case added | `eval` | `eval -> node/edge` |

## Rules

- Every endpoint node needs request evidence.
- Every response-field node needs JSON Pointer evidence.
- Every protection node records observation and stability only.
- Every implementation edge needs file/function/test evidence.
- Do not generalize one market/stage/session to another without a separate edge.
- Do not mark `positive_allowed` unless the graph links a successful implementation to real endpoint evidence and regression evidence.
