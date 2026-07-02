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

当前仓库保留 12 个 `SKILL.md`，但不等于 12 个都应直接响应用户自然语言。默认按三层加载：

| 层级 | Skill | 触发规则 |
|---|---|---|
| 对外入口 | `website-314-api-delivery` | 用户要完整纯接口、FastAPI 接口测试、服务化、314/本地框架接入 |
| 对外入口 | `reverse-js-crawler` | 用户要单站点/单链路的页面侦察、接口还原、JS sign/token、采集脚本 |
| 对外入口 | `web-h5-loop-engineering` | 用户明确要求 LOOP/闭环/多 agent/反复验证，或前序任务因证据不完整需要循环修正 |
| 对外入口 | `web-h5-loop-engineering` + `skills-evaluation-governance` | 用户要求公开靶场训练、public-range-evidence、用实战验证进化 SKILLS |
| 对外入口 | `skills-evaluation-governance` | 用户在治理 SKILLS 本身：评分、触发收敛、准入、漂移、eval |
| 条件升级 | `imperva-waf-reese84` | 仅当观察到 Imperva/Reese84/Incapsula/x-d-token 等明确证据，或用户明确点名 |
| 条件升级 | `captcha-service-delivery` | 仅当观察到 CAPTCHA/verification-service 证据，或用户明确点名 provider/sitekey/challenge |
| 条件升级 | `site-api-adapter` | 仅当接口已经稳定且用户要 adapter/schema/runbook/prompt-router |
| 内部工具 | `find-crypto-entry` / `ast-deobfuscate` / `env-patch` | 由入口 skill 调度；只有用户明确提出原子任务时才直接使用 |
| 内部治理 | `ai-reverse-skill-creator` / `karpathy-guidelines` | 用于创建/修改 skill 或编码纪律，不作为 Web/H5 逆向入口 |

收敛原则：先选一个对外入口；只有出现明确证据或用户明确点名时才升级到专项 skill；工具层不能和业务入口抢触发。

## 路由优先级与关系边界

1. `web-h5-loop-engineering` 优先级最高: 仅当用户明确要求 LOOP、闭环、多 agent、三角色验证、反复复测、执行账本,或前序任务因证据/验收不完整需要循环修正时触发。
2. `website-314-api-delivery`: 用户要完整新站点纯接口、FastAPI 接口测试交付、服务化、314/本地基础框架接入、查询/加车/生单/支付链路时触发。它可以调度 `reverse-js-crawler`,但不被单点 JS 逆向抢入口。
3. `reverse-js-crawler`: 用户要聚焦单站点/单链路页面侦察、接口还原、JS sign/token、请求复现或采集脚本时触发。完整服务化交付和明确 LOOP 不从这里开始。
4. `karpathy-guidelines`: 基础工程规范/编码质量规范,不作为业务入口,只在其他 Skill 进入实现、评审、重构或验证时作为辅助 checklist。
5. `captcha-open-source-model-stack`: CAPTCHA 本地/开源模型栈、数据集到模型路线、训练和评测选择。只限授权、本地、实验室、研究、评测环境。
6. `captcha-model-action-e2e`: 已有模型预测后的动作回放、失败复测、promotion gate 和指标归档。它不负责模型栈选择。
7. `browser-fingerprint-surface-lab`: browser fingerprint surface inventory、surface hash、profile consistency 和 drift 观察。
8. `fingerprint-block-reason-diagnostics`: 基于 surface/report/响应/session 证据做 block reason 归因,不修改 fingerprint surface。

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

### 1-业务流程层（5 个）

| Skill | 适用场景 | 主要触发词 |
|---|---|---|
| `website-314-api-delivery` | 新网站 → 纯接口 → FastAPI 接口测试交付 → 可选接入本地基础框架（314 是一个分支） | 新站点接入、纯接口、FastAPI接口测试、314 基础框架、加解密全部实现 |
| `reverse-js-crawler` | 页面侦察、接口识别、签名/token 还原、采集脚本交付 | JS逆向、接口还原、加密参数、补环境、批量采集 |
| `imperva-waf-reese84` | Imperva/Reese84/84 盾/x-d-token/WAF challenge | 84盾、Reese84逆向、Incapsula、WAF挑战、风控token |
| `skills-evaluation-governance` | 给技能评分、补 eval、回测、漂移测试、版本治理 | SKILLS评分、Skill Bench、新增Skill准入、回测、漂移 |
| `web-h5-loop-engineering` | Web/H5 逆向需要闭环、多角色验证、执行账本和验收报告 | LOOP、闭环处理、多 agent、反复抓包复测、执行账本 |

### 2-JS逆向工具层（4 个，默认内部工具）

| Skill | 适用场景 |
|---|---|
| `find-crypto-entry` | 定位 JS 加密参数生成入口（函数位置 + 调用链） |
| `ast-deobfuscate` | Babel AST 解混淆（字符串解密、控制流还原、死代码删除） |
| `env-patch` | 浏览器加密 JS 在 Node.js 中运行（补环境） |
| `ai-reverse-skill-creator` | 创建/优化/评测逆向类 skill |

### 4-通用规范层（1 个）

| Skill | 适用场景 |
|---|---|
| `karpathy-guidelines` | 基础工程规范 / 编码质量规范。只作为其他执行类 Skill 的辅助 checklist,不作为业务任务入口 |

### 5-沉淀工具层（1 个）

| Skill | 适用场景 |
|---|---|
| `site-api-adapter` | 把单站点稳定的逆向结果标准化为 adapter.yaml / schema.json / runbook / prompt-router（接口稳定后才用，默认被 1 层调用） |

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

