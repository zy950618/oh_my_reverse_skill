---
name: web-h5-loop-engineering
standard_type: external_entry
description: >-
  Orchestration entry for Web/H5 reverse-engineering work only when the user explicitly asks for LOOP, closed-loop handling, multi-agent/three-role verification, repeated validation, execution ledger, acceptance report, or when a prior attempt failed because evidence, repeat verification, cleanup, impact, or backend acceptance was incomplete. It coordinates executor, verifier, and governor roles with loop ledger, acceptance report, fixture freshness, and metrics. Do not trigger for ordinary one-pass crawler tasks, simple fixture freshness checks, or single-tool JS work; use reverse-js-crawler or the relevant support tool first.
platforms: [web, h5]
---

# Web/H5 Loop Engineering

## Purpose

把 Web/H5 逆向任务从“一次执行”改成有边界的闭环：执行、验证、治理复核至少三角色循环推进，直到证据达标、触发停止条件或进入人工复核。

## Standard LOOP 100-Point Gate

This skill owns the standard LOOP supervisor role. A run must maintain `LOOP_STATE.md`, split work across agent roles, keep failure recovery records, and produce a standard-loop score. Local structure and validator PASS can support `STRUCTURE-ONLY` or local-lab readiness, but cannot be reported as real-site success without direct final business API acceptance, repeat direct interface evidence, and business data assertions.

本 skill 是总控编排，不直接替代 `reverse-js-crawler`、`website-314-api-delivery`、`site-api-adapter` 或验证码/WAF 专项 skill。

公开靶场训练 / SKILLS 实战进化也从本 skill 进入，但只能在
`public-range-evidence/_allowlist.yaml` 允许的 target 和 mode 内执行。公开靶场 run
必须产出 machine-readable evidence、loop ledger 和 acceptance report；只有最终业务 API
通过非浏览器 direct interface 且 repeat direct interface 验证时，才允许进入
`positive_allowed`。

## Workflow

1. 定义 loop 目标和停止条件：
   - 写清 domain、market、locale、currency、stage、auth_state、target_api。
   - 写清完成条件、失败阈值、最大迭代次数、人工复核条件。
   - 没有停止条件时不能启动长期 loop。
   - 用 `tools/web_h5_loop_runner.py init` 创建 execution ledger；没有 ledger 的 loop 只能算讨论，不能算实战执行。
   - 公开靶场 run 还要先查 `public-range-evidence/_allowlist.yaml`，写清 target_id、allowed_mode、in_scope、out_of_scope 和 positive gate。

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
- 公开靶场训练必须通过 `tools/validate_public_range_evidence.py public-range-evidence`；未满足 direct interface repeat gate 的结果只能是 `negative_eval_only`、`memory_only` 或 `prohibited`。
- 公开靶场训练若要声明为真实执行，必须通过 `tools/validate_real_execution_proof.py public-range-evidence` 并取得 `REAL_EXECUTION_PASS`；缺少 `execution_proof` 的 evidence 只能算 `STRUCTURE_ONLY`。
- 状态必须拆成两层：`execution_status` 只说明是否真实执行过，`capability_status` 才说明能力参与资格。`REAL_EXECUTION_PASS` 不等于 `positive_allowed`。
- dummy/local/provider testing key 只能证明流程、采集、状态机和边界负例；没有最终业务 API backend acceptance 和 repeat direct interface acceptance 时，不能证明真实业务能力。

## Tool Policy

- 开始 loop 前 Read `4-通用规范层/karpathy-guidelines/SKILL.md`。
- 涉及 Web/H5 逆向执行时 Read `1-业务流程层/reverse-js-crawler/SKILL.md`。
- 涉及评分/准入/漂移时 Read `1-业务流程层/skills-evaluation-governance/SKILL.md`。
- 涉及抓包、多轮复测、清 cookie/storage/cache、并发、session/cache 时 Read `99-SKILLS治理/16-实战复测与证据新鲜度规约.md` 和 `reverse-js-crawler/references/web-h5-crawler-hardening.md`。
- 涉及真实执行标准化、并发验收、风控证据、网页一致性或 metrics 时 Read `references/real-execution-standard.md` 和 `reverse-js-crawler/references/crawler-acceptance-pack.md`。
- 每次修改 loop 结构、角色规则、runner、acceptance、metrics 或 freshness gate 后跑 `python tools/validate_web_h5_loop_gate.py`、`python tools/validate_web_h5_real_execution_gate.py` 和 `python tools/ci_gate.py .ci-out`。
- 每次新增或修改公开靶场 evidence 后跑 `python tools/validate_public_range_evidence.py public-range-evidence`，并保留本轮 ledger/report 的结构校验结果。

