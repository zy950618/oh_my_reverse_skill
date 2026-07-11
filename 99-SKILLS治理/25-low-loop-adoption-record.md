---
record_id: LOW-LOOP-V3-ADOPTION-RECORD
adoption_status: CANDIDATE
operator_entry: false
base_sha: 6e2f2e5ed7a1006a8178e566215a07a586341e35
task_id: V3-LCL-01
implementation_status: MANUAL_ORCHESTRATED_LEDGER_ONLY
capability_level: structure_only
---

# Low-LOOP V3 采纳候选记录

## 1. 记录边界

本记录始于 `V3-LCL-01`，并以 append-only reconciliation 追踪后续已合并候选结构；它不是采纳决定、执行入口或可运行程序。V3 仍只能作为 adoption candidate 接受评估，不能由本记录自行采纳。

## 2. 用户授权快照

- 连续执行上限：最多 8 rounds 或 6 hours，先到者停止。
- Claude 可在 gates 通过后创建 local topic commits，并 local merge 到 `test`。
- `push_remote` 与其他 remote mutation：`DENY`。
- 每个已关闭 round 可在证据冻结、工作树 clean 且可安全删除时执行 `worktree remove` 和本地 `branch -d`。
- 用户对“exact old interrupted cleanup”的授权已执行完毕；该历史授权不延续、不复用，也不扩大本 LCL 权限。

本记录不声称上述可选动作在本 LCL 已发生；每项动作仍须满足对应 gate、范围和当前有效授权。

## 3. 来源与 hash

| source | sha256 | 状态 |
|---|---|---|
| `chatgpt_loop` | `65f70ed84ff61f2ec02cb5c6672e960b3abf308e450c72be43211eb1fcb53bc8` | hash observed；snapshot 在本 LCL 前已 byte-verified |
| `Claude/Codex draft` | `74969591cf90e6b93bf2397980c1c173432393e4f70609352c0989391d5513ec` | hash observed；snapshot 在本 LCL 前已 byte-verified |
| `audit` | `181ade17c507a0c6e9b3a3fcc9e788f6a1249eb98e295116bd0a60d3d3aa5aad` | hash observed；不声称存在 snapshot |

上述 hash 均为 observed；前两个 source snapshot 的 byte verification 发生在本 LCL 之前，audit 仅有 observed hash，本文不声称 audit 有 snapshot。这些材料仍是 ignored local evidence，不是已采纳仓库事实、operator 输入或独立验证结论；source migration 尚未完成，本 LCL 未提升其证据等级。

## 4. 迁移候选矩阵

下表只记录已合并候选结构的落点与实现程度。`IMPLEMENTED_CANDIDATE` 表示对应规范结构已经进入候选权威链，`PARTIAL_CANDIDATE` 表示只有结构或人工流程可用、运行实现仍缺失；两者都不表示 `ADOPTED`、migration complete 或可执行能力。

