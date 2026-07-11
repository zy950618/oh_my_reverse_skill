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

本记录是 `V3-LCL-01` 的非 operator 采纳候选，不是采纳决定、执行入口或可运行程序。本任务只能起草规范与 adoption candidate，不能自行采纳 V3。

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

下表全部为 `CANDIDATE`，仅标识目标位置与候选处置；没有任何一项声称 migration complete。

| ID | 主题 | destination | disposition |
|---|---|---|---|
| M-001 | local fact discovery | `24 §4, §6, §7` | `CANDIDATE`：冻结本地事实、信任类与 provenance，待迁移验证 |
| M-002 | integration/owner protection | `24 §1, §5, §9` | `CANDIDATE`：以权威层级、显式授权和原子关闭保护 owner，未完成集成 |
| M-003 | role separation | `24 §2` | `CANDIDATE`：Claude 治理、Codex executor/testimony，待 operator 对齐 |
| M-004 | four status dimensions | `24 §3` | `CANDIDATE`：分离 workflow/run/implementation/capability，待 schema 化 |
| M-005 | low-context budget | `24 §8` | `CANDIDATE`：round/time/token/path/action 有界，待 ledger 字段落地 |
| M-006 | cross-session state | `24 §3, §7, §10` | `CANDIDATE`：以 identity、hash 与 lineage 恢复，待持久状态实现 |
| M-007 | bounded continuous/anti-fake-loop | `24 §8` | `CANDIDATE`：单 LCL 单 topic、同 blocker 两次停止，待 runner 实现 |
| M-008 | workflow close state | `24 §9` | `CANDIDATE`：原子 `CLOSING`→`CLOSED`，待 gate 与 ledger 实现 |
| M-009 | branch/worktree/Git | `24 §5, §9` | `CANDIDATE`：拆分授权并限定 clean worktree 与安全 `branch -d`，待集成 |
| M-010 | TaskSpec/Codex testimony | `24 §2, §4, §6` | `CANDIDATE`：冻结 TaskSpec，Codex 文本仅 testimony，待结构化 |
| M-011 | verifier/governor/artifacts | `24 §2, §4, §7` | `CANDIDATE`：独立验证、governor 裁决和 artifact 谱系，待实现 |
| M-012 | cleanup/retention | `24 §7, §9` | `CANDIDATE`：只清可再生临时物并保留唯一/关闭证据，待策略落地 |
| M-013 | remote/push separation | `24 §5` | `CANDIDATE`：fetch/push/remote mutation 分权，commit/merge/push 不互相蕴含 |
| M-014 | stop/report | `24 §8, §10, §12` | `CANDIDATE`：重复 blocker、边界或证据不足时停止并报告，待 operator 落地 |

## 5. 历史材料

空 legacy package 与旧 `22/23` claims 仅作为历史记录。Codex 未将 owner root drafts 视为 authority；迁移事实由 Claude 冻结后写入 `TaskSpec`，Codex 仅使用这些 frozen facts，不自行把 owner drafts 的 claim 迁移为 V3 事实。

## 6. 采纳条件与当前 claim ceiling

V3 的正式采纳需要后续 LCL 完成 schemas、operator、唯一 entry 的收敛，并完成 source migration、shadow validation、独立验证和治理批准。上述条件均不因本候选记录而视为完成。

当前 claim ceiling 仅为：两份文档的候选结构可供后续审议；`adoption_status=CANDIDATE`、`implementation_status=MANUAL_ORCHESTRATED_LEDGER_ONLY`、`capability_level=structure_only`。任何未来 executable CLI 均为 `NOT_IMPLEMENTED`、`NOT_RUNNABLE`，且仅由未来 roadmap 定义；本记录不定义或展示当前命令，也不声称任何 CLI 已执行。
