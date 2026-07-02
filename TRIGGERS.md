# TRIGGERS — 触发词速查表

> 说什么 → 触发哪个 Skill。中英双列。
>
> 这张表是**用户视角**的速查。每个 Skill 自己的 frontmatter `TRIGGER when:` 是**Claude 视角**的判断依据。两者互补。
>
> 其他入口:[USAGE](./USAGE.md) · [INSTALL](./INSTALL.md)

---

## 怎么读这张表

- **关键词**:你说这句话或包含这些词,Claude 会激活对应 Skill
- **Skill**:被触发的 Skill 名
- **层**:1=业务流程总控 / 2=JS 工具 / 4=规范 / 5=沉淀 / 6=验证码逆向
- **做什么**:Skill 接管后的实际行为(一句话)
- **不触发**:什么时候 Skill 不应该被激活(避免误触)

---

## 网页逆向类

| 关键词 (中) | 关键词 (en) | Skill | 层 | 做什么 | 不触发 |
|---|---|---|---|---|---|
| 逆向 XXX 网站 / 纯接口实现 / FastAPI 接口测试 / 网站接入 / 把 XXX 接入 314 | reverse XXX website / new site adapter / pure API / FastAPI test API / 314 framework | `website-314-api-delivery` | 1 | 六阶段总控,把网页 → Python/FastAPI 可测接口 → 人工确认后可选接入本地基础框架 | 只想看 HTML 内容 / 调浏览器自动化 |
| JS 逆向 / 接口还原 / 加密参数 / 补环境 / 批量采集 | JS reverse / API restoration / sign reverse / crawler delivery | `reverse-js-crawler` | 1 | 页面侦察 + 真实 API 识别 + sign 还原 + Python/Node 复现 | 静态分析 / 非 Web/H5 |
| Loop Engineering / LOOP / 闭环处理 / 多 agent 逆向 / 三个 agent 验证 / 循环执行验证修正 / 反复抓包复测 / 自动化验证闭环 / 爬虫 LOOP / 真实 Loop Runner / 执行账本 / 实战执行标准化 / 结果量化沉淀 | Loop Engineering / agent loop / multi-agent reverse loop / closed-loop verification / Ralph-style loop / loop runner / execution ledger / quantitative crawler metrics | `web-h5-loop-engineering` | 1 | Executor + Verifier + Governor 至少三角色闭环,并产出 runner ledger、acceptance report、fixture freshness 和 metrics | 单次加密入口定位 / 不需要多轮验证 |
| 公开靶场训练 / public-range-evidence / 用公开靶场进化 SKILLS / 靶场训练进化 SKILLS | public range training / public-range evidence / evolve skills with public ranges | `web-h5-loop-engineering` + `skills-evaluation-governance` | 1 | 按 allowlist 跑公开/本地/官方测试靶场，产出 evidence、负例/边界 eval 和正向门槛判断 | 非 allowlist 真实生产站点 / CAPTCHA/WAF 绕过 |
| 84 盾 / Reese84 / Incapsula / x-d-token / WAF 挑战 / 风控 token / 浏览器指纹 / 反扒 / token 被拒 | reese84 / incapsula / imperva / x-d-token / browser fingerprint / WAF challenge / anti-bot | `imperva-waf-reese84` | 1 | 指纹模拟 + token 缓存 + 阶段化接受度验证 | 普通 cookie / 单纯 401(非 WAF) |
| 验证码 / reCAPTCHA / hCaptcha / Turnstile / 滑块 / 点选 / sitekey / challenge / verify endpoint / captcha token / 验证前后响应不同 | captcha / recaptcha / hcaptcha / turnstile / slider / click captcha / sitekey / challenge / verify endpoint | `captcha-service-delivery` | 6 | provider 流程 + 站点绑定 + clean/verified/repeat 三轮抓包 + token 状态 + 图谱回归 | 普通 sign/x-sign 定位 |
| 找加密入口 / xxx 在哪生成 / 签名怎么算 / 请求头 xxx 哪来的 / 定位加密函数 | locate sign entry / find crypto entry / where is x-sign generated | `find-crypto-entry` | 2 | 静态搜参数名 + XHR 断点,只输出函数位置+调用链 | 抓包看请求 / 分析普通参数 |
| 解混淆 / 反混淆 / 字符串数组解密 / _0x 看不懂 / 控制流平坦化 / deobfuscate / sojson / obfuscator.io | deobfuscate / unobfuscate / string array decrypt / control flow flattening | `ast-deobfuscate` | 2 | Babel AST:字符串解密 / 控制流还原 / 死代码删除 | minified(只是压缩) / 想格式化代码 |
| 补环境 / 把 JS 搬到 Node / webpack 模块提取 / Node 里跑 / 环境模拟 | env patch / node sandbox / webpack module extract / run browser JS in Node | `env-patch` | 2 | window/document/navigator/Proxy 引擎 + 模块提取 | 浏览器内调试 / 普通 Node 代码 |

