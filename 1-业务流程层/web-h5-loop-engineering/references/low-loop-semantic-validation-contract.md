---
standard_id: LOW-LOOP-SEMANTIC-VALIDATION-CONTRACT
version: 3.0.0-candidate
implementation_status: MANUAL_ORCHESTRATED_LEDGER_ONLY
capability_level: structure_only
---

# Low-LOOP V3 语义不变量契约

本契约补充 JSON Schema 无法表达的跨对象、跨事件、时序、身份、授权和 Git 拓扑约束。它是 `structure_only` 规范，不是 operator entry、validator、执行循环或可运行接口，也不定义任何未来命令名称。`MUST`、`MUST NOT`、`SHOULD` 具有规范性含义。

校验输入是同一 bundle 中由 `index.schema.json` 引用的 TaskSpec、RunResult、ArtifactManifest、VerificationResult、GovernorDecision、AuthorizationGrant、CleanupDecision 与 BranchExecutionLedger。校验者必须先完成 JSON Schema 结构检查，再按下列不变量检查对象引用、hash、actor、grant、时间和状态转换。任一 MUST 失败都必须产生带不变量编号、受影响对象 ID、JSON Pointer 和证据 artifact ID 的 blocker；不得用模型说明替代证据。

### LL-S001 — workflow 与 run 状态分离

`RunResult.status=SUCCEEDED` 只表示该进程运行成功，MUST NOT 推导 `BranchExecutionLedger.current_workflow_status=CLOSED`、验证通过、治理放行、合并完成或能力晋级。`CLOSED` 必须由账本中完整的验证、治理、合并后复验与收尾事件链独立证明。

### LL-S002 — 模型证词不可信

executor 或其他模型产生的总结、完成声明与自评必须保持 `trust_class=MODEL_DATA`，且 MUST NOT 单独满足 assertion、grant、governor gate、cleanup 或关闭条件。引用模型证词时必须同时引用独立 observed artifact；否则结论为 `INCONCLUSIVE` 或 blocker。

### LL-S003 — observed run proof

声称某次运行已发生时，RunResult 必须具有不可混用的 `invocation_id`、`attempt_id`、`run_id`，并记录冻结的 `program`、`argv`、`cwd`、时间、timeout、exit/signal，以及 stdout/stderr artifact 引用。ArtifactManifest 中对应 artifact 的 producer run/command、hash 和时间必须匹配；缺失或冲突时不得把运行标为 observed proof。

### LL-S004 — executor 不得充当 verifier

每个 VerificationResult 的 `verifier_actor_id` MUST 与 `executor_actor_id` 不同，`verifier_run_id` MUST 与 `executor_run_id` 不同；验证事件的 actor 也必须与被验证 run 的 executor 不同。当前若无法提供 actor-separated verifier，只能记录人工独立复跑的实际边界并阻塞更强声明，不得通过更换角色标签伪造独立性。

### LL-S005 — governor 不得充当 executor

GovernorDecision 的 `governor_actor_id` MUST NOT 出现在其范围内的 `executor_actor_ids`，governor run 也不得是被裁决的 executor run。实施 gate、judge、测试或交付改动的 actor 不得对该改动自行放行。

### LL-S006 — grant 只能来自权威主体

AuthorizationGrant 必须链接 `trust_class=USER_AUTHORITY` 的 authority artifact，issuer principal 必须是对该 scope 有权授权的主体，且签发时间、有效期与撤销状态必须覆盖动作发生时间。TaskSpec、仓库数据、外部数据、模型、executor、verifier 或 governor 均不得自授权；TaskSpec 的 `grant_ids` 只引用外部 grant，不创造权限。

### LL-S007 — canonical roots

read、write、execute 与 output 必须分别在对应 roots 下校验。校验前必须将相对路径基于冻结 worktree 解析，消除 `.`/`..`，解析符号链接，并使用规范化绝对路径比较；路径同时命中 allowed 与 forbidden 时以 forbidden 为准。任何跨 root、路径穿越、符号链接逃逸或 root 类型替代都必须拒绝。

### LL-S008 — structured argv

每个计划或 observed command 必须由单个 `program` 与逐项 `argv[]` 表示，RunResult 必须与 TaskSpec 中相同 `command_id` 的结构化值一致。不得把完整 shell 指令、管道、重定向、命令替换或命令链放入一个字段后解释执行；数据参数不得被重新解析为 shell 语法。

### LL-S009 — artifact producer 与 lineage

每个 artifact ID 与 path 在 manifest 内必须唯一，producer 的 run/command 必须引用存在且相符的 RunResult。派生 artifact 的每个 parent/input 必须存在且 input hash 匹配；lineage 不得成环。声称可复现时必须存在可追溯的输入、producer command 和一致 hash；缺少其中任一项时 `is_reproducible` 不得为 true。

### LL-S010 — provenance blocker 必须限域

每个 provenance blocker 必须明确列出受影响 artifact、path、capability 与 distribution scope。它只阻塞交集范围，不得泛化为无关范围的全局失败；局部 provenance 成功也不得覆盖其他 artifact 或 distribution 的 unresolved 状态。范围为空、无法定位或相互冲突时进入 HUMAN_REVIEW。

### LL-S011 — HUMAN_REVIEW 只能由 human event 解除

进入 `HUMAN_REVIEW` 后，后续离开该状态的首个账本事件必须由 `actor_role=HUMAN_REVIEWER` 的真实人类主体产生，并引用人类裁决证据。executor、verifier、governor、模型重试、超时或新 testimony 均不得解除 HUMAN_REVIEW；缺少人类事件时状态必须保持 HUMAN_REVIEW 或转为 BLOCKED。

