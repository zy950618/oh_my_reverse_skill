# oh_my_reverse_skill — AGENTS.md

本仓库是 Web/H5 逆向工程 SKILLS 总库,11 个 skill 分 5 个分层。本文件是 OpenAI Codex CLI 的入口约定。

## 接到逆向任务时

1. 读 `99-SKILLS治理/06-网页逆向标准规划.md` 输出 6 阶段规划
2. 按 `00-SKILLS索引.md` 选 skill
3. 进入实现前 Read `4-通用规范层/karpathy-guidelines/SKILL.md` 确认 4 原则
4. 输出结论前 Read `99-SKILLS治理/11-AI事实证据规约.md`，区分 observed / derived / assumed / unverified
5. 扩展范围或跨 market/stage/session 前 Read `99-SKILLS治理/12-反泛化与任务收敛规约.md`
6. 涉及批量/并发/指纹/会话/cache 前 Read `99-SKILLS治理/13-并发指纹与会话隔离规约.md`
7. 每次更新端点/字段/状态/保护/实现/eval 前后 Read `99-SKILLS治理/14-知识图谱行程与关联规约.md`
8. 每次改动后 Read `99-SKILLS治理/15-AI变更风险与回归校验规约.md` 写影响面和必跑回归
9. 涉及基础逆向、浏览器清空、抓包复测、旧/新数据、多轮比对、验证码/token/session freshness 时,先读 `99-SKILLS治理/16-实战复测与证据新鲜度规约.md` 和 `逆向工程经验库/domains/<domain>/reverse-memory.md`
10. 遇运行时问题(断点/时间/cookie/TLS 指纹/风控/接口变更)Read `99-SKILLS治理/10-逆向运行时常见问题.md`
11. 完成前 Read `99-SKILLS治理/17-交付收尾清理与加密算法图谱规约.md`,写 cleanup ledger 和加密算法细节图
12. 涉及证据不足、验证失败、拒答边界、人工复核、监控、错误纠正或历史遗留时 Read `99-SKILLS治理/18-证据验证拒答人工复核与监控规约.md`
13. 完成前跑 `python tools/verify_delivery.py --domain <domain>` 自验

## 强制约束

- 真实扣款不在自动化环境跑,除非用户明示授权
- 不把"评分高"等同于"任务真实成功"
- 不把一次失败硬编码成只适配一个站点的规则
- 不把 assumed / unverified 写成 observed 事实
- 不把单接口、单 market、单 session 成功泛化成全链路成功
- 不声称支持并发,除非有并发阶梯记录和会话隔离证据
- 不改端点/字段/请求头/指纹/实现/eval 而不更新知识图谱和影响回归记录
- 不把旧 HAR/旧 token/旧 scriptId/旧浏览器 profile 当成本次 observed 事实
- 不重新开荒:已有 reverse-memory / site-memory / captcha-memory 时必须先读再抓包
- 不把已验证完成后的临时测试文件、旧历史数据、废代码、废注释留在交付面;清理前必须先迁移必要证据
- 涉及 sign/token/加密算法时,必须产出整体加密算法细节图
- 不在证据不足、验证失败或用户要求越界时硬交付;必须拒答/收缩范围并给安全替代方案
- 不删除唯一证据或用户改动;清理错误代码前必须迁移 failure evidence 并写错误纠正账本
- 不把辱骂性前缀、人格化称谓或情绪化口头禅写入强制输出规范
- 任务结束按 `CLAUDE.md` 阶段 E 沉淀、阶段 F 一致性验证和阶段 G 清理/算法图收尾

## 关键工具

- `tools/replayer/snapshot_replay.py`: replay 验证
- `tools/replayer/snapshot_diff.py`: 字段 diff
- `tools/replayer/schema_alert.py`: 接口版本变更告警
- `tools/replayer/consistency_report.py`: 一致性报告
- `tools/verify_delivery.py`: 完成度 6 维自验
- `tools/post_task_reminder.py`: Stop hook 沉淀提醒
- `tools/sync_site_memory.py`: 跨项目同步 site memory
- `tools/ci_gate.py`: CI 评分阈值
- `1-业务流程层/skills-evaluation-governance/scripts/score_skills.py`: skill 评分

## 仓库分层

| 层 | 目录 | 角色 |
|---|---|---|
| 1 | `1-业务流程层/` | 顶层入口(4 个 skill) |
| 2 | `2-JS逆向工具层/` | Web/JS 原子工具(4 个) |
| 4 | `4-通用规范层/` | 基础层规范(karpathy-guidelines) |
| 5 | `5-沉淀工具层/` | 接口稳定后的标准化(site-api-adapter) |
| 6 | `6-验证码逆向层/` | 验证码/验证服务逆向(captcha-service-delivery) |
| 99 | `99-SKILLS治理/` | 生命周期/分类/评分/漂移/准入/运行时方法论 |

完整规则见 `CLAUDE.md`。
