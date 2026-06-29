# oh_my_reverse_skill

Web/H5 逆向工程 SKILLS 总库。覆盖 Web/JS 逆向、爬虫接口化、WAF 风控证据治理、Loop Runner 执行账本、一致性验证、Skill 治理评测的完整工具链与流程。

一句话目标: 在授权范围内实现全站关键接口处理、加密/签名逆向和关键接口测试交付; 对 WAF/验证码/风控类状态只按真实接口证据声明能力,必要时引入人工参与协议。

## 快速开始

> 第一次来?按这个顺序看:

1. **[USAGE.md](./USAGE.md)** — 我想做 X,应该说什么(场景速查 + 典型对话)
2. **[INSTALL.md](./INSTALL.md)** — 一站式安装(Skills 软链 + CloakBrowser + hooks + 验证)
3. **[TRIGGERS.md](./TRIGGERS.md)** — 触发词速查表(中英双列,12 个 Skill 全覆盖)
4. **[CHERRY_STUDIO.md](./CHERRY_STUDIO.md)** — Cherry Studio / GUI 适配说明

进阶:

- **[CLAUDE.md](./CLAUDE.md)** — Claude 在本仓库的工作指南
- **[99-SKILLS治理/06-网页逆向标准规划.md](./99-SKILLS治理/06-网页逆向标准规划.md)** — 六阶段执行流程(Claude 视角)
- **[99-SKILLS治理/07-一致性验证规约.md](./99-SKILLS治理/07-一致性验证规约.md)** — fixtures + replay + diff 操作规约
- **[99-SKILLS治理/05-当前评分与回测结果.md](./99-SKILLS治理/05-当前评分与回测结果.md)** — 评分历史与版本变化

---

## 整合来源

本仓库整合了三处来源:

- GitHub 仓库名统一为 `oh_my_reverse_skill`（Web 业务流程 skill）
- 本机 `~/.claude/skills` 下的 Web/JS 原子工具与通用规范
- obsidian 笔记中的工作流文档、站点案例与验证码经验库
- 真实逆向 run/capture/replay 提炼后的脱敏经验库模板和通用结论

## 目录布局

```
oh_my_reverse_skill/
├── 1-业务流程层/   顶层入口，调度其他层
│   ├── website-314-api-delivery       新站点 → FastAPI 接口测试交付（Web 最常用入口，314 为可选本地基础框架分支）
│   ├── reverse-js-crawler             JS 逆向主流程
│   ├── imperva-waf-reese84            Imperva/Reese84/84 盾专攻
│   ├── skills-evaluation-governance   skill 评分/回测/治理
│   └── web-h5-loop-engineering        Loop Engineering 三角色闭环编排 + execution ledger
│
├── 2-JS逆向工具层/   被 1-业务流程层 调用的 Web 原子工具
│   ├── find-crypto-entry              定位 JS 加密参数生成入口
│   ├── ast-deobfuscate                Babel AST 解混淆
│   ├── env-patch                      浏览器 JS 在 Node 补环境
│   └── ai-reverse-skill-creator       创建/优化/评测逆向 skill
│
├── 4-通用规范层/
│   └── karpathy-guidelines            LLM 代码行为守则
│
├── 5-沉淀工具层/   接口稳定后的标准化沉淀
│   └── site-api-adapter               adapter.yaml / schema.json / runbook / prompt-router
│
├── 6-验证码逆向层/
│   └── captcha-service-delivery       验证码 provider 流程 / 站点绑定 / 实战复测 / 图谱回归
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
├── 验证码经验库/
│   ├── providers/                     reCAPTCHA / hCaptcha / Turnstile / 滑块 / 点选通用经验
│   └── domains/_example.com/          示例结构; 真实 domain 目录本地保留
│
└── tools/
    ├── sync_site_memory.py            手动同步 project memory → 站点经验库
    ├── web_h5_loop_runner.py          Loop Runner execution ledger 创建/追加/验证
    ├── web_h5_acceptance_report.py    并发/风控/UI一致性/freshness/metrics 验收报告
    ├── fixture_freshness_report.py    fixtures expired/review_pending/recent replay 新鲜度报告
    └── README.md                      tools 说明
```

## 安装方式

仓库为唯一来源。本机用软链把每个 skill 链回 `~/.claude/skills/`：

GUI / Cherry Studio 用户优先看 [CHERRY_STUDIO.md](./CHERRY_STUDIO.md)。CLI 用户继续使用下面的软链安装方式。

### Windows（PowerShell）

```powershell
# 业务流程层
foreach ($n in @('website-314-api-delivery','reverse-js-crawler','imperva-waf-reese84','skills-evaluation-governance','web-h5-loop-engineering')) {
  New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\$n" -Target "E:\SKILLS\oh_my_reverse_skill\1-业务流程层\$n"
}
# JS 工具层
foreach ($n in @('find-crypto-entry','ast-deobfuscate','env-patch','ai-reverse-skill-creator')) {
  New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\$n" -Target "E:\SKILLS\oh_my_reverse_skill\2-JS逆向工具层\$n"
}
# 通用规范
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\karpathy-guidelines" -Target "E:\SKILLS\oh_my_reverse_skill\4-通用规范层\karpathy-guidelines"
# 沉淀工具
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\site-api-adapter" -Target "E:\SKILLS\oh_my_reverse_skill\5-沉淀工具层\site-api-adapter"
# 验证码逆向层
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\captcha-service-delivery" -Target "E:\SKILLS\oh_my_reverse_skill\6-验证码逆向层\captcha-service-delivery"
```

