---
title: oh_my_reverse_skill 索引
tags:
  - codex
  - skills
  - reverse
  - skill-bench
  - governance
---

# oh_my_reverse_skill 索引

本仓库是 Web/H5 逆向工程 SKILLS 总库，分层组织，仓库为唯一来源，通过 Windows junction 安装到 `~/.claude/skills/`。

## 层次划分

| 层 | 目录 | 角色 |
|---|---|---|
| 1 | `1-业务流程层/` | 顶层入口，按用户需求调度 2/5 层 |
| 2 | `2-JS逆向工具层/` | Web/JS 原子工具，被 1 层调用 |
| 4 | `4-通用规范层/` | 行为守则、代码纪律 |
| 5 | `5-沉淀工具层/` | 接口稳定后的标准化沉淀（被 1 层调用） |
| 6 | `6-验证码逆向层/` | 验证码/验证服务的 provider 流程、站点绑定、实战复测、图谱和回归 |
| 99 | `99-SKILLS治理/` | 生命周期/分类/评分/漂移/准入 |
| - | `站点经验库/` | 站点案例（按 domain/market/locale 拆分） |
| - | `逆向工程经验库/` | run/capture/replay、旧新证据、工具失败和复测经验 |
| - | `验证码经验库/` | 验证码 provider 与站点绑定经验库 |
| - | `tools/` | 仓库辅助脚本（sync_site_memory.py 等） |

## 全部 12 个 skill

### 1-业务流程层（4 个）

| Skill | 适用场景 | 主要触发词 |
|---|---|---|
| `website-314-api-delivery` | 新网站 → 纯接口 → FastAPI 接口测试交付 → 可选接入本地基础框架（314 是一个分支） | 新站点接入、纯接口、FastAPI接口测试、314 基础框架、加解密全部实现 |
| `reverse-js-crawler` | 页面侦察、接口识别、签名/token 还原、采集脚本交付 | JS逆向、接口还原、加密参数、补环境、批量采集 |
| `imperva-waf-reese84` | Imperva/Reese84/84 盾/x-d-token/WAF challenge | 84盾、Reese84逆向、Incapsula、WAF挑战、风控token |
| `skills-evaluation-governance` | 给技能评分、补 eval、回测、漂移测试、版本治理 | SKILLS评分、Skill Bench、新增Skill准入、回测、漂移 |

### 2-JS逆向工具层（4 个）

| Skill | 适用场景 |
|---|---|
| `find-crypto-entry` | 定位 JS 加密参数生成入口（函数位置 + 调用链） |
| `ast-deobfuscate` | Babel AST 解混淆（字符串解密、控制流还原、死代码删除） |
| `env-patch` | 浏览器加密 JS 在 Node.js 中运行（补环境） |
| `ai-reverse-skill-creator` | 创建/优化/评测逆向类 skill |

### 4-通用规范层（1 个）

| Skill | 适用场景 |
|---|---|
| `karpathy-guidelines` | LLM 编码行为守则（最小改动、显式假设、可验证成功标准） |

### 5-沉淀工具层（1 个）

| Skill | 适用场景 |
|---|---|
| `site-api-adapter` | 把单站点稳定的逆向结果标准化为 adapter.yaml / schema.json / runbook / prompt-router（接口稳定后才用，被 1 层调用） |

### 6-验证码逆向层（1 个）

| Skill | 适用场景 |
|---|---|
| `captcha-service-delivery` | reCAPTCHA / hCaptcha / Turnstile / 滑块 / 点选等验证码服务的 provider 流程、站点绑定、token 状态、真实抓包复测、图谱和影响回归 |

## 调度顺序（典型场景）

### 网页逆向（最常用）

```
website-314-api-delivery（Web 总控）
  ├─ reverse-js-crawler         主链路
  │    ├─ find-crypto-entry     定位加密
  │    ├─ ast-deobfuscate       看不懂的 JS
  │    └─ env-patch             浏览器 JS → Node
  ├─ imperva-waf-reese84        遇到 84盾/Incapsula
  ├─ captcha-service-delivery   遇到验证码/滑块/点选/Turnstile/reCAPTCHA
  ├─ 5-沉淀工具层/site-api-adapter   接口稳定后做 adapter
  └─ skills-evaluation-governance    任务结束做评分
```

完整规划见 `99-SKILLS治理/06-网页逆向标准规划.md`。

## 新网站接入入口

任何新网站接口交付任务都从 `website-314-api-delivery` 开始。默认先做 Python/FastAPI 接口测试交付；接口全部成功后，再人工确认是否加入本地基础框架。典型输入：

```text
目标网站：https://www.example.com/
目标：纯接口实现查询、加车、生单、支付
要求：加解密全部实现，先提供 FastAPI 接口测试；全部成功后询问是否接入本地基础框架，314 作为可选分支
```