---

## 一致性验证类(产出 vs 真实网页对齐)

> 没有专门的 SKILL,是**脚本工具链**。Claude 看到对应关键词会走 [07 一致性验证规约](./99-SKILLS治理/07-一致性验证规约.md) 的流程。

| 关键词 (中) | 关键词 (en) | 工具 | 做什么 |
|---|---|---|---|
| 跑一致性 / fixtures / snapshot diff / 重放对比 / 验证产出和网页一致 | run consistency / fixtures verification / snapshot diff / replay vs original | `tools/recorder/cloak_recorder.py` + `tools/replayer/snapshot_replay.py` + `consistency_report.py` | 录制 fixtures → 重放 → 字段 diff → 出 markdown 报告 + trend.json |
| HAR 导入 / 抓包导入 fixtures | HAR import / DevTools to fixtures | `tools/recorder/har_to_fixtures.py` | Chrome DevTools 导出的 HAR → snapshots 三件套 |
| CloakBrowser 录制 / 反指纹浏览器录制 | CloakBrowser record / cloak record | `tools/recorder/cloak_recorder.py` | 启动带反指纹的 Chromium 录请求 |
| 验证 fixtures 合规 / fixtures schema 检查 | validate fixtures schema | `tools/replayer/validate_fixtures.py` | 检查三件套齐 / category 合法 / expiry 未过 |
| 真实 Loop / 并发验收 / 风控证据 / fixtures 新鲜度 / 结果量化 | loop runner / acceptance report / fixture freshness / real execution gate | `tools/web_h5_loop_runner.py` + `tools/web_h5_acceptance_report.py` + `tools/fixture_freshness_report.py` + `tools/validate_web_h5_real_execution_gate.py` | 建立执行账本、并发/风控/UI一致性验收、暴露 expired/review_pending 并沉淀 metrics |

---

## 治理 / 评分 / 创建类

| 关键词 (中) | 关键词 (en) | Skill | 层 | 做什么 | 不触发 |
|---|---|---|---|---|---|
| Skill 评分 / Skill Bench / 跑分 / 评测 / 回测 / 漂移测试 / 新增 Skill 准入 / 负例测试 | score skills / Skill Bench / backtest / drift test / new skill admission | `skills-evaluation-governance` | 1 | 三段分→四段分评分,回测,漂移检测 | 一般代码评审 / PR review |
| 新建 skill / 创建 skill 从零起 / 优化 SKILL.md 描述 / 跑 description loop / 触发词优化 | create skill / optimize SKILL.md description / run trigger loop | `ai-reverse-skill-creator` | 2 | 起骨架 + eval loop + 触发词优化 | 一般 prompt 优化 / 通用 GPT 调优 |
| 接口化沉淀 / adapter.yaml / prompt-router / runbook / schema 沉淀 / 多站点复用 | API adapter / adapter.yaml / prompt-router / standardization | `site-api-adapter` | 5 | 把接口稳定的逆向产出 → adapter.yaml / schema.json / runbook | 还在调接口 / 接口未稳定 |
| 行为守则 / 最小改动 / 避免过度抽象 / 显式假设 / 可验证成功标准 | karpathy guidelines / surgical changes / surface assumptions / verifiable success | `karpathy-guidelines` | 4 | 辅助规范:其他 Skill 写代码、评审、重构、验证时读取 | 不作为 Web/H5/CAPTCHA/WAF/业务任务主入口 |
| 事实证据 / AI 虚假 / 没证据 / 以点概面 / 发散 / 并发隔离 / session 混用 | evidence / hallucination / overgeneralization / concurrency isolation / session cache | 治理规约 11/12/13 | 99 | 结论分级 + 范围账本 + 并发/session/cache 隔离 | 普通闲聊 / 非逆向任务 |
| 知识图谱 / 影响回归 / 改 A 伤 B / 数据偏移 / 写死请求头 / 写死指纹 / 端点关联 | knowledge graph / impact regression / dependency graph / drift / hardcoded headers | 治理规约 14/15 | 99 | 节点边更新 + Impact Record + 必跑回归矩阵 | 普通项目管理 |
| 旧数据 / 新数据 / 清空浏览器 / 重新抓包 / 多轮比对 / HAR 过期 / token 过期 / scriptId 旧了 / 真实经验没吸收 | fresh evidence / stale HAR / browser reset / recapture / old token / new token / reverse memory | 治理规约 16 + `逆向工程经验库` | 99 | run 账本 + Fresh Evidence Table + old-vs-new diff + 经验写回 | 不涉及动态证据 |
| 收尾清理 / 删除测试文件 / 历史数据 / 废代码 / 废注释 / 加密算法图 | cleanup / remove temp files / stale history / dead code / crypto graph | 治理规约 17 + `逆向工程经验库` | 99 | cleanup ledger + encryption-algorithm-graph.md | 未完成验证 |