### macOS / Linux（bash）

```bash
REPO="$HOME/SKILLS/oh_my_reverse_skill"   # 改成你本地实际路径
DST="$HOME/.claude/skills"
mkdir -p "$DST"

# 业务流程层
for n in website-314-api-delivery reverse-js-crawler imperva-waf-reese84 skills-evaluation-governance web-h5-loop-engineering; do
  ln -snf "$REPO/1-业务流程层/$n" "$DST/$n"
done
# JS 工具层
for n in find-crypto-entry ast-deobfuscate env-patch ai-reverse-skill-creator; do
  ln -snf "$REPO/2-JS逆向工具层/$n" "$DST/$n"
done
# 通用规范
ln -snf "$REPO/4-通用规范层/karpathy-guidelines" "$DST/karpathy-guidelines"
# 沉淀工具
ln -snf "$REPO/5-沉淀工具层/site-api-adapter" "$DST/site-api-adapter"
# 验证码逆向层
ln -snf "$REPO/6-验证码逆向层/captcha-service-delivery" "$DST/captcha-service-delivery"
```

> `ln -snf`：`-s` 符号链接，`-n` 不解引用已存在目标，`-f` 强制覆盖。和 Windows junction 等效。

## 标准入口

收到「网页逆向 XXX 网站 / 实现某站点纯接口 / FastAPI 接口测试交付」类请求时，先看 `99-SKILLS治理/06-网页逆向标准规划.md`，按规划走，不要直接跳进 reverse-js-crawler 写代码。
默认先交付可测试的 Python/FastAPI 接口；接口全部验证成功后，再人工确认是否接入本地基础框架。只有用户确认“是”并选择框架时，才进入 314 或其他本地基础框架改写分支。
开始抓包前先读 `逆向工程经验库/domains/<domain>/reverse-memory.md` 和 `站点经验库/<domain>/known-failures.md`；没有 reverse-memory 时先从模板建立,再分配新的 `run_id`。
完成验证后按 `99-SKILLS治理/17-交付收尾清理与加密算法图谱规约.md` 做最终清理;涉及 sign/token/加密时,补 `encryption-algorithm-graph.md`。

正式经验库只收真实接口测试后的精炼结论: 已完成确认、未完成确认、踩坑点、下次不再重复处理的错误路径、脱敏字段含义和回归要求。研发阶段的 HAR、完整请求响应、token/cookie、订单参数、临时脚本和交付包留在本地临时项目库或交付目录,不进入 GitHub。

## 一体化路径

实际任务按这条路径闭环:

| 阶段 | 实际落点 | 写什么 | 进入 GitHub |
|---|---|---|---|
| 1. 任务规划 | `99-SKILLS治理/06-网页逆向标准规划.md` | 目标、scope、domain/market/stage、证据口径、风险红线 | 是 |
| 2. 研发探索 | 本地临时项目库、`交付项目/<domain>/`、抓包目录 | HAR、完整 req/resp、临时脚本、调试记录、失败尝试 | 否 |
| 3. 真实测试确认 | 本地 run 账本、validation ledger、diff/replay 输出 | 已完成确认、未完成确认、真实接口结果、阻塞原因 | 否,只沉淀摘要 |
| 4. 正式经验沉淀 | `站点经验库/<domain>/`、`逆向工程经验库/domains/<domain>/`、`验证码经验库/domains/<domain>/` | 脱敏结论、踩坑点、下次排查顺序、JSON Pointer、状态机、回归要求 | 真实 domain 默认否 |
| 5. 知识图谱 | `站点经验库/<domain>/knowledge-graph.md` | domain/market/stage/endpoint/field/state/protection/implementation/eval 节点和边 | 真实 domain 默认否 |
| 6. 影响回归 | `站点经验库/<domain>/impact-regression.md` | direct/downstream impact、必跑回归、数据校验、漂移风险 | 真实 domain 默认否 |
| 7. SKILLS 升级 | `1-业务流程层/`、`2-JS逆向工具层/`、`6-验证码逆向层/`、`99-SKILLS治理/`、`evals/` | 经过成功经验验证的通用规则或负例门槛 | 是 |
| 8. 收尾清理 | `99-SKILLS治理/17-交付收尾清理与加密算法图谱规约.md`、`逆向工程经验库/domains/<domain>/encryption-algorithm-graph.md` | cleanup ledger、算法图谱、删除/保留/迁移说明 | 规则是;真实 domain 默认否 |

最后必须能回答: 哪些接口真实通过,哪些没有通过,哪些路径下次不用再试,哪些节点/边写进知识图谱,哪些回归必须重跑,哪些材料只能本地保留。
