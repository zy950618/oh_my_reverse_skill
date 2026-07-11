---
operator_entry: false
roadmap_status: CANDIDATE
implementation_status: MANUAL_ORCHESTRATED_LEDGER_ONLY
capability_level: structure_only
---

# Low-LOOP V3 非操作实现路线图

本路线图描述从当前 `MANUAL_ORCHESTRATED_LEDGER_ONLY` 演进到可验证本地实现的依赖顺序。它不是用户操作入口，不证明 adoption 完成，也不授权 Git、远端或外部系统 mutation。每阶段只有在 promotion evidence 被独立复核后才能提升；否则维持其 capability ceiling。

可搜索术语覆盖：`schema validator`、`Codex connector`、`replay`、`MCP`、`crypto graph`、`reproducibility`。这些术语仅定位未来阶段，不表示对应实现已存在。

## 统一阶段约束

所有阶段都必须：fail-closed；使用本地 synthetic fixture；区分 observed/derived/assumed/unverified；保持 append-only 审计；不处理真实 secret、登录、支付、PII、WAF 绕过、隐匿或指纹伪造。Provenance blocker 只冻结受影响的 path、artifact、capability 或 distribution，除非证据证明影响范围更大。

## Phase 0 — Adoption

- **依赖：** 无。
- **交付：** candidate 标准、adoption 决策记录、版本/取代关系、canonical 链接与明确 owner。
- **检查：** 正例验证引用闭合；负例拒绝缺失版本或 owner；对抗例拒绝用 draft/旧日志冒充 adopted standard。
- **非目标：** runner、执行器、Git 自动化。
- **能力上限：** `structure_only`、manual orchestration。
- **回滚：** 撤销 adoption 指针并保留决策记录，不删除证据。
- **提升证据：** 批准者、时间、范围、版本、理由及引用 hashes 可独立复核。

## Phase 1 — Schema validator 与 append-only state

- **依赖：** Phase 0。
- **交付：** versioned schemas、canonical serialization/hash、严格 validator、append-only events、派生 current state。
- **检查：** 正例可重放同 hash；负例拒绝 unknown/missing/invalid transition；对抗例拒绝篡改、截断、乱序和旧 run 注入。
- **非目标：** 运行外部进程或 Git mutation。
- **能力上限：** validated ledger only。
- **回滚：** 停用新 schema writer，以旧 reader 只读保留事件。
- **提升证据：** golden vectors、迁移报告、tamper/ordering 测试与独立 hash 复算。

## Phase 2 — Identity、grants 与 trust boundary

- **依赖：** Phase 1。
- **交付：** actor/run/worktree identity；分离的 commit/merge/rollback/remove/delete/fetch/push grants；expiry/scope；不可信输入边界和 owner inventory。
- **检查：** 正例仅允许匹配 scope 的有效 grant；负例拒绝过期或隐含授权；对抗例拒绝 prompt injection、身份混淆、owner dirty/untracked 覆盖和 grant replay。
- **非目标：** 实际执行 Git 动作。
- **能力上限：** authorization decisions only。
- **回滚：** 全部 mutation grant fail-closed，保留读取和审计。
- **提升证据：** authorization matrix、owner 冲突 fixture、注入测试和审计事件。

## Phase 3 — Artifact、retention 与最小恢复

- **依赖：** Phase 1、Phase 2。
- **交付：** content-addressed artifact manifest、lineage、retention/ownership/provenance 字段、hash-valid checkpoint 与最小恢复器。
- **检查：** 正例恢复最近有效 checkpoint；负例拒绝缺失 lineage/hash；对抗例拒绝 artifact substitution、路径穿越、symlink escape 和唯一证据删除。
- **非目标：** 重跑命令、自动 cleanup。
- **能力上限：** artifact-backed read/recover only。
- **回滚：** 切回只读 manifest，冻结疑似 artifact。
- **提升证据：** corruption fixtures、恢复轨迹、retention 决策及独立 hash 验证。

## Phase 4 — Secure argv executor 与具体 Codex connector

- **依赖：** Phase 2、Phase 3。
- **交付：** argv-only subprocess core、cwd/env/time/output limits、stdout/stderr capture、observed exit/signal/timeout，以及一次一 fresh invocation 的具体 Codex connector。
- **检查：** 正例受限 fixture 产生可寻址结果；负例拒绝 shell string、越界 cwd/env 和未授权 path；对抗例覆盖参数注入、输出洪泛、超时、进程树逃逸与伪造 testimony。
- **非目标：** 接受 Codex 自报为验证结论；Git mutation。
- **能力上限：** bounded local execution。
- **回滚：** 禁用 connector，保留 ledger/artifacts 为只读。
- **提升证据：** 平台矩阵、资源限制测试、真实 observed process facts 与 connector isolation proof。

