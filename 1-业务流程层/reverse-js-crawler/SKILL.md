---
name: reverse-js-crawler
description: >-
  Use this skill for crawler reverse engineering and interface restoration: page reconnaissance, real API discovery, JavaScript sign/token/cookie analysis, browser runtime dependency tracing, request reproduction, batch collection, concurrency acceptance, risk-control evidence, UI/API parity, fixture freshness, and verified Python/Node.js delivery. Trigger when the user asks for JS reverse, crawler reverse, API restoration, encrypted parameters, sign/x-sign/authKey/token, web data collection, turning a page into stable collection scripts, concurrency crawler validation, anti-flake validation, or Chinese requests such as 逆向采集, JS逆向, 接口还原, 接口复现, 加密参数, 补环境, 浏览器环境模拟, 请求复现, 批量采集, 数据清洗, 采集脚本交付, 并发爬虫验收, 风控证据, 网页一致性, or fixtures 新鲜度治理.
platforms: [web, h5]
---

# Reverse JS Crawler

## Do NOT Trigger When

- 用户明确要"FastAPI 接口测试交付"、"314 基础框架"、"长期可维护服务"、"完整查询→加车→生单→支付链路交付" → 切到 `website-314-api-delivery`（让它做总控，调用本 skill 做逆向部分）
- 用户只要把已有逆向结果"标准化 adapter / schema / runbook / prompt-router" → 切到 `site-api-adapter`
- 目标网站命中 Imperva / Reese84 / Incapsula / 84盾 / x-d-token → 切到 `imperva-waf-reese84`
- 用户做的不是 Web/H5 页面、接口或浏览器 JS 逆向 → 不属于本仓库范围
- 用户要求"评分某个 skill"、"准入测试"、"漂移检查" → 切到 `skills-evaluation-governance`
- 用户只是问"AST 解混淆"、"在 Node 跑这段 JS"、"找加密入口"等原子问题 → 直接用对应原子工具 `ast-deobfuscate` / `env-patch` / `find-crypto-entry`

## Purpose

把页面、接口、抓包或 JS 线索还原成可运行、可验证、可维护的采集工程。不要只给方向；要闭环到脚本、测试、日志和失败边界。

## Workflow

1. 侦察页面与真实入口：
   - 从页面行为和网络请求确认真实数据入口。
   - 记录 URL、method、headers、query/body、initiator、返回结构。
   - 区分页面渲染数据、接口 JSON、WebSocket/SSE、静态配置。

2. 依赖分析和分类：
   - 识别 Header、Cookie、localStorage/sessionStorage、时间戳、nonce、UA、Referer、Origin。
   - 标出每个依赖来自服务端、浏览器环境、业务脚本还是第三方 SDK。
   - 分类为纯 HTTP、JS 加密、补环境、WAF、登录态、支付风险或不可自动化。

3. JS 加密还原：
   - 优先定位入口，再决定 AST 解混淆、Hook、补环境或直接复用。
   - 记录调用链、入参、出参、中间态、脚本 URL、函数位置。
   - 对 sign/token/cookie 生成逻辑给出可复现实现和对照样例。

4. 请求复现：
   - 最小可行请求先跑通，再加入重试、分页、并发、代理、日志。
   - 如果需要浏览器或 TLS 指纹，说明原因，并优先把可抽离部分下沉到纯 HTTP/Node runtime。

5. Web/H5 爬虫硬化闸门：
   - 单次 200、偶发成功或本地 token 生成成功都不能声明稳定。
   - 至少记录 `clean_unverified`、`verified`、`repeat_verified` 三组抓包或明确阻塞原因。
   - 每轮复测必须清空 cookie/storage/cache/service worker 或创建新的 browser context，并记录 `state_reset`。
   - 涉及批量或并发时必须先跑 1 worker 基线，再跑 2/5/10 worker 并发阶梯；每阶记录 session/cache 隔离、失败率、403/429/503、P95 和停止条件。
   - 不允许共享 cookie jar、localStorage/sessionStorage、token cache 或账号态，除非有当前 run 的后端接受证据证明可复用。
   - 用 `tools/web_h5_acceptance_report.py` 生成并验证 acceptance report；没有 report 不声明批量、并发或稳定。
   - 风控处理只允许授权范围内的隔离、退避、jitter、session retirement、kill switch、fresh replay 和人工复核；不写绕过、指纹伪造或 clearance cookie 复用。
   - 数据验收必须做 UI/API parity：网页可见字段对 API JSON Pointer，fixtures freshness 通过后才能声明当前网页一致。

6. 批量采集与清洗：
   - 增加分页、断点续传、去重、字段校验、异常记录。
   - 输出结构化数据和统计摘要。

7. 交付：
   - 给出工程目录、运行方式、配置项、测试方式、已知失败边界。
   - 成功必须以真实目标请求被服务端接受为准，不以本地 token 生成成功为准。

