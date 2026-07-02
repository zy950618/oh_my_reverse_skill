---
name: skills-evaluation-governance
description: >-
  Use this skill to score, refine, backtest, and govern Codex/Claude skills: assess whether notes are installable skills, create evals, prepare Skill Bench structure, compare SKILL.md quality, define trigger/negative-trigger tests, track drift, maintain versions, record changes, and enforce admission gates for new Skills. Trigger when the user asks to rate skills, use Skill Bench, convert notes into usable skills, evaluate trigger accuracy, maintain a skills library, score a new Skill before accepting it, run backtests, or Chinese requests such as SKILLS评分, 技能评分, 可用SKILLS, 新增Skill准入, Skill Bench跑分, 回测, 漂移测试, 长期治理, 版本号, 变更记录, 触发词优化, 负例测试, or 技能库治理.
platforms: [cross-platform]
---

# Skills Evaluation Governance

## Do NOT Trigger When

- 用户在做实际业务任务（实现某个接口、修某个 bug、跑某个测试）→ 不要把"治理"当万能锤
- 用户只是问"这个 skill 是干嘛的" → 直接回答 description，不用本 skill 评分
- 用户要求"创建一个新 skill" → 用 `skill-creator:skill-creator`（plugin）；本 skill 用于评分/准入，不用于创建
- 用户只问"看一下当前评分" → 直接读 `99-SKILLS治理/05-当前评分与回测结果.md`，不必走完整评分流程
- 用户要求"改某个 skill 的 description"等具体修改 → 直接改对应 SKILL.md，不必整套评分

## Purpose

把经验笔记升级为可安装、可触发、可评测、可回测、可持续改进的 Skills。评分时必须区分笔记质量、Skill 包质量、Skill Bench 可跑性、站点经验沉淀和长期漂移风险。

新增 Skill 不能直接进入“可用”。必须先完成评分、回测、版本记录和准入判断。

## Rubric

Score separately:

- Knowledge quality: domain depth, examples, templates.
- Skill package quality: `SKILL.md`, frontmatter, concise workflow, references.
- Trigger quality: description can trigger correct tasks and avoid near-miss tasks.
- Eval quality: positive and negative prompts, criteria, repeatability.
- Site memory quality: test logs become known failures, market matrix, eval backlog, and change log.
- Operational quality: CI, drift tracking, versioning, install path.
- Karpathy behavior quality: assumptions surfaced, scope kept narrow, success criteria verifiable, changes traceable to the request.
- Evidence/review quality: validation ledger, refusal ledger, human review gate, monitoring plan, and error-correction memory updates.

## Workflow

0. 站点记忆评估：
   - 检查是否存在站点经验库、市场矩阵、已知失败、测试日志提炼、eval backlog、change log。
   - 判断同域名不同 market/locale/currency/stage 是否被分开治理。

1. 只读评估：
   - 统计 `SKILL.md`、`evals/`、`agents/openai.yaml`、`references/`。
   - 判断是笔记库、模板库，还是可安装 Skill。

2. 设计 eval：
   - 至少包含正例、边界例、负例。
   - criteria 要能客观判断，不写空泛评价。

3. 接 Skill Bench：
   - Skill 路径必须仓库可见。
   - CI 需要 API key secret。
   - 本地结构校验不等于官方跑分。

4. 迭代：
   - 根据失败 eval 调整 description 或 workflow。
   - 从正常测试日志提炼失败模式，写回站点经验库。
   - 不为了通过 eval 过拟合单个案例。

5. 新 Skill 准入：
   - 检查 `99-SKILLS治理/04-新增SKILL评分回测准入.md`。
   - 跑 quick_validate 和 `scripts/score_skills.py`。
   - 回测至少一个正例、一个负例、一个历史回归例。
   - 更新 `99-SKILLS治理/05-当前评分与回测结果.md`。

6. 防虚幻治理：
   - 检查是否要求证据、验证、拒答、人工复核和监控。
   - 检查错误发生后是否更新 memory / known-failures / eval / 图谱 / impact-regression。
   - 检查错误代码、废弃输出和历史遗留是否被删除、迁移或登记为 legacy debt。
   - 检查是否拒绝把辱骂性前缀、人格化称谓或情绪化口头禅写入强制交付格式。

## Karpathy Checks

这些原则用于评价 Skill 行为，不替代后续 AGENT 编码规则：

- 不默默假设：Skill 要求先分类、列证据、标注未知。
- 不过度复杂：Skill 不吞掉相邻任务，复杂细节放 references。
- 精准处理：每个 Skill 只解决清晰边界内的问题。
- 目标驱动：必须有可验证成功标准和回测闭环。

## Success Criteria