---

## 跨类场景(多 Skill 协同)

入口优先级: 明确 LOOP/闭环/多 agent 先走 `web-h5-loop-engineering`; 完整纯接口/FastAPI/314 服务化交付走 `website-314-api-delivery`; 聚焦单链路 JS 逆向、接口还原或采集脚本走 `reverse-js-crawler`。三者入口相邻但职责不同,不得无优先级同时触发多个主 Skill。

标准 LOOP 触发补充: 验证码训练/坐标/模型包/通过率走 `captcha_model_delivery`；指纹表面、block reason、context isolation 和验证码联动走 `fingerprint_risk_delivery`；真实航司站点只生成 `real_site_observation` 任务包,不能把生产站点当成本地靶场；本地靶场必须标为 `lab_delivery` 并用 validator 验收。

| 场景 | 触发顺序 |
|---|---|
| 新网站全链路接口 | `website-314-api-delivery` → `reverse-js-crawler` → `find-crypto-entry` → `ast-deobfuscate` / `env-patch` → 一致性验证 → `site-api-adapter` |
| Web/H5 多 agent 闭环逆向 | `web-h5-loop-engineering` → Loop Runner ledger → `reverse-js-crawler` / `website-314-api-delivery` → acceptance report / fixture freshness → Verifier replay/diff/schema/concurrency → Governor evidence/scope/memory/cleanup/metrics |
| WAF 拒接口 | 主链路任意触发 + `imperva-waf-reese84` 并行处理 token |
| 验证码阻断业务 API | 主链路任意触发 + `captcha-service-delivery` 做 provider/site binding 与三轮抓包 |
| 收尾治理 | (任意 Skill 工作完)→ reverse-memory + 站点经验库写回 + `skills-evaluation-governance` 打分 + cleanup ledger + 加密算法图 |

---

## 反例:这些词**不会**自动触发本仓库 Skill

- 写普通业务代码 / CRUD / React 前端 / 数据库设计
- 抓包看请求(没有"逆向"意图)
- 装环境 / 配置 / 部署
- 写文档 / 开会 / 项目管理
- LLM 通用 prompt 调优(非 Claude SKILL)

如果你想做这些事但 Claude 误触发了某个 Skill,直接说"不要走 reverse-js-crawler 流程,我只是想 X"即可。

---

## 找不到对应触发词

提个 issue 或直接在 Claude 里说:**"我想做 X,但不知道触发哪个 Skill"**。Claude 会:
1. 尝试匹配最接近的 Skill 询问你确认
2. 如果都不匹配,提示走通用代码 / 走 `ai-reverse-skill-creator` 创建新 Skill

新触发词会沉淀到对应 SKILL.md 的 `description`(下轮 auto_tune 自动跑触发词校准),让下次更准。