| ID | 主题 | destination | disposition |
|---|---|---|---|
| M-001 | local fact discovery | `24 §4, §6, §7`; semantic contract `LL-S001`, `LL-S002`, `LL-S007`; root operator「任务与信任边界」 | `IMPLEMENTED_CANDIDATE`：事实冻结、信任分类、owner inventory 与 provenance 已进入候选规范/契约；source migration 与独立验证仍待 final reconciliation |
| M-002 | integration/owner protection | `24 §1, §5, §9`; semantic contract `LL-S003`, `LL-S014`; root operator「任务与信任边界」「授权」 | `PARTIAL_CANDIDATE`：owner 保护、限域 blocker 和分授权已形成候选人工流程；安全执行集成未实现 |
| M-003 | role separation | `24 §2`; verification/governor schemas; root operator「当前能力边界」「Codex executor envelope」 | `IMPLEMENTED_CANDIDATE`：Claude/Codex 边界及 testimony 规则已对齐候选入口；actor-separated verifier 未实现 |
| M-004 | four status dimensions | `24 §3`; index/task/run/branch ledger schemas; semantic contract `LL-S001`, `LL-S004` | `IMPLEMENTED_CANDIDATE`：四维状态已进入候选 machine contract；当前能力仍固定为 manual/`structure_only` |
| M-005 | low-context budget | `24 §8`; TaskSpec schema; root operator「有界连续执行」「Codex executor envelope」 | `IMPLEMENTED_CANDIDATE`：round/time/token/path/action 边界已有候选字段和入口约束；自动预算执行器未实现 |
| M-006 | cross-session state | `24 §3, §7, §10`; index/artifact/branch ledger schemas; semantic contract `LL-S007`, `LL-S018`; root operator「跨会话恢复」 | `PARTIAL_CANDIDATE`：identity、hash、lineage 与恢复语义已结构化；持久 state store/recovery implementation 未实现 |
| M-007 | bounded continuous/anti-fake-loop | `24 §8`; TaskSpec/branch ledger schemas; semantic contract `LL-S009`; root operator「有界连续执行」 | `PARTIAL_CANDIDATE`：单 topic、预算和 repeated-blocker stop 已进入人工候选流程；完整 V3 runner 未实现 |
| M-008 | workflow close state | `24 §9`; index/branch ledger schemas; semantic contract `LL-S010`, `LL-S015`–`LL-S018`; root operator lifecycle | `PARTIAL_CANDIDATE`：`CLOSING`→`CLOSED` 顺序和引用约束已有候选 machine contract；原子 gate implementation 未实现 |
| M-009 | branch/worktree/Git | `24 §5, §9`; authorization/branch ledger schemas; semantic contract `LL-S005`, `LL-S013`–`LL-S017`; root operator lifecycle/authorization | `PARTIAL_CANDIDATE`：Git 生命周期及互不蕴含授权已结构化并进入人工入口；安全 Git executor 未实现 |
| M-010 | TaskSpec/Codex testimony | `24 §2, §4, §6`; TaskSpec/RunResult schemas; semantic contract `LL-S002`, `LL-S008`; root operator「Codex executor envelope」 | `IMPLEMENTED_CANDIDATE`：冻结 TaskSpec、fresh invocation 和 result testimony 已形成候选结构与直接入口约束 |
| M-011 | verifier/governor/artifacts | `24 §2, §4, §7`; artifact/verification/governor schemas; semantic contract `LL-S006`–`LL-S008`, `LL-S011`; root operator「当前能力边界」 | `PARTIAL_CANDIDATE`：artifact 谱系、verification 与 governor 决策已结构化；actor-separated verifier 仍未实现，当前仅 manual role-separated re-execution |
| M-012 | cleanup/retention | `24 §7, §9`; artifact/cleanup/branch ledger schemas; semantic contract `LL-S012`, `LL-S016`, `LL-S018`; root operator lifecycle | `PARTIAL_CANDIDATE`：retention、唯一证据保护和 cleanup decision 已结构化；自动 cleanup/recovery 未实现且删除仍需独立授权 |
| M-013 | remote/push separation | `24 §5`; AuthorizationGrant schema; semantic contract `LL-S005`; root operator「授权」 | `IMPLEMENTED_CANDIDATE`：fetch/push/remote mutation 与 commit/merge 已分权，push 保持默认 `DENY`；不表示任何 Git 动作已执行 |
| M-014 | stop/report | `24 §8, §10, §12`; TaskSpec/RunResult/branch ledger schemas; semantic contract `LL-S009`; root operator stop conditions/result testimony | `IMPLEMENTED_CANDIDATE`：重复 blocker、边界、漂移或证据不足的停止与报告已进入候选入口和 machine contract |

## 5. 历史材料

空 legacy package 与旧 `22/23` claims 仅作为历史记录。Codex 未将 owner root drafts 视为 authority；迁移事实由 Claude 冻结后写入 `TaskSpec`，Codex 仅使用这些 frozen facts，不自行把 owner drafts 的 claim 迁移为 V3 事实。

## 6. 采纳条件与当前 claim ceiling

V3 的标准、schemas、semantic contract、唯一 root operator、仓库 entries 与 routing 已作为候选结构收敛并纳入追踪；这只满足 candidate evaluation 的结构前提。正式采纳仍需完成 source migration、shadow validation、独立验证、治理批准与 final reconciliation，源材料删除也仍待单独决策。上述候选结构不得被解释为这些最终条件已经完成。

当前 claim ceiling 仅为：已追踪的 V3 候选权威链与 machine contracts 可供后续评估；`adoption_status=CANDIDATE`、`implementation_status=MANUAL_ORCHESTRATED_LEDGER_ONLY`、`capability_level=structure_only`。任何未来 executable CLI 均为 `NOT_IMPLEMENTED`、`NOT_RUNNABLE`，且仅由未来 roadmap 定义；本记录不定义或展示当前命令，也不声称任何 CLI 已执行。

## 7. Append-only reconciliation — V3-LCL-01..05

截至 2026-07-11，以下已合并 SHA 仅证明候选结构已进入当前仓库历史，不等于 adoption、source migration complete、运行实现或治理放行：

| LCL | merged SHA | 候选收敛结果 |
|---|---|---|
| `V3-LCL-01` | `b06beaa` | 候选标准与本 adoption record 建立 |
| `V3-LCL-02` | `639a3c3` | versioned schemas、index 与 semantic validation contract 建立 |
| `V3-LCL-03` | `6fc53bd` | 根目录唯一直接 operator entry 建立并链接候选权威链 |
| `V3-LCL-04` | `f035908` | Codex/Claude 仓库入口约束对齐候选 operator 与人工生命周期 |
| `V3-LCL-05` | `4ed97fa` | 触发、索引与路由表面对齐候选 Low-LOOP 入口 |

当前 capability ceiling 仍为 `MANUAL_ORCHESTRATED_LEDGER_ONLY` / `structure_only`。现有 `web_h5_loop_runner` 只提供既有业务 ledger 的 init/record/validate，不生成 V3 state package；secure executor、持久 state store、actor-separated verifier、自动 Git lifecycle 与 final adoption 均未实现。源材料删除、source migration 的最终确认、shadow validation、独立复核及最终 reconciliation 仍待完成；只有该最终 reconciliation 可以把状态改为 adopted。
