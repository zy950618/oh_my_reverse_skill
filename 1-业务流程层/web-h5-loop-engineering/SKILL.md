---
name: web-h5-loop-engineering
description: >-
  Orchestration entry for Web/H5 reverse-engineering work only when the user explicitly asks for LOOP, closed-loop handling, multi-agent/three-role verification, repeated validation, execution ledger, acceptance report, or when a prior attempt failed because evidence, repeat verification, cleanup, impact, or backend acceptance was incomplete. It coordinates executor, verifier, and governor roles with loop ledger, acceptance report, fixture freshness, and metrics. Do not trigger for ordinary one-pass crawler tasks, simple fixture freshness checks, or single-tool JS work; use reverse-js-crawler or the relevant support tool first.
platforms: [web, h5]
---

# Web/H5 Loop Engineering

## Purpose

把 Web/H5 逆向任务从“一次执行”改成有边界的闭环：执行、验证、治理复核至少三角色循环推进，直到证据达标、触发停止条件或进入人工复核。

本 skill 是总控编排，不直接替代 `reverse-js-crawler`、`website-314-api-delivery`、`site-api-adapter` 或验证码/WAF 专项 skill。

## Workflow

1. 定义 loop 目标和停止条件：
   - 写清 domain、market、locale、currency、stage、auth_state、target_api。
   - 写清完成条件、失败阈值、最大迭代次数、人工复核条件。
   - 没有停止条件时不能启动长期 loop。
   - 用 `tools/web_h5_loop_runner.py init` 创建 execution ledger；没有 ledger 的 loop 只能算讨论，不能算实战执行。

2. 分配至少三类角色：
   - Executor: 做侦察、抓包、JS 入口定位、接口复现或实现改动。
   - Verifier: 跑 fresh capture、clean-state retest、snapshot replay、diff、schema、并发阶梯。
   - Governor: 检查事实等级、反泛化、session/cache 隔离、图谱、影响回归、拒答和 cleanup。
   - 可选第四类 Reviewer: 处理支付、登录态、PII、验证码、WAF、证据冲突和生产影响。

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
   - `Executor` 自评不能替代独立验证。
   - 本地 score 或 gate 通过不能写成真实站点成功。
- 用 `tools/web_h5_acceptance_report.py validate` 验证 acceptance report；默认 `STRUCTURE_PASS` 只代表结构可读。声明并发、稳定或完成前必须用 `--require-complete` 并取得 `SUCCESS_PASS`。
- 用 `tools/fixture_freshness_report.py` 暴露 expired/review_pending/recent replay 状态；freshness 不通过时不得声明网页一致性当前有效。

## Success Criteria

- 至少三角色 loop ledger 存在，并标注每轮 owner、action、evidence、verification、decision。
- Fresh Evidence Table、Old-vs-New Diff、Retest Matrix、Concurrency Ladder 和 Scope Ledger 均有结果或阻塞说明。
- Acceptance Report、Fixture Freshness Ledger、Risk-Control Ledger、Data Acceptance Ledger 和 Metrics Ledger 均存在；真实完成必须是 `SUCCESS_PASS`，`STRUCTURE_PASS` 或 `BLOCKED` 不能写成成功。
- 失败模式进入 known-failures、test-log-lessons、impact-regression 或 eval backlog。
- loop 有最大迭代次数、停止条件、人工复核条件和 cleanup ledger。
- 输出区分 observed / derived / assumed / unverified。

## Tool Policy

- 开始 loop 前 Read `4-通用规范层/karpathy-guidelines/SKILL.md`。
- 涉及 Web/H5 逆向执行时 Read `1-业务流程层/reverse-js-crawler/SKILL.md`。
- 涉及评分/准入/漂移时 Read `1-业务流程层/skills-evaluation-governance/SKILL.md`。
- 涉及抓包、多轮复测、清 cookie/storage/cache、并发、session/cache 时 Read `99-SKILLS治理/16-实战复测与证据新鲜度规约.md` 和 `reverse-js-crawler/references/web-h5-crawler-hardening.md`。
- 涉及真实执行标准化、并发验收、风控证据、网页一致性或 metrics 时 Read `references/real-execution-standard.md` 和 `reverse-js-crawler/references/crawler-acceptance-pack.md`。
- 每次修改 loop 结构、角色规则、runner、acceptance、metrics 或 freshness gate 后跑 `python tools/validate_web_h5_loop_gate.py`、`python tools/validate_web_h5_real_execution_gate.py` 和 `python tools/ci_gate.py .ci-out`。

## Boundaries

- 本 skill 只适用于 Web/H5 逆向、采集、接口复现和能力治理。
- 不负责生成 WAF/CAPTCHA 绕过方案；遇到保护只做证据、分类、授权范围和人工复核。
- 不把多 agent loop 写成无限自动化；必须有 token/成本、迭代次数和人工接管边界。
- 不把一次本地 loop gate 通过泛化成真实站点稳定。
- 不把风险控制写成绕过能力；并发实现只允许隔离、退避、停止、session retirement、fresh replay 和人工复核。

## Governance

- Version: 0.2.0
- Status: real-execution-standard baseline
- Change log: record role/gate/eval changes in `references/governance.md`.
- Drift tests: rerun loop evals when role boundaries, stop conditions, evidence gates, or crawler hardening rules change.

## References

- `references/loop-roles.md`: 三角色或多角色 agent 职责、输入输出和交接规则。
- `references/loop-ledgers.md`: Loop Ledger、Stop Ledger、Human Review Ledger 和 Cleanup Ledger 模板。
- `references/real-execution-standard.md`: Loop Runner、acceptance report、fixture freshness、metrics 和真实完成口径。
- `references/governance.md`: versioning, source patterns, local gates, drift policy.
