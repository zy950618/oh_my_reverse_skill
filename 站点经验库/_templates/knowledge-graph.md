# Knowledge Graph Template

本文件记录当前 domain 的 Web/H5 逆向知识图谱。每个节点和边都必须有证据；没有证据的内容只能标 `assumed` 或 `unverified`。

## Nodes

| Node ID | Type | Scope | Status | Evidence | Notes |
|---|---|---|---|---|---|
| | domain / market / stage / endpoint / request-field / response-field / state / protection / implementation / eval | | observed / derived / assumed / unverified | | |

## Edges

| From | Relation | To | Status | Evidence | Regression |
|---|---|---|---|---|---|
| | domain->market / market->stage / stage->endpoint / endpoint->field / field->state / endpoint->protection / implementation->endpoint / eval->node | | observed / derived / assumed / unverified | | |

## Rules

- Every endpoint node needs request evidence.
- Every response-field node needs JSON Pointer evidence.
- Every protection node records observation and stability only.
- Every implementation edge needs file/function/test evidence.
- Do not generalize one market/stage/session to another without a separate edge.

