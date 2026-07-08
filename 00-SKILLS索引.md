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

## 有效加载策略

active `SKILL.md` 数量以 `python3 tools/governance/score_skills.py --repo .` 和 release score 输出为准；不等于所有 Skill 都应直接响应用户自然语言。默认按三层加载：

| 层级 | Skill | 触发规则 |
|---|---|---|
| 对外入口 | `website-314-api-delivery` | 用户要完整纯接口、FastAPI 接口测试、服务化、314/本地框架接入 |
| 对外入口 | `reverse-js-crawler` | 用户要单站点/单链路的页面侦察、接口还原、JS sign/token、采集脚本 |
| 对外入口 | `web-h5-loop-engineering` | 用户明确要求 LOOP/闭环/多 agent/反复验证，或前序任务因证据不完整需要循环修正 |
| 对外入口 | `web-h5-loop-engineering` + `skills-evaluation-governance` | 用户要求公开靶场训练、public-range-evidence、用实战验证进化 SKILLS |
| 对外入口 | `skills-evaluation-governance` | 用户在治理 SKILLS 本身：评分、触发收敛、准入、漂移、eval |
| 条件升级 | `imperva-waf-reese84` | 仅当观察到 Imperva/Reese84/Incapsula/x-d-token 等明确证据，或用户明确点名 |
| 条件升级 | `authorized-target-adapter` | 仅当真实目标已声明授权边界、allowed_hosts、rate limit、stop condition、kill switch 和业务数据断言时使用 |
| 条件升级 | `site-api-adapter` | 仅当接口已经稳定且用户要 adapter/schema/runbook/prompt-router |
| 内部工具 | `find-crypto-entry` / `ast-deobfuscate` / `env-patch` / `js-page-runtime-parity` | 由入口 skill 调度；只有用户明确提出原子任务时才直接使用 |
| 内部治理 | `ai-reverse-skill-creator` / `karpathy-guidelines` | 用于创建/修改 skill 或编码纪律，不作为 Web/H5 逆向入口 |

收敛原则：先选一个对外入口；只有出现明确证据或用户明确点名时才升级到专项 skill；工具层不能和业务入口抢触发。

## 路由优先级与关系边界

1. `web-h5-loop-engineering` 优先级最高: 仅当用户明确要求 LOOP、闭环、多 agent、三角色验证、反复复测、执行账本,或前序任务因证据/验收不完整需要循环修正时触发。
2. `website-314-api-delivery`: 用户要完整新站点纯接口、FastAPI 接口测试交付、服务化、314/本地基础框架接入、查询/加车/生单/支付链路时触发。它可以调度 `reverse-js-crawler`,但不被单点 JS 逆向抢入口。
3. `reverse-js-crawler`: 用户要聚焦单站点/单链路页面侦察、接口还原、JS sign/token、请求复现或采集脚本时触发。完整服务化交付和明确 LOOP 不从这里开始。
4. `karpathy-guidelines`: 基础工程规范/编码质量规范,不作为业务入口,只在其他 Skill 进入实现、评审、重构或验证时作为辅助 checklist。
7. `browser-fingerprint-surface-lab`: browser fingerprint surface inventory、surface hash、profile consistency 和 drift 观察。
8. `fingerprint-block-reason-diagnostics`: 基于 surface/report/响应/session 证据做 block reason 归因,不修改 fingerprint surface。

## 层次划分

| 层 | 目录 | 角色 |
|---|---|---|
| 1 | `1-业务流程层/` | 顶层入口，按用户需求调度 2/5 层 |
| 2 | `2-JS逆向工具层/` | Web/JS 原子工具，被 1 层调用 |
| 4 | `4-通用规范层/` | 行为守则、代码纪律 |
| 5 | `5-沉淀工具层/` | 接口稳定后的标准化沉淀（被 1 层调用） |
| 7 | `7-指纹风控层/` | fingerprint surface 观察和 block reason 归因，不做 concealment/falsification |
| 99 | `99-SKILLS治理/` | 生命周期/分类/评分/漂移/准入 |
| - | `站点经验库/` | 站点案例（按 domain/market/locale 拆分） |
| - | `逆向工程经验库/` | run/capture/replay、旧新证据、工具失败和复测经验 |
| - | `tools/` | 仓库辅助脚本（sync_site_memory.py 等） |

## 全部 active skill（数量以评分工具为准）

active skill 数量以 `python3 tools/governance/score_skills.py --repo .` 和 release score 输出为准。

### 1-业务流程层

| Skill | 适用场景 | 主要触发词 |
|---|---|---|
| `website-314-api-delivery` | 新网站 → 纯接口 → FastAPI 接口测试交付 → 可选接入本地基础框架（314 是一个分支） | 新站点接入、纯接口、FastAPI接口测试、314 基础框架、加解密全部实现 |
| `reverse-js-crawler` | 页面侦察、接口识别、签名/token 还原、采集脚本交付 | JS逆向、接口还原、加密参数、补环境、批量采集 |
| `imperva-waf-reese84` | Imperva/Reese84/84 盾/x-d-token/WAF challenge | 84盾、Reese84逆向、Incapsula、WAF挑战、风控token |
| `skills-evaluation-governance` | 给技能评分、补 eval、回测、漂移测试、版本治理 | SKILLS评分、Skill Bench、新增Skill准入、回测、漂移 |
| `web-h5-loop-engineering` | Web/H5 逆向需要闭环、多角色验证、执行账本和验收报告 | LOOP、闭环处理、多 agent、反复抓包复测、执行账本 |
| `authorized-target-adapter` | 真实目标授权边界、allowed_hosts、rate limit、stop condition、kill switch 和业务数据断言 | authorized target、scope contract、business-data assertions |

### 2-JS逆向工具层（默认内部工具）

| Skill | 适用场景 |
|---|---|
| `find-crypto-entry` | 定位 JS 加密参数生成入口（函数位置 + 调用链） |
| `ast-deobfuscate` | Babel AST 解混淆（字符串解密、控制流还原、死代码删除） |
| `env-patch` | 浏览器加密 JS 在 Node.js 中运行（补环境） |
| `js-page-runtime-parity` | 对授权目标或本地 lab 做 Browser/Node/V8/PageRuntime 输出一致性验证 |
| `ai-reverse-skill-creator` | 创建/优化/评测逆向类 skill |

### 4-通用规范层

| Skill | 适用场景 |
|---|---|
| `karpathy-guidelines` | 基础工程规范 / 编码质量规范。只作为其他执行类 Skill 的辅助 checklist,不作为业务任务入口 |

### 5-沉淀工具层

| Skill | 适用场景 |
|---|---|
| `site-api-adapter` | 把单站点稳定的逆向结果标准化为 adapter.yaml / schema.json / runbook / prompt-router（接口稳定后才用，默认被 1 层调用） |
### 7-指纹风控层（observation/lab）

| Skill | 适用场景 |
|---|---|
| `browser-fingerprint-surface-lab` | browser fingerprint surface inventory、surface hash、profile consistency 和 drift 观察 |
| `fingerprint-block-reason-diagnostics` | 基于 surface/report/响应/session 证据做 block reason 归因，不修改 fingerprint surface |

## Source of truth

- 触发词和路由矩阵: [TRIGGERS.md](./TRIGGERS.md)
- 用户调用方式: [USAGE.md](./USAGE.md)
- 安装与软链: [INSTALL.md](./INSTALL.md)
- Claude Code 执行流程和边界: [CLAUDE.md](./CLAUDE.md)