## Success Criteria

- 已确认真实数据入口，不靠猜 URL。
- 已列出请求依赖和来源。
- 已区分普通加密、补环境、WAF、业务错误和测试数据问题。
- 已提供可运行复现和至少一次稳定性验证；稳定性验证必须覆盖多轮清状态复测，不能把偶发成功当成正确。
- 批量或并发声明必须有并发阶梯记录、session/cache 隔离证据和停止条件。
- 抓包、fixtures、replay、script hash、state_reset 和 run_id 能互相对应。
- 风控/保护相关结论必须有 protected business API backend acceptance 或明确 blocked/human_review/negative eval。
- 数据交付必须有 UI/API parity、JSON Pointer、fixture freshness 和 replay/diff 证据；strict-review 或 freshness 失败时不能声明当前一致。
- 实战结果必须进入 metrics，不成功也要记录 flaky、blocked_by_protection 或 review_pending。
- 已把测试中的失败模式写入站点经验库或 eval backlog。

## Tool Policy

- **开始实现前 Read `~/.claude/skills/karpathy-guidelines/SKILL.md`**,确认 4 条原则:Think Before Coding / Simplicity First / Surgical Changes / Goal-Driven Execution。这是基础层规范,所有执行类 skill 强制依赖。
- **遇到逆向运行时问题(断点/时间/cookie/TLS 指纹/风控恢复/接口变更)Read `~/.claude/skills/oh_my_reverse_skill/99-SKILLS治理/10-逆向运行时常见问题.md`**。
- **输出结论、扩范围或做并发前 Read `~/.claude/skills/oh_my_reverse_skill/99-SKILLS治理/11-AI事实证据规约.md` / `12-反泛化与任务收敛规约.md` / `13-并发指纹与会话隔离规约.md`**。
- **改端点/字段/状态/保护/实现/eval 前后 Read `14-知识图谱行程与关联规约.md` / `15-AI变更风险与回归校验规约.md`,并更新 knowledge-graph.md / impact-regression.md**。
- **涉及抓包、清空 cookies、多轮复测、旧/新 HAR、scriptId、browser profile、并发或 session/cache 时 Read `16-实战复测与证据新鲜度规约.md` 和 `references/web-h5-crawler-hardening.md`**。
- **涉及并发验收、风控证据、网页一致性、acceptance report 或 metrics 时 Read `references/crawler-acceptance-pack.md`,并跑 `tools/web_h5_acceptance_report.py`**。
- 使用 `js_reverse` MCP 做页面打开、网络拦截、Hook、运行时变量、调用栈、Cookie/storage 观察。
- 使用仓库搜索和静态分析定位脚本入口。
- **进入加密还原阶段前，按需主动 Read 子 skill 的 SKILL.md 把上下文装进来再做**：
  - 找加密入口：Read `~/.claude/skills/find-crypto-entry/SKILL.md`
  - 看不懂的混淆 JS：Read `~/.claude/skills/ast-deobfuscate/SKILL.md`
  - 浏览器环境依赖搬到 Node：Read `~/.claude/skills/env-patch/SKILL.md`
- 每次 Read 后用一句话总结该 sub-skill 的 Boundaries，确认没越权（如 env-patch 仅处理"Node 内 JS 模拟"，不处理"DOM 完整渲染"）。
- 不要求用户手工抓包，除非当前环境无法访问目标页面并且缺少任何样本。

## Boundaries

- 这是逆向采集 Skill，不是通用编码 AGENT。
- 不把项目代码风格规则写进这里；编码规则后续放 AGENT。
- 不把 WAF/Incapsula/Reese84 深度风控细节堆在这里；遇到这类问题切到 `imperva-waf-reese84`。

## Governance

If the user asks for full website-to-service delivery, FastAPI interface test delivery, optional local base framework integration such as 314, search/cart/order/payment stages, or long-term API service output, use `website-314-api-delivery` as the orchestrator and use this skill only for the reverse/crypto parts.

- Version: 0.4.0
- Status: real-execution-acceptance baseline
- Site memory: write normal test failures to `站点经验库/<domain>/` when they can affect future same-site work.
- Backtest: run positive, negative, and regression evals after changing trigger words or workflow.
- CI: use Skill Bench or local backtest; quick_validate must pass before accepting changes.

## References

- `references/workflow.md`: 完整逆向交付流程。
- `references/testing.md`: 请求复现和批量采集测试要求。
- `references/web-h5-crawler-hardening.md`: Web/H5 爬虫反偶发、清状态复测、抓包证据、并发阶梯和 session/cache 隔离硬门槛。
- `references/crawler-acceptance-pack.md`: acceptance report、risk-control concurrency、UI/API parity、strict freshness 和 metrics 标准。
- `references/governance.md`: versioning, change log, Skill Bench, GitHub CI, quick_validate, and drift-test policy.