### LL-S012 — cleanup safety

CleanupDecision 仅在 artifact 非唯一或已完成可验证迁移、未被引用且 `reference_count=0`、owner 已知、retention 已到期、无 hold、provenance 已解决，并存在动作时有效且明确允许 `cleanup_delete` 的 grant 时，才可为 `DELETE`。任一事实为未知或互相冲突也禁止 DELETE。DELETE 前后 hash、恢复可行性与恢复证据必须闭合；唯一、未迁移、被引用、owner 未知、未到期、held、provenance 未解决或缺 grant 的候选必须 KEEP、ARCHIVE 或 HUMAN_REVIEW。

### LL-S013 — commit、merge 与 push 授权互不蕴含

`topic_commit`、`merge_local`、`push_remote` 必须分别找到在动作时有效、目标匹配且明确 ALLOW/满足条件的 operation grant。任一个 grant 或动作成功 MUST NOT 推导另两个动作获准；`fetch_remote` 与 `remote_mutation` 同样不蕴含 push 权限。未授权操作必须维持未执行状态并形成 blocker。

### LL-S014 — post-merge 必须使用新 run

合并后验证必须针对记录的 `merge_sha` 启动新的 invocation、attempt 与 run；该 run ID 不得等于任何 pre-merge executor 或 verifier run，`post_merge.tested_sha` 必须等于 `merge.merge_sha`。旧 run、旧 artifact 或仅重新解释旧结果不能满足 post-merge gate。

### LL-S015 — judge 变更只允许 shadow validation

run 内冻结 judge 的 ID/version/hash 不得改变。若 judge、测试、gate 或验收逻辑发生变化，必须创建新 judge 版本并在 shadow validation 中同时保留旧、新 judge 的结果与差异；新 judge 结果不得为修改它的 actor 自行放行，也不得追溯改写原 run 的结论。完成独立复核与 governor 裁决前，新版本只能是 shadow-only。

### LL-S016 — structure_only 不得晋级

本 bundle 的 `implementation_status` 必须保持 `MANUAL_ORCHESTRATED_LEDGER_ONLY`，TaskSpec、GovernorDecision、BranchExecutionLedger 与 Index 的 capability ceiling/current level 必须保持 `structure_only`。schema parse、文档存在、结构检查、提交或本地分数均不得晋级到更高 canonical capability level，也不得被表述为当前可运行 validator 或 executable loop。

### LL-S017 — topology-aware rollback closure

rollback 必须从 ledger 记录的 base/topic/merge SHA 与 parent topology 计算目标，使用单独授权的 `rollback_commit`，保留原历史并记录新的 rollback commit。完成后必须以新 run 验证 rollback commit，证明受影响引用与 worktree/branch 状态闭合；仅改状态标签、移动引用、删除 branch/worktree 或恢复文件内容均不足以令 `topology_closed=true`。失败时保持 ROLLING_BACK、BLOCKED 或 HUMAN_REVIEW，不得 CLOSED。

### LL-S018 — index 与 ledger 引用/hash 完整性

Index 的每个 object reference 必须指向存在的独立对象，object ID、schema ID 与内容 hash 必须匹配；最终成功信息不得以内联对象替代 required references。Ledger event sequence 必须从 1 严格单调递增、append-only，时间不回退，`previous_event_sha256` 必须链接前一事件 hash，current state/latest event/ledger hash 必须与末事件和 ledger 内容一致。所有 event evidence/grant、artifact parent/producer、verification、decision、cleanup 与 post-merge 引用必须可解析且 hash 一致；缺失、重复、悬空、循环或 hash 冲突均阻塞 CLOSED。

## 结构边界与裁决结果

JSON Schema 通过仅表示对象形状满足 Draft 2020-12 约束；上述不变量仍需人工编排的独立语义审查。语义结果只能记录为 `PASS`、`FAILED` 或 `INCONCLUSIVE`，其中 `INCONCLUSIVE` 必须阻塞 merge 与 `CLOSED`。本契约不构成 validator 实现，也不声称任何 loop 当前可执行。

## Impact Record

```yaml
change_id: v3-lcl-02-low-loop-schema-bundle
change_type: add
changed_node: TaskSpec, RunResult, ArtifactManifest, VerificationResult, GovernorDecision, AuthorizationGrant, CleanupDecision, BranchExecutionLedger, Index, semantic invariants
changed_edge: task -> grant -> run -> artifact -> verification -> governor -> commit/merge -> post-merge verification -> cleanup -> closure
evidence: nine Draft 2020-12 schema files and this semantic contract
direct_impact: establishes structure-only interchange shapes and cross-object invariants
downstream_impact: future validators and orchestrators must honor identities, grants, hashes, provenance, topology, and claim ceiling
required_regression: JSON parsing, unique schema IDs, resolvable relative refs, invariant ID uniqueness
data_validation: no runtime or real-site data; structure-only checks only
drift_risk: a future schema may weaken role separation, grant separation, cleanup safety, or capability ceiling
rollback: remove this newly added bundle only under separately authorized repository change control
owner_notes: no executable validator, loop, CLI, capability promotion, commit, merge, or remote action is included
```

## Cleanup Ledger

- removed: none
- kept_as_evidence: all nine schemas and this contract
- migrated_to_memory: not applicable; no runtime or site evidence was produced
- still_unverified: executable validation and orchestration are intentionally out of scope
- encryption_algorithm_graph: not applicable; no sign, token, encryption, or cryptographic implementation was introduced
