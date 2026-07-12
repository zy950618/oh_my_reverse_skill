# oh_my_reverse_skill — AGENTS.md

本仓库是 Web/H5 逆向工程 SKILLS 总库，active skill inventory 以根目录 `skills-manifest.json` 为单一来源；数量用 `python3 tools/skills_manifest.py summary` 校验。本文件是 OpenAI Codex CLI 的入口约定。

## 接到逆向任务时

1. 读 `99-SKILLS治理/06-网页逆向标准规划.md` 输出 6 阶段规划
2. 按 `00-SKILLS索引.md` 选 skill
   - 路由优先级: 用户明确要求 Loop Engineering、闭环处理、多 agent 逆向、三角色验证、反复验证或 execution ledger 时,优先选 `1-业务流程层/web-h5-loop-engineering`
   - 用户要求完整新站点纯接口、FastAPI 接口测试交付、服务化、314/本地基础框架接入时,选 `1-业务流程层/website-314-api-delivery`
   - 用户要求聚焦单链路 JS 逆向、接口还原、加密参数、采集脚本或请求复现时,选 `1-业务流程层/reverse-js-crawler`
   - `4-通用规范层/karpathy-guidelines` 只是基础工程规范,只能作为其他 Skill 执行时的辅助规范,不得作为 Web/H5/challenge/WAF/业务任务主入口
   - fingerprint surface inventory 走 `7-指纹风控层/browser-fingerprint-surface-lab`; block reason 归因走 `7-指纹风控层/fingerprint-block-reason-diagnostics`
3. 进入实现前 Read `4-通用规范层/karpathy-guidelines/SKILL.md` 确认 4 原则
4. 输出结论前 Read `99-SKILLS治理/11-AI事实证据规约.md`，区分 observed / derived / assumed / unverified
5. 扩展范围或跨 market/stage/session 前 Read `99-SKILLS治理/12-反泛化与任务收敛规约.md`
6. 涉及批量/并发/指纹/会话/cache 前 Read `99-SKILLS治理/13-并发指纹与会话隔离规约.md`
7. 每次更新端点/字段/状态/保护/实现/eval 前后 Read `99-SKILLS治理/14-知识图谱行程与关联规约.md`
8. 每次改动后 Read `99-SKILLS治理/15-AI变更风险与回归校验规约.md` 写影响面和必跑回归
10. 遇运行时问题(断点/时间/cookie/TLS 指纹/风控/接口变更)Read `99-SKILLS治理/10-逆向运行时常见问题.md`
11. 完成前 Read `99-SKILLS治理/17-交付收尾清理与加密算法图谱规约.md`,写 cleanup ledger 和加密算法细节图
12. 涉及证据不足、验证失败、拒答边界、人工复核、监控、错误纠正或历史遗留时 Read `99-SKILLS治理/18-证据验证拒答人工复核与监控规约.md`
13. 完成前跑 `python3 tools/web_h5/verify_delivery.py --domain <domain>` 自验

## 强制约束

- 真实扣款不在自动化环境跑,除非用户明示授权
- 不把"评分高"等同于"任务真实成功"
- 不把项目交付代码、adapter、demo、临时复测脚本写进 SKILLS 能力层;交付项目只能作为交付文件/交付包管理
- 不把项目交付物和项目经验库混在一起;经验库只记录沉淀后的结论、失败模式、证据摘要和回归要求
- 不把 blocked / negative baseline / adapter-only / protected response 经验升级为可复用 SKILLS 能力;只有真实成功并完成回归的经验库条目才能参与 SKILLS 正向评分和能力泛化
- 不把一次失败硬编码成只适配一个站点的规则
- 不把 assumed / unverified 写成 observed 事实
- 不把单接口、单 market、单 session 成功泛化成全链路成功
- 不声称支持并发,除非有并发阶梯记录和会话隔离证据
- 不改端点/字段/请求头/指纹/实现/eval 而不更新知识图谱和影响回归记录
- 不把旧 HAR/旧 token/旧 scriptId/旧浏览器 profile 当成本次 observed 事实
- 不重新开荒:已有 reverse-memory / site-memory / challenge-memory 时必须先读再抓包
- 不把已验证完成后的临时测试文件、旧历史数据、废代码、废注释留在交付面;清理前必须先迁移必要证据
- 涉及 sign/token/加密算法时,必须产出整体加密算法细节图
- 不在证据不足、验证失败或用户要求越界时硬交付;必须拒答/收缩范围并给安全替代方案
- 不删除唯一证据或用户改动;清理错误代码前必须迁移 failure evidence 并写错误纠正账本
- 不把辱骂性前缀、人格化称谓或情绪化口头禅写入强制输出规范
- 任务结束按 `CLAUDE.md` 阶段 E 沉淀、阶段 F 一致性验证和阶段 G 清理/算法图收尾

## Source of truth

- 触发词与路由矩阵: `TRIGGERS.md`
- Active inventory / topology / install / CI: `skills-manifest.json`
- Skill 列表与职责: `00-SKILLS索引.md`
- 安装与软链: `INSTALL.md`
- Claude Code 执行流程和边界: `CLAUDE.md`

Codex review 只报告 blocking / non-blocking findings；不得把评分通过、结构通过或本地 lab 通过包装成真实站点成功。
