---
name: web-h5-loop-engineering
standard_type: external_entry
description: >-
  Orchestration entry for Web/H5 reverse-engineering business work only when the user explicitly asks for business LOOP, closed-loop handling, role-separated verification, repeated validation, execution ledger, acceptance report, or when a prior attempt failed because evidence, repeat verification, cleanup, impact, or backend acceptance was incomplete. Explicit LCL or Claude-Codex repository engineering routes to the unique root Low-LOOP operator instead. Do not trigger for ordinary one-pass crawler tasks, simple fixture freshness checks, or single-tool JS work; use reverse-js-crawler or the relevant support tool first.
platforms: [web, h5]
---

# Web/H5 Loop Engineering

## Purpose

把 Web/H5 逆向业务任务从“一次执行”改成有边界的闭环：执行、验证、治理复核按人工角色分离循环推进，直到证据达标、触发停止条件或进入人工复核。当前角色分离不等于 actor-separated independent verifier。

## Low-LOOP V3 Routing Boundary

Web/H5 business LOOP 负责站点逆向证据、业务断言、最终业务 API 与 pure API 边界；仓库级 Low-LOOP 负责 Claude-Codex 工程编排。用户明确要求 LCL、Low-LOOP 或 Claude-Codex engineering 时，必须先进入唯一直接 operator entry [`Claude codex 指挥codex 二次优化loop执行文件.md`](../../Claude%20codex%20指挥codex%20二次优化loop执行文件.md)，不得把本 Skill 当作竞争入口或复制调用模板。

权威链继续指向 [`24-low-loop-execution-standard.md`](../../99-SKILLS治理/24-low-loop-execution-standard.md)、[`25-low-loop-adoption-record.md`](../../99-SKILLS治理/25-low-loop-adoption-record.md)、[V3 schema index](schemas/index.schema.json)、[semantic validation contract](references/low-loop-semantic-validation-contract.md) 和[非操作 roadmap](references/low-loop-roadmap.md)。能力声明保持 `MANUAL_ORCHESTRATED_LEDGER_ONLY` / `structure_only`；未来 CLI 尚未实现，命令契约只在 roadmap 中定义。

## Standard LOOP 100-Point Gate

This skill owns the Web/H5 business LOOP supervisor role. Local control and evidence state belongs under ignored `.loop/`: `.loop/current.json` is derived from append-only events, while task, run, and artifact references follow the V3 schema index and semantic contract. Do not create or recreate `LOOP_STATE.md`. The current `tools/web_h5/web_h5_loop_runner.py` supports ledger init, iteration record, and ledger validation only; it does not implement the future V3 state store, executor, autonomous loop, or actor-separated verifier. Local structure and validator PASS can support only `STRUCTURE-ONLY` within the current claim ceiling and cannot be reported as real-site success without direct final business API acceptance, repeat direct interface evidence, and business data assertions.


公开靶场训练 / SKILLS 实战进化也从本 skill 进入，但只能在
`configs/range_scope_contract.yaml` 允许的 target 和 mode 内执行。公开靶场 run
必须产出 machine-readable evidence、loop ledger 和 acceptance report；只有最终业务 API
通过非浏览器 direct interface 且 repeat direct interface 验证时，才允许进入
`positive_allowed`。

## Workflow

1. 定义 loop 目标和停止条件：
   - 写清 domain、market、locale、currency、stage、auth_state、target_api。
   - 写清完成条件、失败阈值、最大迭代次数、人工复核条件。
   - 没有停止条件时不能启动长期 loop。
   - 用 `tools/web_h5/web_h5_loop_runner.py init` 创建 execution ledger；没有 ledger 的 loop 只能算讨论，不能算实战执行。
   - 公开靶场 run 还要先查 `configs/range_scope_contract.yaml`，写清 target_id、allowed_mode、in_scope、out_of_scope 和 positive gate。

2. 人工分离三类职责（不声称 actor-separated independent verifier）：
   - Executor: 做侦察、抓包、JS 入口定位、接口复现或实现改动。
   - Verifier: 跑 fresh capture、clean-state retest、snapshot replay、diff、schema、并发阶梯。
   - Governor: 检查事实等级、反泛化、session/cache 隔离、图谱、影响回归、拒答和 cleanup。

3. 单轮 loop 顺序：
   - Plan: 选一个最小任务，不扩 scope。
   - Act: 调用对应执行 skill 或工具。
   - Observe: 记录 run_id、capture_id、network_log_id、script_hash、state_reset。
   - Verify: 对照 JSON Pointer、replay、fixtures、并发阶梯和失败分类。
   - Revise: 只修当前失败根因，更新 ledger。
   - Persist: 写回 site memory、reverse memory、knowledge graph、impact regression 或 eval backlog。
   - Metrics: 更新 task_count、success_browserless_verified、concurrency_verified、flaky_count、blocked_by_protection 和 fixture freshness 状态。

4. 多轮规则：
   - 每一轮必须有新观察或明确复用旧证据的理由。
   - 每轮从失败 ledger 或上一轮 learning 开始，不重新开荒。
   - 混合结果例如 `200, 403, 200` 是 flaky，不是成功。
   - 两轮连续同一 blocker 后，收缩 scope 或进入人工复核，不用无限重试掩盖失败。

