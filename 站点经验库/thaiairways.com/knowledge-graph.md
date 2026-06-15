# Thai Airways Knowledge Graph

本文件记录 `thaiairways.com` 的 Web/H5 逆向知识图谱。当前文件先建立图谱落点；未逐条补证据的节点保持 `unverified` 或引用既有站点文件。

## Nodes

| Node ID | Type | Scope | Status | Evidence | Notes |
|---|---|---|---|---|---|
| thaiairways.com | domain | Web/H5 | observed | site-memory.md | 站点入口和 API hosts 已在 site-memory.md 记录 |

## Edges

| From | Relation | To | Status | Evidence | Regression |
|---|---|---|---|---|---|
| thaiairways.com | domain->market | CN / TH / JP / US | derived | market-matrix.md + site-memory.md | 各 market 必须单独验证 |

## Rules

- Every endpoint node needs request evidence.
- Every response-field node needs JSON Pointer evidence.
- Every protection node records observation and stability only.
- Every implementation edge needs file/function/test evidence.
- Do not generalize one market/stage/session to another without a separate edge.

