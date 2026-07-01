---
title: 新增 SKILL 评分回测准入
tags:
  - skills
  - scorecard
  - backtest
  - governance
---

# 新增 SKILL 评分回测准入

每个新的 Skill 进入 `可用的SKILLS/` 前，必须先评分和回测。

## 准入结论

| 分数 | 状态 | 处理 |
|---:|---|---|
| 90-100 | 可用稳定 | 可进入可用目录，后续做漂移测试 |
| 80-89 | 可用基线 | 可进入，但必须标记待补 eval/回测 |
| 70-79 | 候选 | 只能放候选区，不进入可用 |
| 50-69 | 笔记/模板 | 需要重写成 Skill |
| <50 | 原始材料 | 只能作为 reference 来源 |

## 硬性门槛

新 Skill 至少满足：

- `SKILL.md` 存在。
- frontmatter 有 `name` 和 `description`。
- `description` 同时描述能力和触发场景。
- `agents/openai.yaml` 存在。
- `references/` 至少 2 个文件。
- `evals/` 至少 3 个用例。
- 至少 1 个负例 eval。
- 至少 1 个边界/回归 eval。
- 至少 1 个事实证据/反泛化/并发隔离类行为 eval。
- 若 Skill 会改端点/字段/请求头/状态/保护/实现/eval,必须说明如何更新知识图谱和影响回归记录。
- `references/governance.md` 存在。
- quick_validate 通过。

## 评分维度

唯一评分口径见 `99-SKILLS治理/skill-score-rubric.yaml`。当前临时验收标准采用
`score_skills.py / ci_gate.py` 的 100 分结构:

| 类别 | 分值 | 子项 |
|---|---:|---|
| structure | 25 | `SKILL.md`、frontmatter、`agents/openai.yaml`、references、eval layout、governance reference、maintainability |
| operational | 25 | trigger clarity、workflow behavior、eval quality、routing boundaries、evidence write-back、real-task metrics |
| consistency | 30 | active fixtures、active snapshot count、active expiry、active recent report、consistency rate |
| drift | 20 | drift policy、regression coverage、version/change log、historical metrics |

旧 8 维不再作为独立评分规则；它们只作为以上四类的子项解释。

执行行为评分必须检查 AI 自理能力：

- 事实证据：关键结论是否区分 observed / derived / assumed / unverified。
- 反泛化：是否阻止单接口、单 market、单 session 成功被写成全链路成功。
- 并发隔离：是否要求并发阶梯、session/cache 隔离和停止条件。
- 图谱更新：是否要求改动后更新节点、边、影响面和必跑回归。
- 证据新鲜度：是否要求 run/capture/replay、旧新数据隔离和经验写回。
- 收尾清理：是否按 `17-交付收尾清理与加密算法图谱规约.md` 要求验证后清理临时/历史/废弃物,涉及加密时补算法细节图。

## Karpathy 风格检查

这些来自 Karpathy 风格编码准则，但用于评测 Skill 行为质量：

- 不默默假设：Skill 要要求分类、证据和边界。
- 不虚假完成：Skill 要求结论有证据等级,未验证项必须显式列出。
- 不以点概面：Skill 要求范围账本,不跨 market/stage/session 泛化。
- 不乱并发：Skill 要求单线程基线、并发阶梯、会话隔离和失败率记录。
- 不过度复杂：Skill 不要吞掉不属于自己的任务。
- 精准处理：一个 Skill 只解决一类问题。
- 目标驱动：必须定义可验证成功标准。

## 回测要求

新增 Skill 时必须跑：

- 自身 eval。
- 至少 1 个相邻 Skill 的负例。
- 至少 1 个历史失败回归例。
- 至少 1 个 AI 行为负例:无证据结论/以点概面/未验证并发/旧新数据混用/缺少收尾清理 五选一。
- 至少 1 个影响回归负例:改端点/字段/请求头/指纹但不更新图谱或不跑受影响回归。
- 涉及加密/sign/token 的 Skill 至少 1 个算法图谱负例:只有代码/聊天结论,没有整体加密算法细节图。
- quick_validate。
- 本地结构评分脚本。

如果接 GitHub CI，则 PR 必须跑 Skill Bench。

## 新增 Skill 记录

每次新增 Skill 后，在 `05-当前评分与回测结果.md` 追加：

- Skill 名称。
- 版本号。
- 新增原因。
- 评分。
- 回测结果。
- 未覆盖风险。
- 后续补强项。

