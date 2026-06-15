# oh_my_reverse_skill

Web/H5 逆向工程 SKILLS 总库。覆盖 Web/JS 逆向、爬虫接口化、WAF 风控对抗、一致性验证、Skill 治理评测的完整工具链与流程。

## 快速开始

> 第一次来?按这个顺序看:

1. **[USAGE.md](./USAGE.md)** — 我想做 X,应该说什么(场景速查 + 典型对话)
2. **[INSTALL.md](./INSTALL.md)** — 一站式安装(Skills 软链 + CloakBrowser + hooks + 验证)
3. **[TRIGGERS.md](./TRIGGERS.md)** — 触发词速查表(中英双列,11 个 Skill 全覆盖)

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
- 真实逆向 run/capture/replay 经验库

## 目录布局

```
oh_my_reverse_skill/
├── 1-业务流程层/   顶层入口，调度其他层
│   ├── website-314-api-delivery       新站点 → 314 接口交付（Web 最常用入口）
│   ├── reverse-js-crawler             JS 逆向主流程
│   ├── imperva-waf-reese84            Imperva/Reese84/84 盾专攻
│   └── skills-evaluation-governance   skill 评分/回测/治理
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
│   ├── _templates/                    （domain/market/locale/currency/stage 多维拆分模板）
│   └── thaiairways.com/               含 案例原稿/ 子目录
│
├── 逆向工程经验库/
│   ├── _templates/                    run/capture/replay、old-vs-new、工具失败、加密算法图、交付清理模板
│   └── domains/                       按 domain 记录 reverse-memory
│
├── 验证码经验库/
│   ├── providers/                     reCAPTCHA / hCaptcha / Turnstile / 滑块 / 点选通用经验
│   └── domains/                       站点验证码绑定与实战复测记录
│
└── tools/
    ├── sync_site_memory.py            手动同步 project memory → 站点经验库
    └── README.md                      tools 说明
```

## 安装方式

仓库为唯一来源。本机用软链把每个 skill 链回 `~/.claude/skills/`：

### Windows（PowerShell）

```powershell
# 业务流程层
foreach ($n in @('website-314-api-delivery','reverse-js-crawler','imperva-waf-reese84','skills-evaluation-governance')) {
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
for n in website-314-api-delivery reverse-js-crawler imperva-waf-reese84 skills-evaluation-governance; do
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

收到「网页逆向 XXX 网站 / 实现某站点纯接口」类请求时，先看 `99-SKILLS治理/06-网页逆向标准规划.md`，按规划走，不要直接跳进 reverse-js-crawler 写代码。
开始抓包前先读 `逆向工程经验库/domains/<domain>/reverse-memory.md` 和 `站点经验库/<domain>/known-failures.md`；没有 reverse-memory 时先从模板建立,再分配新的 `run_id`。
完成验证后按 `99-SKILLS治理/17-交付收尾清理与加密算法图谱规约.md` 做最终清理;涉及 sign/token/加密时,补 `encryption-algorithm-graph.md`。