公开靶场训练 / SKILLS 实战进化按同一闭环执行，但只能使用
`public-range-evidence/_allowlist.yaml` 中允许的 target 和 mode。每轮至少产出
`public-range-evidence/<target_id>/<run_id>.json`、Loop Runner ledger、acceptance
report 和验证命令结果。只有 direct interface accepted 加 repeat direct interface
accepted 的最终业务 JSON/data 证据能进入 `positive_allowed`；验证码/WAF/provider
testing keys 和 browser-only 结果只能进入负例、边界或 memory。

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

## Web/H5 Loop Engineering

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

## Phase 3 CAPTCHA Algorithm Skills

Phase 3 adds local/authorized CAPTCHA algorithm training skills. These skills can produce local algorithm metrics, failure samples, localhost action replay evidence, evals, and experience cards. They do not prove third-party CAPTCHA/WAF positive capability unless Phase 2.1 final business API and server-side ledger assertions also pass.

- `6-验证码逆向层/captcha-open-source-model-stack`: local/open-source model family selection, dataset-to-model routing, training and benchmark planning. It does not run action replay or third-party challenge automation.
- `6-验证码逆向层/captcha-model-action-e2e`: scoped action replay, failure replay, promotion gate and metrics archival after model predictions exist. It does not choose model families.
- `6-验证码逆向层/captcha-visual-recognition-lab`: text/slider/rotate/click/icon/multi-image visual recognition lab.
- `6-验证码逆向层/captcha-image-dataset-governance`: synthetic and authorized dataset labels, splits, provenance, and failure-sample feedback.
- `6-验证码逆向层/captcha-algorithm-benchmark`: per-challenge metrics and failure-case accounting.
- `6-验证码逆向层/captcha-action-planner`: localhost or authorized action replay from recognition results.
- `6-验证码逆向层/captcha-provider-diagnostics`: provider/state/verify-vs-business diagnostics only.
- `7-指纹风控层/fingerprint-block-reason-diagnostics`: fingerprint block reason diagnostics, no evasion.
- `1-业务流程层/authorized-target-adapter`: scope, allowed hosts, rate limits, stop conditions, redaction, and business-data gates for authorized real targets.

Phase 3 local lab: `public-range-labs/captcha-vision-lab/`.
Tools: `captcha_vision_dataset_generator.py`, `captcha_vision_baseline_solver.py`, `captcha_vision_benchmark.py`, `captcha_action_replay_lab.py`.

Capability boundary: local benchmark and localhost action replay may be recorded as local lab evidence, but public-range evidence remains `memory_only` or another non-positive status unless `business_data_status=DATA_ASSERTION_PASS`.

## Phase 3.4 Runtime And Fingerprint Lab

Phase 3.4 adds authorized runtime parity and observation-only fingerprint diagnostics.

- `2-JS逆向工具层/js-page-runtime-parity`: Browser/Node/V8/PageRuntime signature fixture parity, environment contract, runtime diff, and regression fixture.
- `7-指纹风控层/browser-fingerprint-surface-lab`: browser fingerprint surface inventory, surface hash, profile consistency, and risk-state attribution without stealth or spoofing.
- `public-range-labs/realistic-captcha-risk-lab`: self-owned localhost lab combining JS signature parity, fingerprint observation, captcha action replay evidence references, business ledger/concurrency raw reports, and Phase 2.1 evidence boundaries.

Boundary: runtime parity is not risk token forgery; fingerprint surface diagnostics are not evasion. Public evidence remains non-positive unless business data assertions pass on an authorized target.

## Phase 3.5 Longrun Hardening

Phase 3.5 adds long-run verification and failure-driven hardening for the local SKILLS loop.

- Run_id: `run-20260630-041500-phase3-5-longrun`.
- Entry tool: `tools/phase3_longrun_runner.py`.
- Config: `configs/phase3_longrun.yaml`.
- Evidence root: `public-range-evidence/longrun/phase3-5/<run_id>/`.
- Experience cards: `skills-experience/longrun/phase3-5/<run_id>/`.
- Evals: `evals/longrun/phase3-5/`.
- New skill: `6-验证码逆向层/captcha-model-training`.

Required outputs: `longrun-ledger.json`, `longrun-summary.json`, `metric-trends.json`, `failure-cases.json`, `issue-ledger.json`, `regression-report.json`, and `capability-decision.json`.

Capability boundary: Phase 3.5 can harden local CAPTCHA/runtime/fingerprint/concurrency rules, but it remains `memory_only` unless Phase 2.1 final business API and business-data assertions pass.

## Standard LOOP Delivery Contract

Standard LOOP routing uses the fixed skill type taxonomy in `99-SKILLS治理/20-routing-contract.md`:

- `external_entry`: user-facing entry skills such as `website-314-api-delivery`, `reverse-js-crawler`, `web-h5-loop-engineering`, and `skills-evaluation-governance`.
- `conditional_escalation`: evidence-triggered specializations such as CAPTCHA/WAF/site adapter work.
- `internal_tool`: atomic JS/runtime/replay helpers called by entry skills.
- `auxiliary_policy`: engineering guidelines only; `karpathy-guidelines` must not become a Web/H5 business entry.
- `captcha_model_delivery`, `fingerprint_risk_delivery`, `pure_api_delivery`, `lab_delivery`, and `real_site_observation`: delivery capability families with separate evidence gates.

Final business delivery is pure API only. Browsers may be used for analysis, capture, runtime trace, parity, or sample collection, but final business flow must not depend on Playwright, Puppeteer, Camoufox, browser profiles, copied cookies, browser storage, or manual cookie/token copy.