## Phase 5 — Replay vertical slice

- **依赖：** Phase 4。
- **交付：** 单个 synthetic request/response replay 的 TaskSpec→executor→result 最小纵切，run isolation 与 deterministic fixture。
- **检查：** 正例稳定复现限定输出；负例在 stale/missing input 时失败；对抗例拒绝跨 run artifact、旧 token、旧 script id 和 cache 污染。
- **非目标：** 真实站点、登录、并发或通用采集能力。
- **能力上限：** one local replay fixture。
- **回滚：** 移除纵切注册但保留失败证据与 fixture hash。
- **提升证据：** fresh-worktree 重复运行、隔离证明、输入输出 hashes 和明确 scope。

## Phase 6 — Artifact proof

- **依赖：** Phase 5。
- **交付：** command→stream→output→assertion 的完整 lineage；size/hash/tool version；每项 acceptance 的 artifact binding。
- **检查：** 正例每个 assertion 可回溯；负例拒绝 missing/unknown/weak-signal-only；对抗例拒绝换包、截断日志、mtime/path-exists 假成功和自报 exit。
- **非目标：** 决定 merge。
- **能力上限：** artifact-bound execution proof。
- **回滚：** 降级为 inconclusive，不保留 pass 声明。
- **提升证据：** proof bundle、独立复算、tamper negatives 与 assertion coverage。

## Phase 7 — Acceptance、Verifier 与 Governor

- **依赖：** Phase 6。
- **交付：** frozen acceptance；独立 Verifier；policy Governor；`INCONCLUSIVE` fail-closed；gate 自修改隔离。
- **检查：** 正例独立复跑一致；负例拒绝 Codex testimony-only 和缺失 artifact；对抗例拒绝阈值放宽、validator 自证、fixture 删除、角色串谋和旧 proof 重用。
- **非目标：** 执行 commit/merge。
- **能力上限：** `READY_TO_MERGE` recommendation only。
- **回滚：** 恢复 frozen gate，新增 gate 仅 shadow。
- **提升证据：** 正/负/对抗套件、角色独立性记录、policy version/hash 和逐项判定。

## Phase 8 — Git lifecycle

- **依赖：** Phase 2、Phase 7。
- **交付：** fresh topic worktree、diff allowlist audit、分授权 commit/merge/rollback/remove/delete、fresh post-merge run、safe branch deletion 和 base-drift detection。
- **检查：** 正例在显式 grant 下完成本地闭环；负例拒绝缺 grant、dirty worktree、未关闭依赖；对抗例覆盖 TOCTOU base drift、owner untracked、merge 后失败、未合并 commit 和远端 mutation。
- **非目标：** 默认 push、force delete、自动处理 owner 文件。
- **能力上限：** authorized local Git lifecycle；remote mutation denied。
- **回滚：** 停在可审计状态；rollback 必须另授权且保留关联证据。
- **提升证据：** commit/merge/post-merge SHAs、grant IDs、cleanliness proof、rollback drill 与 Git facts 复核。

## Phase 9 — Local parity 与 HAR providers

- **依赖：** Phase 6、Phase 7。
- **交付：** 明确能力声明的 local runtime provider 与 sanitized HAR provider；统一 request/response model；provider/version identity。
- **检查：** 正例在固定 fixture 上 parity；负例拒绝缺字段、未知 provider 和漂移；对抗例覆盖 HAR secret 泄漏、顺序歧义、编码差异、重定向和 cache 串扰。
- **非目标：** 真实账号、挑战绕过、生产稳定性或跨 market 泛化。
- **能力上限：** specified local/HAR fixtures only。
- **回滚：** quarantine 单一 provider，不冻结无关 provider 或 artifact。
- **提升证据：** parity matrix、sanitization report、provider hashes 与 mismatch 解释。

## Phase 10 — MCP identity、schema 与 health

- **依赖：** Phase 2、Phase 9。
- **交付：** server/tool identity、capability allowlist、input/output schema hashes、health/readiness、version drift fail-closed。
- **检查：** 正例锁定身份/schema 后调用 fixture；负例拒绝 unknown/unhealthy/drift；对抗例覆盖同名替换、schema downgrade、能力夸报和响应注入。
- **非目标：** 自动信任新 server 或由 MCP 扩权。
- **能力上限：** identity-locked local MCP capability。
- **回滚：** 禁用受影响 server/capability，其他范围照常审计。
- **提升证据：** attestation、schema snapshots、health traces、drift 与 impersonation tests。