## Phase 3 CAPTCHA Algorithm Triggers

| Keywords | Skill | Layer | Action | Do not trigger for |
|---|---|---|---|---|
| open-source captcha model stack / OCR model choice / detector stack / segmentation model / local model benchmark / model registry | `captcha-open-source-model-stack` | 6 | Select local/open-source model families, dataset-to-model route, benchmark plan, and registry entries for authorized/local labs | Action replay, provider token work, third-party CAPTCHA/WAF/risk-control bypass |
| model action e2e / action replay from model prediction / failure replay / promotion gate / action success metrics | `captcha-model-action-e2e` | 6 | Convert existing model predictions into scoped actions, replay failures, and archive promotion metrics | Model family selection, dataset splitting, remote solver APIs, unauthorized challenge automation |
| CAPTCHA algorithm training / captcha vision benchmark / text captcha / slider offset / rotate angle / synthetic captcha dataset | `captcha-visual-recognition-lab` + `captcha-image-dataset-governance` + `captcha-algorithm-benchmark` | 6 | Generate local/authorized samples, run baseline solvers, output metrics, failure cases, evidence, experience cards, and evals | Unknown third-party production challenge automation |
| localhost action replay / captcha action planner / drag slider from prediction / click predicted target | `captcha-action-planner` | 6 | Convert recognition output into localhost or authorized browser actions with screenshot, trace/network summary, and state transition evidence | Clearance cookie reuse, third-party solver API, or human token replay |
| provider diagnostics / sitekey / iframe / token field / verify endpoint vs business API | `captcha-provider-diagnostics` | 6 | Observe provider state and separate challenge/verify endpoint success from final business API success | Bypass or automated handling of unknown production providers |
| fingerprint block reason / webdriver / canvas / WebGL / client hints / permissions | `fingerprint-block-reason-diagnostics` | 7 | Record observed signals and block reason ledger for diagnostics only | Webdriver hiding, fingerprint forgery, proxy rotation, or rate-limit evasion |
| authorized target / owned target / allowed_hosts / rate_limit / stop_condition | `authorized-target-adapter` | 1 | Establish scope, allowed hosts, limits, redaction, and Phase 2.1 business data gates before real target adaptation | Non-authorized target automation |

## Phase 3.4 Runtime/Fingerprint Triggers

| Keywords | Skill | Layer | Action | Do not trigger for |
|---|---|---|---|---|
| ruoyiPage / PageRuntime / Browser Node V8 parity / JS signature fixture / environment contract | `js-page-runtime-parity` | 2 | Run authorized JS fixture across Browser, Node, and PageRuntime, then emit dependency map, contract, diff, and regression fixture | Unauthorized token generation, WAF bypass, risk token forgery |
| fingerprint surface / browser surface inventory / profile consistency / risk-state attribution | `browser-fingerprint-surface-lab` | 7 | Observe fingerprint values, surface hash, drift, allowed actions, and forbidden actions | Webdriver hiding, fingerprint spoofing, proxy evasion |
| realistic captcha risk lab / Phase 3.4 lab / runtime parity plus fingerprint plus concurrency | `js-page-runtime-parity` + `browser-fingerprint-surface-lab` + `authorized-target-adapter` | 2/7/1 | Run self-owned localhost lab evidence and keep capability boundaries explicit | Unknown third-party production automation |

## Phase 3.5 Longrun Triggers

| Keywords | Skill | Layer | Action | Do not trigger for |
|---|---|---|---|---|
| Phase 3.5 longrun / long-run verification / deep hardening loop / failure-driven SKILLS feedback | `web-h5-loop-engineering` + `skills-evaluation-governance` + `captcha-model-training` | 1/6 | Run `tools/phase3_longrun_runner.py`, generate longrun ledger, issue ledger, failure cases, experience cards, evals, and capability decision | Third-party CAPTCHA/WAF solving claims |
| multi-image captcha / longrun captcha benchmark / failure cases to training targets | `captcha-visual-recognition-lab` + `captcha-algorithm-benchmark` + `captcha-model-training` | 6 | Benchmark all local challenge types and convert failures into training targets | DOM answer leakage, human token replay |