## Boundaries

- 本 skill 只适用于 Web/H5 逆向、采集、接口复现和能力治理。
- 不负责生成 WAF/CAPTCHA 绕过方案；遇到保护只做证据、分类、授权范围和人工复核。
- 不把多 agent loop 写成无限自动化；必须有 token/成本、迭代次数和人工接管边界。
- 不把一次本地 loop gate 通过泛化成真实站点稳定。
- 不把风险控制写成绕过能力；并发实现只允许隔离、退避、停止、session retirement、fresh replay 和人工复核。

## Governance

- Version: 0.2.2
- Status: business-data-assertion gate baseline
- Change log: record role/gate/eval changes in `references/governance.md`.
- Drift tests: rerun loop evals when role boundaries, stop conditions, evidence gates, or crawler hardening rules change.

## Evidence-Backed Phase 1 Update

- Evidence run_id: `run-20260629-091645-gocaptcha-local-dummy`, `run-20260629-091645-cloudflare-turnstile-local-dummy`, `run-20260629-091645-concurrency-localhost`.
- Triggered failure: previous public-range evidence could pass structure gates without proving a localhost service, browser screenshot, network summary, or 1/2/5/10 worker ladder.
- Skill change: require `execution_proof` and the real-execution proof validator before a public-range loop run counts as real execution; require separate `capability_status` before any positive capability claim.
- Added eval: `evals/010-real-execution-proof-required.yaml`.
- Regression commands: `python tools/validate_real_execution_proof.py public-range-evidence`; `python tools/validate_web_h5_loop_gate.py`.

Phase 1 classification: the local dummy CAPTCHA, local Turnstile dummy, and localhost concurrency runs prove the real execution framework and local dummy ranges run. They do not prove real CAPTCHA/WAF/risk-control positive capability, real third-party Turnstile/reCAPTCHA/hCaptcha/GeeTest capability, fingerprint handling, production high concurrency, or universal CAPTCHA solving.

## Evidence-Backed Phase 2 Update

- Evidence run_id: `run-20260630-013842-high-fidelity-risk-lab`.
- Triggered failure evidence: Phase 1 had no server-side risk state machine, no one-time token lifecycle, no challenge-before business API failure vs challenge-after business API success, no direct interface repeat against the final business API, no cross-worker token pollution rejection, and no business API 1/2/5/10 worker ladder.
- Skill change: a local risk lab can be `positive_allowed` only for self-owned localhost risk-state engineering when evidence proves final business API acceptance, direct and repeat direct interface acceptance without browser profile/storage/manual token reuse, negative token/session/action/worker evals, and a business API concurrency ladder.
- Added eval: `evals/011-high-fidelity-risk-lab-positive-boundary.yaml`.
- Regression commands: `python tools/run_phase2_high_fidelity_risk_lab.py`; `python tools/validate_public_range_evidence.py public-range-evidence`; `python tools/validate_real_execution_proof.py public-range-evidence`; `python tools/validate_web_h5_loop_gate.py`.

Phase 2 classification: this is a positive local-lab capability for self-owned server-side token lifecycle, direct interface repeat, negative eval coverage, fingerprint diagnostics recording, and localhost business API concurrency isolation. It is still not real third-party CAPTCHA/WAF/risk-control bypass, production fingerprint handling, or external high-concurrency acceptance.

## Evidence-Backed Phase 2.1 Update

- Evidence run_id: `run-20260630-022227-high-fidelity-risk-lab`.
- Triggered failure evidence: `run-20260630-013842-high-fidelity-risk-lab` and `run-20260629-085616-scrapethissite` had interface/control-flow success but no `business_data_assertions`; under v2.1 they were downgraded to `memory_only`.
- Skill change: LOOP positive delivery now requires four layers: `execution_status=REAL_EXECUTION_PASS`, `control_flow_status=CONTROL_FLOW_PASS`, `business_data_status=DATA_ASSERTION_PASS`, and `capability_status=positive_allowed`.
- Added eval: `evals/012-business-data-assertion-required.yaml`.
- Regression commands: `python tools/validate_business_data_assertions.py public-range-evidence`; `python tools/validate_public_range_evidence.py public-range-evidence`; `python tools/web_h5_acceptance_report.py validate --report <report> --require-complete`; `python tools/ci_gate.py .ci-out`.