## Phase 11 — Static/dynamic crypto graph

- **依赖：** Phase 9、Phase 10。
- **交付：** typed nodes/edges；static/dynamic evidence provenance；input/intermediate/output hashes；mismatch localization；unknown edge 表达。
- **检查：** 正例 synthetic algorithm 链定位一致；负例拒绝由 final output 猜整链；对抗例覆盖 derived 冒充 observed、hook drift、nondeterminism、secret/risk-token 输入和未知许可证实现。
- **非目标：** WAF/challenge defeat、credential extraction、真实 risk token 或外部代码洗白。
- **能力上限：** synthetic/local evidence graph only。
- **回滚：** quarantine 受影响 node/edge/artifact/capability/distribution，不全局冻结无关图。
- **提升证据：** 静动态图对齐 fixture、首个 mismatch proof、provenance/license matrix 和独立复算。

## Phase 12 — Cleanup、recovery 与 reproducibility

- **依赖：** Phase 3、Phase 8、Phase 11。
- **交付：** ownership/TTL cleanup plan；仅可复现 temp 的删除；crash recovery；跨会话 hash-valid resume；reproducibility package。
- **检查：** 正例新 worktree 可限定复现；负例拒绝删唯一/被引用/未知 owner 证据；对抗例覆盖半写事件、merged-unverified、CLOSED 重做、branch/worktree dirty、symlink/race 和同 blocker 循环。
- **非目标：** `git clean/reset`、强删 branch、打包 secret/profile、盲目 rerun。
- **能力上限：** scoped local recovery and reproducibility。
- **回滚：** 停止 apply cleanup，保留 plan/archive；恢复器降级人工复核。
- **提升证据：** crash matrix、resume traces、cleanup dry-run/apply 对照、fresh-worktree package replay 和残留清单。

## Phase 13 — Final local fixture 与 future CLI

- **依赖：** Phase 0–12 全部 promotion evidence 通过。
- **交付：** 单一 synthetic fixture 的完整本地 LCL：TaskSpec→fresh worktree→Codex→diff audit→Verifier→Governor→授权 commit/merge→fresh post-merge→evidence freeze→safe cleanup→`CLOSED`；同时冻结未来 CLI 契约。
- **检查：** 正例完整闭环且 hashes 可复核；负例分别注入执行、验证、授权、merge、post-merge 和 cleanup 失败；对抗例覆盖 prompt injection、base drift、旧 artifact、伪造身份、grant replay、owner 冲突和 provenance scope 扩张。
- **非目标：** 真实第三方站点成功、生产稳定、远端发布、并发、登录、支付或规避能力。
- **能力上限：** `LOW_LOOP_INTEGRATION_PASS`，仅限指定 local fixture、SHA、provider 与工具版本。
- **回滚：** 撤销 capability promotion，保留完整 ledger/proof；任何 post-merge failure 不得标记 `CLOSED`。
- **提升证据：** 独立端到端 run、负例/对抗报告、Git SHAs、grant chain、artifact bundle、cleanup ledger、repro package 与 capability 声明审计。

### Future CLI command contracts

以下名称仅是未来接口契约，全部为 **NOT_IMPLEMENTED**、**NOT_RUNNABLE**，不得作为当前仓库命令执行：

| 概念 | 未来契约边界 | 当前状态 |
|---|---|---|
| `start` | 创建经验证的 TaskSpec、identity 与 fresh state；不隐含 Git 授权 | NOT_IMPLEMENTED / NOT_RUNNABLE |
| `resume` | 从最后 hash-valid state 继续；不盲目重跑或重做 CLOSED | NOT_IMPLEMENTED / NOT_RUNNABLE |
| `status` | 只读核验 ledger、artifact hashes 与 Git facts | NOT_IMPLEMENTED / NOT_RUNNABLE |
| `run` | 执行一个已授权的 bounded transition；不等于连续自治 | NOT_IMPLEMENTED / NOT_RUNNABLE |
| `cleanup` | 规划/处理仅可复现 temp；删除需独立授权与证据 | NOT_IMPLEMENTED / NOT_RUNNABLE |
| `rollback` | 依据独立 grant 执行限定回滚并追加审计 | NOT_IMPLEMENTED / NOT_RUNNABLE |
| `push` | 远端 mutation；默认 DENY，必须单独、显式、限域授权 | NOT_IMPLEMENTED / NOT_RUNNABLE |

这些概念只有通过 Phase 13 的本地 fixture 和安全审计后才可进入实现候选；文档出现不构成可运行性或 adoption。