- 新 Skill 没有绕过准入评分。
- 评分结果区分结构校验、本地回测和官方 Skill Bench 跑分。
- 每个 Skill 至少有正例、负例和回归/边界 eval。
- 测试日志中的重复失败能进入站点经验库或 eval backlog。
- Web/H5 爬虫类 Skill 必须检查 fresh capture、clean-state retest、anti-flake repeatability、concurrency ladder 和 session/cache isolation。
- Web/H5 实战执行类 Skill 必须检查 Loop Runner ledger、Acceptance Report、risk-control concurrency、UI/API parity、fixture freshness 和 quantitative metrics。
- public-range evidence 必须区分 `REAL_EXECUTION_PASS`、`STRUCTURE_ONLY`、`BLOCKED` 和 `INVALID`；没有 `execution_proof` 的 JSON 不能作为真实实战进化证据。
- 改动后版本、变更记录和漂移测试要求同步更新。
- 证据、验证、拒答、人工复核、监控和错误纠正都有明确门槛。

## Tool Policy

- **开始实现前 Read `~/.claude/skills/karpathy-guidelines/SKILL.md`**,确认 4 条原则:Think Before Coding / Simplicity First / Surgical Changes / Goal-Driven Execution。这是基础层规范,所有执行类 skill 强制依赖。
- **遇到逆向运行时问题(断点/时间/cookie/TLS 指纹/风控恢复/接口变更)Read `~/.claude/skills/oh_my_reverse_skill/99-SKILLS治理/10-逆向运行时常见问题.md`**。
- **输出结论、扩范围或做并发前 Read `~/.claude/skills/oh_my_reverse_skill/99-SKILLS治理/11-AI事实证据规约.md` / `12-反泛化与任务收敛规约.md` / `13-并发指纹与会话隔离规约.md`**。
- **改端点/字段/状态/保护/实现/eval 前后 Read `14-知识图谱行程与关联规约.md` / `15-AI变更风险与回归校验规约.md`,并更新 knowledge-graph.md / impact-regression.md**。
- **涉及证据不足、验证失败、拒答、人审、监控、错误纠正或历史遗留时 Read `18-证据验证拒答人工复核与监控规约.md`,并输出对应 ledger**。

## Boundaries

- 用户只要求评分时，不改文件。
- 用户要求整合、创建、准入或治理时，才写入目标目录。
- AGENT 编码规则后续单独沉淀，不混入 Skill 评分包。
- 不把“本地格式通过”说成“官方 Skill Bench 已跑分”。

## Governance

When scoring crawler/reverse Skills, include site memory quality: test logs should produce known failures, market matrix updates, eval backlog entries, and version changes.

When a new real website task reveals a repeated gap, update the relevant Skill, add or revise evals, record the version change, and schedule drift testing. Do not let the skills library become static notes.

- Version: 0.4.3
- Status: business-data-assertion governance baseline
- Change log: record material trigger, workflow, reference, score, and eval changes in `references/governance.md`.
- Drift tests: rerun evals after changing descriptions, adding new cases, or after important real-world failures.
- Review cadence: update examples and negative triggers when repeated user corrections show a gap.

## Evidence-Backed Phase 1 Update

- Evidence run_id: `run-20260629-091645-gocaptcha-local-dummy`, `run-20260629-091645-cloudflare-turnstile-local-dummy`, `run-20260629-091645-concurrency-localhost`.
- Triggered failure: local structure and public-range validators alone did not separate real execution proof from structure-only evidence.
- Skill change: governance review must require `tools/validate_real_execution_proof.py` output and must not count `STRUCTURE_ONLY` files as real-run evidence.
- Added eval: `evals/023-real-execution-proof-required.yaml`.
- Regression commands: `python tools/validate_real_execution_proof.py public-range-evidence`; `python tools/ci_gate.py .ci-out`.

## Evidence-Backed Phase 2 Update

- Evidence run_id: `run-20260630-013842-high-fidelity-risk-lab`.
- Triggered failure evidence: Phase 1.1 governance separated `execution_status` from `capability_status`, but still lacked a high-fidelity local target with server-side token state, final business API direct repeat, negative token lifecycle evals, and a business API concurrency ladder.
- Skill change: governance admission may count this run as `positive_allowed` only within the self-owned localhost risk-lab scope after `validate_public_range_evidence` and `validate_real_execution_proof` pass; it must keep third-party CAPTCHA/WAF/fingerprint/production concurrency claims unverified.
- Added eval: `evals/024-high-fidelity-risk-lab-governance-boundary.yaml`.
- Regression commands: `python tools/run_phase2_high_fidelity_risk_lab.py`; `python tools/validate_public_range_evidence.py public-range-evidence`; `python tools/validate_real_execution_proof.py public-range-evidence`; `python tools/ci_gate.py .ci-out`.

Phase 2 classification: governance now has one positive local-lab evidence item for final business API acceptance, direct interface repeat, negative eval coverage, and worker isolation. It remains a local-range result, not official Skill Bench scoring and not real third-party risk-control capability.

## Evidence-Backed Phase 2.1 Update

- Evidence run_id: `run-20260630-022227-high-fidelity-risk-lab`.
- Triggered failure evidence: historical `positive_allowed` evidence without server-side business ledger or `business_data_assertions` could overclaim interface/control-flow success as business success.
- Skill change: governance admission now requires four distinct statuses and downgrades any positive evidence missing `business_data_status=DATA_ASSERTION_PASS`.
- Added eval: `evals/025-business-data-assertion-governance.yaml`.
- Regression commands: `python tools/validate_business_data_assertions.py public-range-evidence`; `python tools/validate_public_range_evidence.py public-range-evidence`; `python tools/validate_real_execution_proof.py public-range-evidence`; `python tools/ci_gate.py .ci-out`.