Phase 2.1 classification: link pass, HTTP 200, JSON Pointer presence, challenge verify success, direct repeat, and worker PASS are not sufficient. Positive LOOP acceptance must prove final business API data consistency with a server-side business ledger, negative eval `ledger_delta=0`, unique orders, and order/session/worker ownership.

## Evidence-Backed Phase 3.5 Update

- Evidence run_id: `run-20260630-041500-phase3-5-longrun`.
- Failure evidence: `public-range-evidence/longrun/phase3-5/run-20260630-041500-phase3-5-longrun/failure-cases.json` and `public-range-evidence/longrun/phase3-5/run-20260630-041500-phase3-5-longrun/issue-ledger.json`.
- Skill change: longrun LOOP work must include CAPTCHA metrics, JS runtime parity repeat, fingerprint diagnostics, business API concurrency ladder, chaos rejection cases, issue ledger, experience cards, regression evals, and capability decision.
- Added eval: `evals/longrun/phase3-5/001-phase3-5-longrun-regression.yaml`.
- Regression commands: `python tools/phase3_longrun_runner.py --config configs/phase3_longrun.yaml`; `python tools/validate_public_range_evidence.py public-range-evidence`; `python tools/validate_real_execution_proof.py public-range-evidence`; `python tools/validate_business_data_assertions.py public-range-evidence`; `python tools/ci_gate.py .ci-out`.

Phase 3.5 classification: longrun can fix local framework gaps and produce failure-driven rules. It remains `memory_only` unless the final business API has `DATA_ASSERTION_PASS`; it is not proof of third-party CAPTCHA/WAF/risk-control capability.

## Phase 3.8 Scope-Aware Real Website Handling

- Evidence run_id: `run-20260630-101500-phase3-8-family-hardening`.
- Evidence: `public-range-evidence/gocaptcha-official/run-20260630-101500-phase3-8-family-hardening.json`, `public-range-evidence/opencaptchaworld/run-20260630-101500-phase3-8-family-hardening.json`, and `public-range-evidence/raw/skills-page-impact-audit/run-20260630-101500-phase3-8-family-hardening/skills-page-impact-audit.json`.
- Evals: `evals/phase3-8/001-opencaptcha-answer-field-leakage.yaml`, `evals/phase3-8/004-gocaptcha-family-capability-split.yaml`, `evals/phase3-8/007-fingerprint-diagnostics-observation-only.yaml`, `evals/phase3-8/008-js-runtime-parity-boundary.yaml`.
- Step 1 scope classification: `localhost_lab`, `public_range`, `local_open_source_range`, `self_owned`, `authorized_target`, `official_demo`, `unknown_third_party`, `production_unverified`.
- Step 2 challenge detection fields: provider, challenge_family, challenge_type, visual assets, instruction text, action schema, API endpoints, session binding, token binding, risk state, and answer-shaped leakage fields.
- Step 3 route selection: visual solver/action planner for in-scope ranges; JS/V8 parity only for authorized runtime parity; fingerprint diagnostics only observation; business API replay only with allowed_hosts and business data assertions.
- Step 4 acceptance evidence: execution_status, capability_status, business_data_status, per-family metrics, redaction/leakage audit, blackbox gate, failure cases, evals, experience cards, direct repeat when applicable, and concurrency ladder when capability claims include concurrency.
- Weak success cannot mask strong failure. Localhost concurrency is not production high concurrency. Public range candidate is not third-party CAPTCHA/WAF/risk-control capability.

## Phase 3.9 Vendor And Shield Handling