5. 验收：
   - 只有 `Verifier` 和 `Governor` 都通过，才能声明完成。
   - `Executor` 自评不能替代 Claude 的 manual role-separated re-execution 和人工治理判定。
   - 本地 score 或 gate 通过不能写成真实站点成功。
- 用 `tools/web_h5/web_h5_acceptance_report.py validate` 验证 acceptance report；默认 `STRUCTURE_PASS` 只代表结构可读。声明并发、稳定或完成前必须用 `--require-complete` 并取得 `SUCCESS_PASS`。
- 用 `tools/web_h5/fixture_freshness_report.py` 暴露 expired/review-needed/recent replay 状态；freshness 不通过时不得声明网页一致性当前有效。

## Success Criteria

- 三类人工职责的 loop ledger 存在，并标注每轮 owner、action、evidence、verification、decision；不得据此声称 actor-separated verifier 已实现。
- Fresh Evidence Table、Old-vs-New Diff、Retest Matrix、Concurrency Ladder 和 Scope Ledger 均有结果或阻塞说明。
- Acceptance Report、Fixture Freshness Ledger、Risk-Control Ledger、Data Acceptance Ledger 和 Metrics Ledger 均存在；真实完成必须是 `SUCCESS_PASS`，`STRUCTURE_PASS` 或 `BLOCKED` 不能写成成功。
- 失败模式进入 known-failures、test-log-lessons、impact-regression 或 eval backlog。
- loop 有最大迭代次数、停止条件、人工复核条件和 cleanup ledger。
- 输出区分 observed / derived / assumed / unverified。
- 公开靶场训练必须通过 `tools/evidence/validate_public_range_evidence.py public-range-evidence`；未满足 direct interface repeat gate 的结果只能是 `negative_eval_only`、`memory_only` 或 `prohibited`。
- 公开靶场训练若要声明为真实执行，必须通过 `tools/evidence/validate_real_execution_proof.py public-range-evidence` 并取得 `REAL_EXECUTION_PASS`；缺少 `execution_proof` 的 evidence 只能算 `STRUCTURE_ONLY`。
- 状态必须拆成两层：`execution_status` 只说明是否真实执行过，`capability_status` 才说明能力参与资格。`REAL_EXECUTION_PASS` 不等于 `positive_allowed`。
- dummy/local/provider testing key 只能证明流程、采集、状态机和边界负例；没有最终业务 API backend acceptance 和 repeat direct interface acceptance 时，不能证明真实业务能力。

## Tool Policy

- 开始 loop 前 Read `4-通用规范层/karpathy-guidelines/SKILL.md`。
- 涉及 Web/H5 逆向执行时 Read `1-业务流程层/reverse-js-crawler/SKILL.md`。
- 涉及评分/准入/漂移时 Read `1-业务流程层/skills-evaluation-governance/SKILL.md`。
- 涉及抓包、多轮复测、清 cookie/storage/cache、并发、session/cache 时 Read `99-SKILLS治理/16-实战复测与证据新鲜度规约.md` 和 `reverse-js-crawler/references/web-h5-crawler-hardening.md`。
- 涉及真实执行标准化、并发验收、风控证据、网页一致性或 metrics 时 Read `references/real-execution-standard.md` 和 `reverse-js-crawler/references/crawler-acceptance-pack.md`。
- 每次修改 loop 结构、角色规则、runner、acceptance、metrics 或 freshness gate 后跑 `python3 tools/web_h5/validate_web_h5_loop_gate.py`、`python3 tools/web_h5/validate_web_h5_real_execution_gate.py` 和 `python3 tools/governance/ci_gate.py .ci-out`。
- 每次新增或修改公开靶场 evidence 后跑 `python3 tools/evidence/validate_public_range_evidence.py public-range-evidence`，并保留本轮 ledger/report 的结构校验结果。

## Boundaries

- 本 skill 只适用于 Web/H5 逆向、采集、接口复现和能力治理。
- 不负责生成 WAF/challenge 突破方案；遇到保护只做证据、分类、授权范围和人工复核。
- 不把多 agent loop 写成无限自动化；必须有 token/成本、迭代次数和人工接管边界。
- 不把一次本地 loop gate 通过泛化成真实站点稳定。
- 不把风险控制写成突破能力；并发实现只允许隔离、退避、停止、session retirement、fresh replay 和人工复核。

## Governance

- Version: 0.2.2
- Status: business-data-assertion gate baseline
- Change log: record role/gate/eval changes in `references/governance.md`.
- Drift tests: rerun loop evals when role boundaries, stop conditions, evidence gates, or crawler hardening rules change.

## References

- `references/loop-roles.md`: 三角色或多角色 agent 职责、输入输出和交接规则。
- `references/loop-ledgers.md`: Loop Ledger、Stop Ledger、Human Review Ledger 和 Cleanup Ledger 模板。
- `references/real-execution-standard.md`: Loop Runner、acceptance report、fixture freshness、metrics 和真实完成口径。
- `references/governance.md`: versioning, source patterns, local gates, drift policy.