Phase 2.1 classification: `positive_allowed_count` is counted only after execution, control-flow, and business-data gates pass. Evidence that only proves direct replay or control-flow remains `memory_only`, `negative_eval_only`, or `unverified`.

## References

- `references/scorecard-rubric.md`: stricter scorecard and backtest rubric based on Skill Creator plus Karpathy-style behavior checks.
- `references/site-memory-scoring.md`: site memory, market matrix, test-log mining, eval backlog, and change-log scoring.
- `references/governance.md`: versioning, change log, and drift-test policy.
- `references/scoring-rubric.md`: scoring details.
- `references/skill-bench.md`: Skill Bench setup requirements.

## Evidence-Backed Phase 3.5 Update

- Evidence run_id: `run-20260630-041500-phase3-5-longrun`.
- Failure evidence: `public-range-evidence/longrun/phase3-5/run-20260630-041500-phase3-5-longrun/failure-cases.json` and `public-range-evidence/longrun/phase3-5/run-20260630-041500-phase3-5-longrun/issue-ledger.json`.
- Skill change: governance admission now requires longrun issue ledger, experience cards, regression evals, and capability-decision output before any Phase 3 CAPTCHA/runtime/fingerprint hardening can be discussed.
- Added eval: `evals/longrun/phase3-5/001-phase3-5-longrun-regression.yaml`.
- Regression commands: `python tools/phase3_longrun_runner.py --config configs/phase3_longrun.yaml`; `python tools/validate_public_range_evidence.py public-range-evidence`; `python tools/validate_real_execution_proof.py public-range-evidence`; `python tools/validate_business_data_assertions.py public-range-evidence`; `python tools/ci_gate.py .ci-out`.

Phase 3.5 classification: longrun evidence can harden local baselines and governance gates. It remains `memory_only` unless final business API data assertions pass; it is not real third-party CAPTCHA/WAF capability.

## Evidence-Backed Phase 3.6 Update

- Evidence run_id: `run-20260630-053000-phase3-6-public-model`.
- Training evidence: `public-range-evidence/raw/captcha-model-training/run-20260630-053000-phase3-6-public-model/model-eval.json`.
- Public/local action replay evidence: `public-range-evidence/gocaptcha-local/run-20260630-053000-phase3-6-public-model.json`.
- Public fingerprint diagnostics evidence: `public-range-evidence/fingerprint-diagnostics/run-20260630-053000-phase3-6-public-model-sannysoft.json`.
- Skill change: governance now distinguishes local solver improvement, public/local action replay pass, observation-only fingerprint diagnostics, and public evidence `positive_allowed`.
- Added evals: `evals/phase3-6/001-model-training-improves-text-ocr.yaml`, `evals/phase3-6/002-gocaptcha-local-action-replay.yaml`, `evals/phase3-6/003-fingerprint-public-diagnostics.yaml`.
- Regression commands: `python tools/captcha_model_train.py --run-id <run_id>`; `python tools/captcha_model_eval.py --run-id <run_id>`; `python tools/captcha_action_replay_lab.py --target gocaptcha-local --run-id <run_id>`; `python tools/captcha_leakage_audit.py --run-id <run_id>`; `python tools/capability_promotion_gate.py --run-id <run_id>`.

Phase 3.6 classification: text OCR has a measured local model improvement and GoCaptcha-local action replay executed. Public evidence remains non-positive without final business API `DATA_ASSERTION_PASS`.

## Evidence-Backed Phase 3.10 Update

- Evidence run_id: `run-20260630-163000-phase3-10-realism-hardening`.
- Evidence: `public-range-evidence/shumei-compatible-lab/run-20260630-163000-phase3-10-realism-hardening.json`, `public-range-evidence/aliyun-compatible-lab/run-20260630-163000-phase3-10-realism-hardening.json`, `public-range-evidence/five-second-shield-lab/run-20260630-163000-phase3-10-realism-hardening.json`, and `public-range-evidence/raw/challenge-realism-audit/run-20260630-163000-phase3-10-realism-hardening/challenge-realism-audit.json`.
- Evals: `evals/phase3-10/shumei-compatible-lab-hardening.yaml`, `evals/phase3-10/aliyun-compatible-lab-hardening.yaml`, and `evals/phase3-10/five-second-shield-lab-dynamic.yaml`.
- Scope: local compatible labs and local WAF lab only; self-owned official trial adapters are BLOCKED without private config.
- Capability level: family-scoped `positive_candidate`; no `stable_positive`, no verified vendor solver, and no production WAF bypass.
- Failure cases: realism audit requires hard/adversarial failures or sufficient difficulty evidence; 100/100 p95=0 cannot promote beyond candidate.
- Next training goal: require self-owned official trial evidence, longrun soak, failure replay fixes, and repeated drift gates before verified/stable.
