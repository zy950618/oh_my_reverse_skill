# oh_my_reverse_skill

Web/H5 逆向工程 SKILLS 总库。覆盖 Web/JS 逆向、爬虫接口化、WAF 风控证据治理、Loop Runner 执行账本、一致性验证、Skill 治理评测的完整工具链与流程。


## 快速开始

> 第一次来?按这个顺序看:

1. **[USAGE.md](./USAGE.md)** — 我想做 X,应该说什么(场景速查 + 典型对话)
2. **[INSTALL.md](./INSTALL.md)** — 一站式安装(Skills 软链 + CloakBrowser + hooks + 验证)
3. **[TRIGGERS.md](./TRIGGERS.md)** — 触发词速查表(中英双列,active Skill 范围以评分工具校验结果为准)
4. **[CHERRY_STUDIO.md](./CHERRY_STUDIO.md)** — Cherry Studio / GUI 适配说明

进阶:

- **[CLAUDE.md](./CLAUDE.md)** — Claude 在本仓库的工作指南
- **[99-SKILLS治理/06-网页逆向标准规划.md](./99-SKILLS治理/06-网页逆向标准规划.md)** — 六阶段执行流程(Claude 视角)
- **[99-SKILLS治理/07-一致性验证规约.md](./99-SKILLS治理/07-一致性验证规约.md)** — fixtures + replay + diff 操作规约
- **[99-SKILLS治理/05-当前评分与回测结果.md](./99-SKILLS治理/05-当前评分与回测结果.md)** — 当前评分口径

---

## 整合来源

本仓库整合了三处来源:

- GitHub 仓库名统一为 `oh_my_reverse_skill`（Web 业务流程 skill）
- 本机 `~/.claude/skills` 下的 Web/JS 原子工具与通用规范
- 真实逆向 run/capture/replay 提炼后的脱敏经验库模板和通用结论

## 目录布局

```
oh_my_reverse_skill/
├── 1-业务流程层/   顶层入口，调度其他层
│   ├── website-314-api-delivery       新站点 → FastAPI 接口测试交付（Web 最常用入口，314 为可选本地基础框架分支）
│   ├── reverse-js-crawler             JS 逆向主流程
│   ├── imperva-waf-reese84            Imperva/Reese84/84 盾专攻
│   ├── skills-evaluation-governance   skill 评分/回测/治理
│   ├── web-h5-loop-engineering        Loop Engineering 三角色闭环编排 + execution ledger
│   └── authorized-target-adapter       授权目标 scope / allowed_hosts / stop condition / 业务数据断言
│
├── 2-JS逆向工具层/   被 1-业务流程层 调用的 Web 原子工具
│   ├── find-crypto-entry              定位 JS 加密参数生成入口
│   ├── ast-deobfuscate                Babel AST 解混淆
│   ├── env-patch                      浏览器 JS 在 Node 补环境
│   ├── js-page-runtime-parity          Browser/Node/V8/PageRuntime 输出一致性验证
│   └── ai-reverse-skill-creator       创建/优化/评测逆向 skill
│
├── 4-通用规范层/
│   └── karpathy-guidelines            LLM 代码行为守则
│
├── 5-沉淀工具层/   接口稳定后的标准化沉淀
│   └── site-api-adapter               adapter.yaml / schema.json / runbook / prompt-router
│
│
├── 7-指纹风控层/
│   ├── browser-fingerprint-surface-lab       fingerprint surface inventory / drift 观察
│   └── fingerprint-block-reason-diagnostics  block reason 归因,不修改 fingerprint surface
│
├── 99-SKILLS治理/
│   ├── 01-生命周期.md
│   ├── 02-新网站接入分类.md
│   ├── 03-测试评分漂移.md
│   ├── 04-新增SKILL评分回测准入.md
│   ├── 05-当前评分与回测结果.md
│   └── 06-网页逆向标准规划.md          ← meta 规划入口
│
├── 站点经验库/
│   └── _templates/                    domain/market/locale/currency/stage 多维拆分模板; 真实 domain 目录本地保留
│
├── 逆向工程经验库/
│   ├── _templates/                    run/capture/replay、old-vs-new、工具失败、加密算法图、交付清理模板
│   └── domains/_example.com/          示例结构; 真实 domain 目录本地保留
│
└── tools/
    ├── sync_site_memory.py            手动同步 project memory → 站点经验库
    ├── web_h5_loop_runner.py          Loop Runner execution ledger 创建/追加/验证
    ├── web_h5_acceptance_report.py    并发/风控/UI一致性/freshness/metrics 验收报告
    ├── fixture_freshness_report.py    fixtures expired/review-needed/recent replay 新鲜度报告
    └── README.md                      tools 说明
```

## 安装方式

安装、软链、hooks 和本地验证只维护在 [INSTALL.md](./INSTALL.md)。

## 快速入口

- 用户怎么调用: [USAGE.md](./USAGE.md)
- 触发词和路由矩阵: [TRIGGERS.md](./TRIGGERS.md)
- Skill 列表与职责: [00-SKILLS索引.md](./00-SKILLS索引.md)
- Claude Code 执行流程和边界: [CLAUDE.md](./CLAUDE.md)
- active Skill 数量来源: `python3 tools/score_skills.py --repo .`

长链路逆向任务先按 `99-SKILLS治理/06-网页逆向标准规划.md` 输出规划；真实交付结论必须有证据、范围账本、回归记录和收尾清理。