## 长期进化闭环

每次真实任务结束后必须问：

1. 有没有新触发词？
2. 有没有新失败类型？
3. 有没有新分类规则？
4. 有没有新加解密或反爬模式？
5. 有没有应该加入 eval 的场景？
6. 是否需要升级版本号？

沉淀路径：

```
真实任务
  → 归类（02-新网站接入分类.md）
  → 执行（按 06-网页逆向标准规划.md）
  → 更新基础逆向经验（逆向工程经验库/<domain>/reverse-memory.md）
  → 记录失败点（站点经验库/<domain>/known-failures.md）
  → 验证码任务同步 验证码经验库/providers 与 domains
  → 更新 references
  → 增加 eval
  → 评分（skills-evaluation-governance）
  → 版本升级
  → 漂移测试（03-测试评分漂移.md）
```

## 官方 CI 跑分

本地目录已有 `SKILL.md` 和 `evals/`，结构上具备被 Skill Bench 评测的能力。但要正式跑分还需要：

- 把 skill 镜像到一个 Git 仓库（本仓库 oh_my_reverse_skill 已具备）
- 仓库可见路径，例如 `skills/<skill-name>/`（本仓库用分层目录，必要时再镜像一份扁平结构给 CI）
- GitHub Actions 配置模型 API key secret（如 `ANTHROPIC_API_KEY`）
- PR 触发 + 定时触发的 Skill Bench workflow

## 治理文档

- `99-SKILLS治理/01-生命周期.md`
- `99-SKILLS治理/02-新网站接入分类.md`
- `99-SKILLS治理/03-测试评分漂移.md`
- `99-SKILLS治理/04-新增SKILL评分回测准入.md`
- `99-SKILLS治理/05-当前评分与回测结果.md`
- `99-SKILLS治理/06-网页逆向标准规划.md`（meta 规划入口）
- `99-SKILLS治理/11-AI事实证据规约.md`（防虚假结论）
- `99-SKILLS治理/12-反泛化与任务收敛规约.md`（防以点概面和发散）
- `99-SKILLS治理/13-并发指纹与会话隔离规约.md`（并发/session/cache/指纹边界）
- `99-SKILLS治理/14-知识图谱行程与关联规约.md`（节点、边、关联更新）
- `99-SKILLS治理/15-AI变更风险与回归校验规约.md`（改动影响面和必跑回归）
- `99-SKILLS治理/16-实战复测与证据新鲜度规约.md`（清空浏览器、抓包、多轮对照、旧新数据隔离）
- `99-SKILLS治理/17-交付收尾清理与加密算法图谱规约.md`（最终清理、删除临时/历史/废代码、整体加密算法细节图）
- `99-SKILLS治理/18-证据验证拒答人工复核与监控规约.md`（证据门槛、验证账本、拒答、人审、监控、错误纠正和历史遗留）

## 新 Skill 准入

```
标准结构
  → quick_validate
  → 本地评分脚本
  → 正例/负例/历史回归回测
  → 更新评分结果
  → 进入对应分层目录
  → mklink /J 到 ~/.claude/skills/
```

评分参考 `skills-evaluation-governance/references/scorecard-rubric.md`，吸收 Karpathy 行为守则（4-通用规范层/karpathy-guidelines）。

---

## 2026-06-26 追加：Web/H5 Loop Engineering

新增业务流程层 skill：

| Skill | 适用场景 | 主要触发词 |
|---|---|---|
| `web-h5-loop-engineering` | Web/H5 逆向任务需要 3 个或多个角色/agent 闭环推进，并产出 execution ledger、acceptance report、fixture freshness 和 metrics，直到证据通过、停止或进入人工复核 | Loop Engineering、LOOP、闭环处理、多 agent 逆向、三个 agent 验证、循环执行验证修正、反复抓包复测、自动化验证闭环、爬虫 LOOP、真实 Loop Runner、执行账本、结果量化沉淀 |

典型闭环：

```text
目标/Scope
  -> Loop Runner: execution ledger
  -> Executor: 侦察、抓包、JS 入口、接口复现
  -> Verifier: clean-state retest、acceptance report、replay、diff、schema、并发阶梯、UI/API parity
  -> Governor: 事实等级、反泛化、session/cache 隔离、fixture freshness、metrics、图谱、影响回归、cleanup
  -> Stop / Human Review / Next Iteration
```

本 skill 只适用于 Web/H5，不引入非 Web/H5 能力，不把本地 loop gate 通过写成真实站点成功。风控处理只记录授权范围内的并发隔离、退避、停止、session retirement、fresh replay 和人工复核，不沉淀绕过策略。