- Evidence run_id: `run-20260630-113000-phase3-9-vendor-shield-range`.
- Evidence: `public-range-evidence/shumei-compatible-lab/run-20260630-113000-phase3-9-vendor-shield-range.json`, `public-range-evidence/aliyun-compatible-lab/run-20260630-113000-phase3-9-vendor-shield-range.json`, and `public-range-evidence/five-second-shield-lab/run-20260630-113000-phase3-9-vendor-shield-range.json`.
- Playbook: `docs/REAL_WEBSITE_HANDLING_PLAYBOOK.md`.
- Evals: `evals/phase3-9/shumei-compatible-lab-compatible-lab.yaml`, `evals/phase3-9/aliyun-compatible-lab-compatible-lab.yaml`, `evals/phase3-9/five-second-shield-lab.yaml`.
- Real website flow: scope decision first; detect CAPTCHA/WAF/JS signature/fingerprint/rate-limit/auth/business block; choose visual solver, human-in-loop, JS parity, official API, backoff, authorized adapter, business assertions, or stop for authorization.
- For WAF/JS challenge, success requires challenge-to-business API closure, direct repeat, negative eval ledger_delta=0, and clearance/session/worker binding under concurrency.

## Phase 3.10 Realism And Integration Readiness

- Evidence run_id: `run-20260630-163000-phase3-10-realism-hardening`.
- Evidence: `public-range-evidence/shumei-compatible-lab/run-20260630-163000-phase3-10-realism-hardening.json`, `public-range-evidence/aliyun-compatible-lab/run-20260630-163000-phase3-10-realism-hardening.json`, `public-range-evidence/five-second-shield-lab/run-20260630-163000-phase3-10-realism-hardening.json`, and `public-range-evidence/raw/challenge-realism-audit/run-20260630-163000-phase3-10-realism-hardening/challenge-realism-audit.json`.
- Scope: compatible labs train only; local WAF lab proves local business-data closure; official vendor trials require private self-owned config.
- Capability level: scoped `positive_candidate` only; no stable_positive and no verified vendor solver.
- Boundary: do not write Shumei/Aliyun verified, five-second shield real bypass, production high concurrency, or real third-party CAPTCHA/WAF capability.
- Failure cases: hard/adversarial wrong_prediction rows and shield negative eval ledger_delta=0 are mandatory feedback.
- Eval: `evals/phase3-10/shumei-compatible-lab-hardening.yaml`, `evals/phase3-10/aliyun-compatible-lab-hardening.yaml`, and `evals/phase3-10/five-second-shield-lab-dynamic.yaml`.
- Next training goal: failure replay fixes, self-owned official trial, and longrun soak before verified/stable promotion.

## References

- `references/loop-roles.md`: 三角色或多角色 agent 职责、输入输出和交接规则。
- `references/loop-ledgers.md`: Loop Ledger、Stop Ledger、Human Review Ledger 和 Cleanup Ledger 模板。
- `references/real-execution-standard.md`: Loop Runner、acceptance report、fixture freshness、metrics 和真实完成口径。
- `references/governance.md`: versioning, source patterns, local gates, drift policy.
## Phase 3.11 evidence-first loop gate

- source_run_id: `run-20260630-173000-phase3-11-type-matrix`
- evidence: `public-range-evidence/shumei-compatible-lab/run-20260630-173000-phase3-11-type-matrix.json`, `public-range-evidence/aliyun-compatible-lab/run-20260630-173000-phase3-11-type-matrix.json`, `public-range-evidence/five-second-shield-lab/run-20260630-173000-phase3-11-type-matrix.json`
- evals: `evals/phase3-11/phase3-11-loop-gate.yaml`
- Do not promote memory_only or local-only evidence into verified production ability. Every loop must report execution_status, capability_status, scope_decision, leakage audit, blackbox gate, realism audit, business data assertions where applicable, and failure evidence retest status.
- If a real website scope is unknown, the loop stops at observation_only and emits blocked_authorization_required for interactive action.
## Phase 3.12 model flywheel loop

- source_run_id: `run-20260630-183000-phase3-12-model-flywheel`
- evidence: `datasets/captcha_flywheel/manifests/run-20260630-183000-phase3-12-model-flywheel/dataset_manifest.json`
- evals: `evals/phase3-12/`
- The loop is data collection -> label manifest -> train/val/test split -> local/open-source model training -> evaluation -> action replay -> failure replay -> SKILLS update.
- Any run using third-party solver platforms, remote solver APIs, copied browser tokens, copied clearance cookies, DOM answers, query expected values, or server expected values must be INVALID/prohibited.
