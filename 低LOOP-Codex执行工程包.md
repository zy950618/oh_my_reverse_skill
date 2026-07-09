# 低 LOOP Codex 执行工程包

> 生成日期: 2026-07-08  
> 最近更新: 2026-07-09 / `LCL-20260708-04` install-safe-uninstall consolidation  
> 角色定位: Claude 负责计划设计、分支状态监督、Codex 任务下发、独立审查、验证判定和下一轮决策；Codex 只负责在指定分支和指定范围内执行补丁。  
> 适用范围: `oh_my_reverse_skill` 仓库的轻量结构闭环 / Low-Cost Structure Loop，包括文档、manifest、安装/卸载、GUI、score 输出、JS runtime 证据治理、外部能力融合拆解。  
> 安全边界: 本工程包不授权 WAF 绕过、指纹伪造、clearance-cookie 复用、验证码绕过、真实扣款、未授权目标、raw cookie/token/profile 落盘。

## 当前权威状态 / Latest Execution State

```yaml
latest_execution_state:
  observed_at: 2026-07-09
  integration_branch: test
  active_objective: LCL-20260708-04
  active_branch: loop/20260708-04-install-safe-uninstall-consolidation
  active_topic: install_safe_uninstall_consolidation
  execution_source: 低LOOP-Codex执行工程包.md
  capability_claim: STRUCTURE_ONLY
  prior_objectives:
    - task_id: LCL-20260708-03
      topic: manifest_single_source
      status: OBSERVED_MERGED_TO_TEST
      evidence:
        - commit: f68998f Merge LCL-20260708-03 manifest design
        - branch_observed: loop/20260708-03-manifest-design
        - files_observed:
            - skills-manifest.json
            - tools/skills_manifest.py
            - 00-SKILLS索引.md
            - INSTALL.md
  active_objective_scope:
    in_scope:
      - update this engineering pack as the single execution authority
      - record LCL-03 as inherited prerequisite evidence
      - land manifest-driven safe uninstall checks for INSTALL.md
      - create one execution log, verification report, acceptance report, and cleanup ledger
    out_of_scope:
      - score JSON output stabilization
      - JS runtime evidence manifest
      - real-domain replay or production capability claims
      - WAF/challenge/fingerprint defeat
  scattered_supplement_policy:
    低LOOP-Codex执行工程包.md: authoritative_execution_source
    低LOOP执行-拉取卸载与再生成方案.md: historical_design_only_after_migration
    SKILLS融合建议与能力缺口处理.md: source_gap_notes_only_after_migration
  completion_claim_allowed_only_when:
    - branch_state_recorded
    - LCL-03 prior evidence recorded
    - LCL-04 validation commands passed
    - cleanup_ledger_written
    - verify_delivery_domain_none_passed
```

本状态只证明 low-cost structure loop 的结构治理闭环；不证明真实站点接口、sign/token、并发、WAF/challenge 或生产可用能力。

---

## 0. 为什么需要这个工程包

`低LOOP执行-拉取卸载与再生成方案.md` 已经定义了规则、状态机和融合方向，但它仍偏“规则设计稿”。Codex 需要的是一个可以直接接收、执行、回报、被 Claude 审核、被工具验证的工程包。

本文件补齐 6 类执行资产：

| 类别 | 名称 | 解决的问题 |
|---|---|---|
| 1 | Codex 任务包模板 | Codex 拿到后知道分支、目标、允许文件、禁止事项、输出格式 |
| 2 | 分支状态机执行账本 | 每轮从 `test` 开分支、验证、合并、下一轮都有机器可读记录 |
| 3 | 验证命令矩阵 | 不同任务类型对应固定验证命令，避免“口头通过” |
| 4 | Claude 审核评分表 | Claude 不直接相信 Codex，自定义审查标准和阻断条件 |
| 5 | 自动续 loop 决策器 | 真实验证通过后才继续下一 loop，失败则阻断或人审 |
| 6 | 外部能力融合执行包 | `ai-reverse-toolkit` / `jshook-skill` / `hello_js_reverse_skill` 如何拆、加、用、融合 |

---

## 1. 总控原则

### 1.1 Claude 与 Codex 的职责边界

```yaml
roles:
  claude:
    planner: true
    supervisor: true
    auditor: true
    gatekeeper: true
    can_merge_decide: true
    can_accept_codex_claim_without_review: false
  codex:
    executor: true
    patch_producer: true
    evidence_reporter: true
    can_merge: false
    can_expand_scope: false
    can_claim_done: false
```

### 1.2 每轮强制分支规则

```yaml
branch_policy:
  integration_branch: test
  direct_edit_on_test: forbidden
  branch_required_per_loop: true
  branch_name: loop/<YYYYMMDD>-<nn>-<topic>
  merge_back_to: test
  next_loop_after_merge_only: true
```

### 1.3 单主题规则

每个 loop 只能处理一个主题：

```yaml
single_topic_only:
  allowed_topic_types:
    - doc
    - manifest
    - install
    - gui
    - score
    - js_runtime
    - external_fusion
    - validator
    - cleanup
  forbidden:
    - one_branch_multiple_unrelated_topics
    - opportunistic_refactor
    - fixing_unrequested_files
```

---

## 2. Codex 任务包模板

Claude 每次交给 Codex 的 prompt 必须包含以下 YAML。缺字段不得启动 Codex。

```yaml
codex_task_package:
  schema_version: 1.0
  task_id: LCL-YYYYMMDD-NN
  title:
  base_branch: test
  branch: loop/<YYYYMMDD>-<nn>-<topic>
  topic_type: doc | manifest | install | gui | score | js_runtime | external_fusion | validator | cleanup
  objective:
  context_files:
    - path:
      why_read:
  allowed_files:
    - path:
      allowed_change:
  forbidden_files:
    - path:
      reason:
  hard_constraints:
    - do_not_edit_test_directly
    - do_not_change_files_outside_allowed_files
    - do_not_claim_real_site_success_from_structure_pass
    - do_not_persist_raw_cookie_token_profile_storage
    - do_not_create_waf_defeat_or_fingerprint_falsification
  required_outputs:
    - diff_summary
    - files_changed
    - commands_run
    - validation_result
    - known_gaps
    - risk_notes
    - rollback_notes
  validation_commands:
    - command:
      expected:
      required_for_merge: true | false
  success_criteria:
    - criterion:
      evidence_required:
  stop_conditions:
    - scope_expansion_needed
    - validation_failed
    - raw_secret_risk
    - human_review_required
    - merge_conflict
```

### 2.1 Codex prompt 模板

```text
你是本轮 Low-Cost Structure Loop 的 Codex Executor。

只在分支 `<branch>` 上工作，base 是 `test`。
只允许修改：
<allowed_files>

禁止修改：
<forbidden_files>

任务目标：
<objective>

硬约束：
1. 不得直接修改 test。
2. 不得扩大范围。
3. 不得保存 raw cookie/token/profile/storage。
4. 不得把 structure-only 说成真实站点成功。
5. 不得实现 WAF 绕过、指纹伪造、验证码绕过或 clearance-cookie 复用。

完成后必须输出：
- diff_summary
- files_changed
- commands_run
- validation_result
- known_gaps
- risk_notes
- rollback_notes

如果无法完成，停止并输出 CODEX_BLOCKED，不要猜测或硬改。
```

### 2.2 Codex 返回模板

```yaml
codex_result:
  task_id:
  branch:
  status: CODEX_DONE | CODEX_BLOCKED
  files_changed:
  diff_summary:
  commands_run:
    - command:
      exit_code:
      key_output:
  validation_result:
    status: pass | fail | not_run
    reason:
  known_gaps:
  risk_notes:
  rollback_notes:
  requested_next_action:
```

---

## 3. 分支状态机执行账本

每轮必须维护一个 branch ledger。可以先以 Markdown/YAML 写在任务记录中，后续可拆成 JSON 文件。

```yaml
branch_execution_ledger:
  schema_version: 1.0
  task_id:
  loop_id:
  topic:
  state:
  base_branch: test
  branch:
  created_from_commit:
  codex_session_id:
  timestamps:
    planned_at:
    branch_created_at:
    codex_assigned_at:
    codex_done_at:
    claude_audit_at:
    validation_at:
    merged_to_test_at:
  state_history:
    - from:
      to:
      evidence:
      by: Claude | Codex | Human
  changed_files:
  validators:
  merge_record:
  next_loop:
```

### 3.1 状态枚举

```yaml
success_path:
  - PLANNED
  - BRANCH_CREATED
  - CODEX_ASSIGNED
  - CODEX_DONE
  - CLAUDE_REVIEWING
  - VALIDATING
  - VALIDATED
  - MERGE_READY
  - MERGED_TO_TEST
  - NEXT_LOOP_PLANNED
failure_states:
  - CODEX_BLOCKED
  - CLAUDE_REJECTED
  - VALIDATION_FAILED
  - MERGE_CONFLICT
  - HUMAN_REVIEW_REQUIRED
  - STOPPED
```

### 3.2 合并前门槛

```yaml
merge_gate:
  base_is_test: true
  branch_not_test: true
  codex_status: CODEX_DONE
  claude_audit: PASS
  validation_status: PASS
  verify_delivery: PASS
  unresolved_blockers: []
  human_review_required: false
  rollback_plan_exists: true
```

### 3.3 合并后门槛

合并回 `test` 后必须在 `test` 上重复关键验证：

```yaml
post_merge_gate:
  branch: test
  git_status_clean_or_expected: true
  repeated_validators: PASS
  verify_delivery: PASS
  next_loop_decision_written: true
```

---

## 4. 验证命令矩阵

不同任务类型使用不同验证集合。Claude 只能根据实际任务选择，不得用无关验证充数。

### 4.1 通用验证

```yaml
common_validators:
  - command: git status --short
    purpose: 确认工作区只包含本轮预期文件
  - command: git diff --stat
    purpose: 查看变更范围
  - command: python3 tools/web_h5/verify_delivery.py --domain none
    purpose: 仓库维护类任务完成 gate
```

### 4.2 文档 / 规则任务

```yaml
doc_validators:
  - command: git diff -- <target-doc>
    purpose: Claude 审核实际文档变更
  - command: python3 tools/web_h5/verify_delivery.py --domain none
    required_for_merge: true
```

### 4.3 LOOP / validator 任务

```yaml
loop_validators:
  - command: python3 tools/validators/validate_loop.py
    required_for_merge: true
  - command: python3 tools/web_h5/validate_web_h5_loop_gate.py
    required_for_merge: true
  - command: python3 tools/web_h5/verify_delivery.py --domain none
    required_for_merge: true
```

### 4.4 manifest / install / GUI 任务

```yaml
manifest_install_validators:
  - command: python3 tools/governance/score_skills.py --repo .
    required_for_merge: true
    caveat: 当前 stdout 可能不是单一 JSON，不能仅靠 json.load 判定
  - command: python3 tools/web_h5/verify_delivery.py --domain none
    required_for_merge: true
  - manual_check: INSTALL/CHERRY 不得硬编码旧 skill 数量
  - manual_check: 卸载命令不得删除非本仓库 skill 链接
```

### 4.5 score 输出任务

```yaml
score_validators:
  - command: python3 tools/governance/score_skills.py --repo . --json-out .ci-out/score-summary.json
    expected: 生成单一 JSON 文件
    required_for_merge: true
  - command: python3 -m json.tool .ci-out/score-summary.json
    expected: JSON parse pass
    required_for_merge: true
  - command: python3 tools/governance/ci_gate.py .ci-out
    required_for_merge: true
```

### 4.6 JS runtime / 脚本采集任务

```yaml
js_runtime_validators:
  - manual_check: 无 raw Cookie/token/profile/storage 示例
  - manual_check: scripts manifest 包含 sha256/captured_at/source_freshness/redaction_status/raw_secret_persisted
  - manual_check: runtime parity 不声明业务成功
  - command: python3 tools/web_h5/verify_delivery.py --domain none
    required_for_merge: true
```

### 4.7 真实 domain 任务升级验证

一旦任务触及真实 domain，不再使用低成本结构闭环完成声明，必须升级：

```yaml
real_domain_validators:
  - command: python3 tools/web_h5/web_h5_loop_runner.py validate --ledger <ledger> --require-complete
  - command: python3 tools/web_h5/web_h5_acceptance_report.py validate <report> --require-complete
  - command: python3 tools/web_h5/fixture_freshness_report.py <domain> --strict-fresh
  - command: python3 tools/web_h5/verify_delivery.py --domain <domain>
```

---

## 5. Claude 审核评分表

Claude audit 采用 100 分制；低于 90 不得合并。

| 维度 | 分值 | PASS 标准 | 阻断条件 |
|---|---:|---|---|
| 范围控制 | 15 | 只改 allowed_files | 修改 forbidden_files |
| 分支纪律 | 15 | 从 `test` 分支创建，未直接改 `test` | 直接在 `test` 改 |
| 设计一致性 | 15 | 不与 06/20/21/LOOP 冲突 | 新增旁路规范 |
| 验证真实性 | 15 | 命令真实运行、输出可复核 | 只写“应通过” |
| 安全边界 | 15 | 无 raw secret，无 WAF/指纹绕过 | 出现 raw token/cookie |
| 能力口径 | 10 | structure-only 不泛化 | 声称真实站点成功 |
| 可回滚性 | 10 | 单主题、可 revert | 多主题混合 |
| 下一轮清晰度 | 5 | next_loop 明确或停止原因明确 | 自动无限 loop |

### 5.1 Claude audit 输出

```yaml
claude_audit:
  score:
  result: PASS | FAIL | HUMAN_REVIEW_REQUIRED
  scope_control:
  branch_discipline:
  design_consistency:
  validation_truth:
  safety_boundary:
  capability_claim:
  rollback:
  next_loop:
  blockers:
  required_fixes:
```

### 5.2 硬阻断条件

以下任一出现，直接 FAIL，不看总分：

- 修改 forbidden files。
- 在 `test` 直接改动实现。
- 验证失败却请求合并。
- raw cookie/token/profile/storage 进入仓库内容。
- WAF/challenge defeat、fingerprint falsification、验证码绕过。
- 把 `STRUCTURE_PASS` 写成真实站点成功。
- 外部项目未准入就作为 active skill。

---

## 6. 自动续 loop 决策器

### 6.1 决策输入

```yaml
next_loop_decider_input:
  current_task_id:
  current_branch:
  current_state:
  merged_to_test:
  claude_audit_result:
  validation_result:
  verify_delivery_result:
  unresolved_blockers:
  human_review_required:
  max_loops:
  loops_completed:
  risk_level:
  proposed_next_task:
```

### 6.2 决策输出

```yaml
next_loop_decision:
  auto_continue_allowed: true | false
  decision: continue | stop | human_review | blocked
  next_task_id:
  next_branch:
  reason:
  required_user_confirmation: true | false
```

### 6.3 自动继续规则

允许自动继续：

```yaml
allow_continue_if:
  current_state: MERGED_TO_TEST
  claude_audit_result: PASS
  validation_result: PASS
  verify_delivery_result: PASS
  unresolved_blockers: []
  human_review_required: false
  loops_completed_less_than_max: true
  next_task_single_topic: true
  next_task_risk_level: low
```

必须停止：

```yaml
stop_if:
  - validation_failed
  - claude_audit_failed
  - human_review_required
  - merge_conflict
  - same_blocker_twice
  - next_task_touches_real_domain
  - next_task_requires_auth_or_payment_or_pii
  - max_loops_reached
```

---

## 7. 外部能力融合执行包

### 7.1 外部来源事实登记

```yaml
external_source_inventory:
  source_name: ai-reverse-toolkit | jshook-skill | hello_js_reverse_skill
  source_found: true | false
  source_path_or_url:
  source_type: template | runtime_hook | demo | tool | site_case | unknown
  license_status: known | unknown | not_applicable
  current_repo_evidence:
  allowed_use:
  forbidden_use:
  fusion_target:
  validation_required:
```

### 7.2 ai-reverse-toolkit 拆解执行

```yaml
ai_reverse_toolkit_fusion:
  source_status: historical_reference_or_unverified_external_template
  extract:
    - intake_template
    - routing_template
    - evidence_template
    - scope_template
  add_as:
    - reference
    - checklist
    - eval_seed
  do_not_add_as:
    - active_skill
    - production_capability
  target_layers:
    - 1-业务流程层 references
    - 99-SKILLS治理 planning/routing evidence rules
  validation:
    - no_duplicate_with_06_planning
    - no_claim_source_exists_without_file_or_url
    - no_site_specific_field_generalization
```

### 7.3 jshook-skill 拆解执行

```yaml
jshook_skill_fusion:
  source_status: unverified_external_or_missing_current_repo_entity
  extract:
    - fetch_xhr_hook_trace
    - crypto_function_input_output_trace
    - storage_access_observation
    - call_stack_capture
    - script_hash_binding
  add_as:
    - 2-layer reference
    - tool-contract candidate
    - future internal_tool candidate after eval
  do_not_add_as:
    - 1-layer external_entry
    - stealth_tool
    - fingerprint_falsification
    - waf_defeat
  target_layers:
    - reverse-js-crawler reference
    - find-crypto-entry reference
    - env-patch reference
    - js-page-runtime-parity evidence contract
  validation:
    - requires capture_id
    - requires script_url_and_sha256
    - requires input_output_sample
    - requires no_raw_secret_persisted
```

### 7.4 hello_js_reverse_skill 拆解执行

```yaml
hello_js_reverse_skill_fusion:
  source_status: demo_or_unverified_missing_entity
  extract:
    - minimal_positive_eval
    - negative_boundary_eval
    - onboarding_example
    - regression_seed
  add_as:
    - eval_seed
    - onboarding_reference
    - negative_case
  do_not_add_as:
    - production_skill
    - real_site_success_case
  target_layers:
    - 2-JS逆向工具层 evals
    - ai-reverse-skill-creator onboarding/reference
  validation:
    - no_real_site_claim
    - no_active_skill_without_governance
    - no_trigger_pollution
```

### 7.5 外部融合合并门槛

```yaml
external_fusion_merge_gate:
  source_inventory_complete: true
  source_type_classified: true
  target_layer_justified: true
  duplicate_capability_checked: true
  eval_or_reference_path_defined: true
  no_active_skill_without_99_governance: true
  no_raw_secret_or_defeat_content: true
  claude_audit: PASS
```

---

## 8. 分支任务清单

首批任务清单：

| 顺序 | task_id | 分支名 | 单轮主题 | 允许修改 | 验证 | 合并条件 |
|---:|---|---|---|---|---|---|
| 1 | `LCL-20260708-01` | `loop/20260708-01-low-loop-rules` | 补强低 LOOP 规则文件 | `低LOOP执行-拉取卸载与再生成方案.md` 或本工程包 | `verify_delivery --domain none` | Claude audit PASS + 单主题 diff |
| 2 | `LCL-20260708-02` | `loop/20260708-02-codex-engineering-pack` | 建立 Codex 可执行工程包 | 本文件 | `verify_delivery --domain none` | Codex task package + audit rubric 完整 |
| 3 | `LCL-20260708-03` | `loop/20260708-03-manifest-design` | manifest 单一来源 | `skills-manifest.json`、`tools/skills_manifest.py`、索引/安装/CI 相关文档 | `tools/skills_manifest.py validate` + score / CI gates | `OBSERVED_MERGED_TO_TEST`，merge commit: `f68998f` |
| 4 | `LCL-20260708-04` | `loop/20260708-04-install-safe-uninstall-consolidation` | INSTALL 安全卸载 + LCL 状态收敛 | `INSTALL.md`、本工程包、LOW-LOOP 执行/验证/验收记录 | manifest validate + release gate + loop/report checks + `verify_delivery --domain none` | 不删除非本仓库 skill + 单一最新执行面 + cleanup ledger |
| 5 | `LCL-20260708-05` | `loop/20260708-05-score-json-output` | score JSON 输出稳定 | 需另行授权 | json.load pass | ci_gate 不污染 stdout |
| 6 | `LCL-20260708-06` | `loop/20260708-06-js-runtime-evidence` | JS manifest/hash/freshness/redaction | 需另行授权 | no raw secret + manifest fields | 不声明真实站点能力 |
| 7 | `LCL-20260708-07` | `loop/20260708-07-external-fusion` | 外部三项能力融合拆解 | 需另行授权 | source inventory + fusion matrix | 不直接 active skill |

> 编号冲突处理：旧设计稿曾把 `LCL-20260708-04` 记为 score JSON 输出稳定化。当前权威口径以本工程包为准：`LCL-20260708-04` 是 INSTALL 安全卸载 + 收敛；score JSON 顺延为 `LCL-20260708-05`，不得混入本轮。

---

## 9. 本工程包自己的验收标准

本文件完成后，Claude 自审：

```yaml
engineering_pack_acceptance:
  codex_task_package_template: required
  branch_state_ledger: required
  validation_matrix: required
  claude_audit_rubric: required
  auto_continue_decider: required
  external_fusion_packages: required
  no_real_site_success_claim: required
  no_raw_secret_example: required
```

验证命令：

```bash
git diff -- 低LOOP-Codex执行工程包.md
python3 tools/web_h5/verify_delivery.py --domain none
```

---

## 10. 使用方式

### 10.1 Claude 规划

Claude 先选择一个 branch task，填充 `codex_task_package`。

### 10.2 Codex 执行

Claude 将任务包发给 Codex。Codex 只在指定分支和指定文件内处理。

### 10.3 Claude 审核

Claude 根据第 5 节评分表审核 Codex diff 和验证输出。

### 10.4 验证与合并

通过验证后，Claude 标记 `MERGE_READY`。合并到 `test` 后重复验证。

### 10.5 自动下一轮

只有第 6 节 `allow_continue_if` 全部满足，才进入下一 loop。

---

## 11. 正式落库拆分方案

本工程包本身不是最终规范源。每个 loop 完成后，必须判断成果应该落到哪里；不能长期只停留在本文件里。

### 11.1 落库状态

```yaml
landing_status:
  DESIGN_ONLY: 只在工程包中设计，尚未进入正式治理源
  STAGED_DOC: 已形成可迁移章节，但未改正式文件
  FORMALIZED: 已拆入正式治理源或 skill/reference/tool contract
  VALIDATED: 正式落库后对应 validator/gate 通过
  SUPERSEDED: 工程包章节已被正式文件替代，只保留迁移索引
```

### 11.2 正式落库目标矩阵

| 内容类型 | 临时位置 | 正式落库目标 | 落库前置条件 | 验证 |
|---|---|---|---|---|
| LOOP profile / 状态机 | 本工程包 | `web-h5-loop-engineering/SKILL.md`、`loop-ledgers.md`、`validate_loop.py` | 状态字段稳定，Claude audit 通过 | LOOP gate |
| 路由与能力等级 | 本工程包 | `99-SKILLS治理/20-routing-contract.md`、`21-scope-capability-levels.md` | 不与现有入口冲突 | routing validator |
| 06 六阶段入口 | 本工程包 | `99-SKILLS治理/06-网页逆向标准规划.md` | 不增加旁路流程 | verify_delivery |
| 安装/卸载 | 本工程包 | `INSTALL.md`、`CHERRY_STUDIO.md`、manifest 工具 | 有 manifest 或安全删除规则 | dry-run / manual target check |
| score 输出 | 本工程包 | `tools/governance/score_skills.py`、`ci_gate.py` | JSON schema 明确 | `json.load` pass |
| JS 脚本采集 | 本工程包 | `tool-contracts/collect_scripts.contract.md`、`env-patch` references | redaction/hash/freshness 字段完整 | no raw secret check |
| Browser/Node parity | 本工程包 | `js-page-runtime-parity`、`compare_browser_vs_node.contract.md` | 不声明业务成功 | parity report schema |
| 外部能力融合 | 本工程包 | 99 准入规则、2 层 references、eval seeds | license/provenance 通过 | fusion gate |

### 11.3 落库任务模板

```yaml
formal_landing_task:
  source_section:
  target_file:
  target_section:
  landing_type: move | summarize | reference | validator_rule | eval_seed | deprecate
  reason:
  prerequisite:
  forbidden:
    - copy_unverified_external_code
    - bypass_existing_governance
    - duplicate_root_level_must_rule
  validation:
    - command_or_manual_check:
      expected:
  rollback:
  status: DESIGN_ONLY | STAGED_DOC | FORMALIZED | VALIDATED | SUPERSEDED
```

### 11.4 落库原则

- 本工程包只做执行设计和 staging，不长期承载 MUST 规则。
- 能进入正式文件的内容必须拆短、去重、绑定 validator 或 eval。
- 不能一次 loop 同时落库多个层级；每个分支只落一个目标。
- 正式落库后，本工程包对应章节标注 `SUPERSEDED` 或只保留索引。

---

## 12. 外部来源许可证与隔离规则

外部能力融合必须先过许可证、来源、干净室隔离三道门。`ai-reverse-toolkit`、`jshook-skill`、`hello_js_reverse_skill` 在未确认来源、许可证和内容前，不得复制代码、不得导入 active skill、不得作为成功经验。

### 12.1 外部来源准入状态

```yaml
external_source_gate:
  source_name:
  source_url_or_path:
  source_exists: true | false
  license_status: unknown | permissive | restrictive | proprietary | incompatible
  provenance_status: unknown | user_provided | repo_observed | public_url_verified
  content_type: idea | prompt | template | code | eval | docs | site_case
  import_allowed: true | false
  allowed_mode: reference_only | clean_room_summary | eval_seed | code_import
  blocked_reason:
```

### 12.2 许可证硬规则

| 状态 | 允许 | 禁止 |
|---|---|---|
| `unknown` | 只写“待确认来源”，可做抽象需求 | 复制正文、复制代码、导入 skill |
| `permissive` | 按许可证保留 attribution 后可引用/改写 | 删除版权、混入不兼容代码 |
| `restrictive` | 只做行为级总结，需人工确认 | 直接复制实现 |
| `proprietary` | 只能作为用户提供的参考需求 | 任何代码/模板导入 |
| `incompatible` | 不融合 | 任何复用 |

### 12.3 Clean-room 融合流程

```yaml
clean_room_fusion:
  observer:
    role: 只阅读外部来源，输出能力摘要和不可复制内容清单
  designer:
    role: 不接触外部原文，仅根据摘要设计本仓库抽象规则
  executor:
    role: 在本仓库分支内实现抽象规则或 eval，不复制原文
  auditor:
    role: 检查是否存在 verbatim copy、license 缺失、来源不明
```

### 12.4 三个外部来源的隔离口径

| 来源 | 当前处理 | 许可证/来源要求 | 允许融合 | 禁止融合 |
|---|---|---|---|---|
| `ai-reverse-toolkit` | 未确认完整实体，只能按历史引用处理 | 需要 source URL/path + license | intake/routing/evidence/scope 抽象模板 | 直接导入模板正文或 active skill |
| `jshook-skill` | 未确认实体，按 runtime hook 能力候选处理 | 需要源码/文档来源 + license | hook tracing 证据字段、contract、eval seed | stealth、WAF defeat、指纹伪造代码 |
| `hello_js_reverse_skill` | 未确认实体，按 demo 候选处理 | 需要 demo 来源 + license | onboarding/eval seed/negative boundary | 生产 skill、真实站点成功声明 |

### 12.5 Codex 许可证约束

Codex 任务包必须增加：

```yaml
license_constraints:
  do_not_fetch_or_copy_external_code_without_user_approval: true
  do_not_paste_external_template_verbatim: true
  require_source_url_and_license_for_import: true
  unknown_license_means_reference_only: true
  report_any_external_snippet: true
```

---

## 13. 真实分支任务清单：工程版

前面的任务表是人类可读 backlog；工程版必须能直接变成 Codex task package 和 branch ledger。

```yaml
branch_task_backlog:
  schema_version: 1.0
  integration_branch: test
  policy:
    one_active_branch_only: true
    require_branch_per_task: true
    require_merge_to_test_before_next: true
    require_claude_audit_before_merge: true
  tasks:
    - task_id: LCL-20260708-01
      title: 补强低 LOOP 规则文件
      branch: loop/20260708-01-low-loop-rules
      topic_type: doc
      status: DONE_OR_CURRENT_BRANCH_DIFF
      allowed_files:
        - 低LOOP执行-拉取卸载与再生成方案.md
      forbidden_files:
        - '*'
      validators:
        - git diff -- 低LOOP执行-拉取卸载与再生成方案.md
        - python3 tools/web_h5/verify_delivery.py --domain none
      merge_gate:
        claude_audit: PASS
        single_file_only: true
        verify_delivery: PASS
      next_on_success: LCL-20260708-02

    - task_id: LCL-20260708-02
      title: 建立 Codex 可执行工程包
      branch: loop/20260708-02-codex-engineering-pack
      topic_type: doc
      status: CURRENT
      allowed_files:
        - 低LOOP-Codex执行工程包.md
      forbidden_files:
        - INSTALL.md
        - tools/**
        - 99-SKILLS治理/**
        - 1-业务流程层/**
        - 2-JS逆向工具层/**
      validators:
        - git diff -- 低LOOP-Codex执行工程包.md
        - python3 tools/web_h5/verify_delivery.py --domain none
      merge_gate:
        claude_audit_score_min: 90
        required_sections:
          - codex_task_package_template
          - branch_execution_ledger
          - validation_matrix
          - claude_audit_rubric
          - auto_continue_decider
          - external_fusion_packages
          - formal_landing_plan
          - license_isolation
          - copyable_codex_prompts
          - final_landing_acceptance_pack
      next_on_success: LCL-20260708-03

    - task_id: LCL-20260708-03
      title: manifest 单一来源设计
      branch: loop/20260708-03-manifest-design
      topic_type: manifest
      status: OBSERVED_MERGED_TO_TEST
      evidence:
        merge_commit: f68998f
        merge_subject: Merge LCL-20260708-03 manifest design
        observed_files:
          - skills-manifest.json
          - tools/skills_manifest.py
          - 00-SKILLS索引.md
          - INSTALL.md
      validators:
        - python3 tools/skills_manifest.py validate
        - python3 tools/governance/score_skills.py --repo . --manifest skills-manifest.json
        - python3 tools/governance/ci_gate.py .ci-out --manifest skills-manifest.json --release
      merge_gate:
        no_hardcoded_old_count: true
        manifest_source_of_truth: skills-manifest.json
      next_on_success: LCL-20260708-04

    - task_id: LCL-20260708-04
      title: INSTALL 安全卸载落地 + 单一最新执行收敛
      branch: loop/20260708-04-install-safe-uninstall-consolidation
      topic_type: install
      status: IN_PROGRESS
      allowed_files:
        - INSTALL.md
        - 低LOOP-Codex执行工程包.md
        - 99-SKILLS治理/05-SKILLS-CHANGELOG.md
        - 99-SKILLS治理/22-LOW-LOOP-EXECUTION-LOG.md
        - 99-SKILLS治理/23-LOW-LOOP-VERIFICATION-REPORT.md
        - tools/reports/LCL-20260708-04-loop-ledger.json
        - tools/reports/LCL-20260708-04-acceptance.md
      validators:
        - python3 tools/skills_manifest.py validate
        - python3 tools/governance/score_skills.py --repo . --manifest skills-manifest.json
        - python3 tools/governance/ci_gate.py .ci-out --manifest skills-manifest.json --release
        - python3 tools/web_h5/web_h5_loop_runner.py validate --ledger <ledger>
        - python3 tools/web_h5/web_h5_acceptance_report.py validate <report>
        - python3 tools/web_h5/verify_delivery.py --domain none
      merge_gate:
        no_delete_non_repo_skill: true
        target_check_documented: true
        single_latest_execution_surface: true
        cleanup_ledger: required
      next_on_success: LCL-20260708-05

    - task_id: LCL-20260708-05
      title: score JSON 输出稳定化
      branch: loop/20260708-05-score-json-output
      topic_type: score
      status: PLANNED_REQUIRES_USER_APPROVAL
      allowed_files: []
      validators:
        - json.load pass
        - ci_gate pass
      merge_gate:
        machine_json_separated_from_human_logs: true
      next_on_success: LCL-20260708-06

    - task_id: LCL-20260708-06
      title: JS runtime evidence manifest
      branch: loop/20260708-06-js-runtime-evidence
      topic_type: js_runtime
      status: PLANNED_REQUIRES_USER_APPROVAL
      allowed_files: []
      validators:
        - no raw secret example
        - manifest fields complete
      merge_gate:
        no_real_site_claim: true
      next_on_success: LCL-20260708-07

    - task_id: LCL-20260708-07
      title: 外部能力融合拆解落库
      branch: loop/20260708-07-external-fusion
      topic_type: external_fusion
      status: PLANNED_REQUIRES_USER_APPROVAL
      allowed_files: []
      validators:
        - source inventory complete
        - license gate complete
        - no active skill direct import
      merge_gate:
        external_fusion_gate: PASS
      next_on_success: STOP_OR_NEW_BACKLOG
```

工程规则：

- `allowed_files: []` 表示还未授权具体落地文件，不能执行。
- `PLANNED_REQUIRES_USER_APPROVAL` 不能自动开分支。
- 每完成一项，必须把 `status`、`merge_gate`、`next_on_success` 更新成 observed 状态。

---

## 14. 模板强校验方案

当前 YAML 仍是文档模板。为避免“只写模板不验证”，每个模板都要绑定最小强校验。

### 14.1 强校验分级

| 等级 | 方式 | 当前是否可执行 | 说明 |
|---|---|---|---|
| `manual_required` | Claude 人工核对字段 | 可执行 | 当前单文件阶段使用 |
| `json_schema_planned` | 后续提取为 JSON Schema | 待落库 | 需要新工具或 schema 文件 |
| `validator_planned` | 后续接入 `tools/validators` | 待落库 | 需要另行授权改 tools |
| `ci_gate_planned` | 后续进入 CI | 待落库 | 需要 workflow 修改 |

### 14.2 当前单文件阶段的强校验清单

```yaml
manual_strong_checks:
  codex_task_package:
    required_keys:
      - task_id
      - base_branch
      - branch
      - objective
      - allowed_files
      - forbidden_files
      - hard_constraints
      - required_outputs
      - validation_commands
      - stop_conditions
  branch_execution_ledger:
    required_keys:
      - task_id
      - state
      - base_branch
      - branch
      - state_history
      - validators
      - merge_record
      - next_loop
  claude_audit:
    required_keys:
      - score
      - result
      - blockers
      - required_fixes
  external_source_gate:
    required_keys:
      - source_name
      - license_status
      - provenance_status
      - import_allowed
      - allowed_mode
      - blocked_reason
```

### 14.3 后续正式工具化建议

正式落库时应新增或扩展 validator：

```yaml
future_validators:
  - validate_low_cost_loop_package.py
  - validate_branch_task_backlog.py
  - validate_external_source_gate.py
  - validate_codex_task_package.py
```

这些工具不在当前单文件授权范围内，只作为后续任务。

---

## 15. Codex 可直接复制的一轮一 prompt

以下 prompt 可直接复制给 Codex。每轮只复制对应一个 prompt，不要混用。

### 15.1 LCL-20260708-02：工程包补强 prompt

```text
你是 Codex Executor。只处理 Low-Cost Structure Loop 的工程包文档。

Base branch: test
Working branch: loop/20260708-02-codex-engineering-pack
Allowed files:
- 低LOOP-Codex执行工程包.md

Forbidden files:
- INSTALL.md
- CHERRY_STUDIO.md
- tools/**
- 99-SKILLS治理/**
- 1-业务流程层/**
- 2-JS逆向工具层/**
- .github/**

Task:
把工程包补齐为 Codex 可直接执行、Claude 可审核、工具可验证的执行层设计。必须包含：
1. 正式落库拆分方案
2. 外部来源许可证与隔离规则
3. 真实分支任务清单工程版
4. YAML 模板强校验方案
5. Codex 可直接复制的一轮一 prompt
6. 最终落地验收包

Hard constraints:
- 不修改 allowed files 以外任何文件。
- 不创建 active skill。
- 不复制外部项目代码或模板原文。
- 不写 raw cookie/token/profile/storage。
- 不声明真实站点能力。

Validation commands:
- git diff -- 低LOOP-Codex执行工程包.md
- python3 tools/web_h5/verify_delivery.py --domain none

Return YAML:
codex_result:
  status:
  files_changed:
  diff_summary:
  commands_run:
  validation_result:
  known_gaps:
  risk_notes:
  rollback_notes:
```

### 15.2 LCL-20260708-03：manifest 设计 prompt

```text
你是 Codex Executor。只设计 skill manifest 单一来源，不落地未授权文件。

Base branch: test
Working branch: loop/20260708-03-manifest-design
Allowed files: <由 Claude 填写，未授权时为空>
Forbidden files: <由 Claude 填写>

Task:
设计 skills-manifest 的 schema、生成规则、校验规则，以及 INSTALL/CHERRY/score/CI 如何引用它。

Do not:
- 不改 INSTALL.md，除非 allowed_files 明确包含。
- 不改 tools，除非 allowed_files 明确包含。
- 不写死 11/15 个 skill 作为长期 source of truth。

Return codex_result YAML。
```

### 15.3 LCL-20260708-07：外部融合拆解 prompt

```text
你是 Codex Executor。只处理外部能力融合拆解设计，不导入外部代码。

Sources:
- ai-reverse-toolkit
- jshook-skill
- hello_js_reverse_skill

Task:
为每个来源建立 source inventory、license gate、allowed use、forbidden use、target layer、validation required。

Hard constraints:
- 未确认 license 的来源只能 reference_only 或 clean_room_summary。
- 不复制外部代码或模板原文。
- 不创建 active skill。
- jshook 类能力不得包含 stealth、WAF defeat、fingerprint falsification。
- hello/demo 类只能作为 eval/onboarding，不作为生产能力。

Return codex_result YAML。
```

---

## 16. 最终落地验收包

每个 loop 合并前必须形成最终落地验收包。

```yaml
final_landing_acceptance_pack:
  task_id:
  branch:
  target_landing:
    status: DESIGN_ONLY | STAGED_DOC | FORMALIZED | VALIDATED | SUPERSEDED
    target_files:
    reason:
  codex:
    result_status:
    diff_summary:
    commands_run:
    known_gaps:
  claude:
    audit_score:
    audit_result:
    blockers:
    required_fixes:
  validation:
    commands:
      - command:
        exit_code:
        key_output:
    required_passed: true | false
  safety:
    raw_secret_check: PASS | FAIL
    license_gate: PASS | FAIL | NOT_APPLICABLE
    capability_claim_check: PASS | FAIL
  merge:
    merge_allowed: true | false
    merged_to_test: true | false
    post_merge_validation: PASS | FAIL | NOT_RUN
  next_loop:
    auto_continue_allowed: true | false
    next_task_id:
    reason:
```

### 16.1 最终验收 PASS 条件

```yaml
final_acceptance_pass_if:
  codex_result_status: CODEX_DONE
  claude_audit_result: PASS
  claude_audit_score_min: 90
  required_validation_passed: true
  raw_secret_check: PASS
  capability_claim_check: PASS
  unresolved_blockers: []
  merge_allowed: true
```

### 16.2 最终验收 FAIL 条件

```yaml
final_acceptance_fail_if:
  - codex_blocked
  - claude_audit_fail
  - validation_failed
  - raw_secret_detected
  - license_gate_failed
  - capability_overclaim
  - modified_forbidden_files
  - no_rollback_plan
```

---

## 17. 外部仓库许可证事实落地包

上一版只有 license gate 概念；这一节把 `ai-reverse-toolkit`、`jshook-skill`、`hello_js_reverse_skill` 的外部融合变成可验收事实包。没有事实包，不允许进入融合任务。

### 17.1 外部仓库事实采集任务

每个外部来源必须先建立独立事实记录：

```yaml
external_repo_fact_pack:
  schema_version: 1.0
  source_name: ai-reverse-toolkit | jshook-skill | hello_js_reverse_skill
  source_kind: repo | local_dir | gist | doc | unknown
  source_locator:
    url:
    local_path:
    provided_by:
  existence:
    status: observed | not_found | unverified
    evidence:
      - command_or_url:
        observed_output:
  license:
    status: observed | missing | unknown | incompatible
    license_file:
    spdx_id:
    attribution_required: true | false | unknown
    commercial_or_redistribution_limits:
  content_inventory:
    has_skill_md: true | false | unknown
    has_code: true | false | unknown
    has_docs: true | false | unknown
    has_evals: true | false | unknown
    has_tools: true | false | unknown
    sensitive_or_disallowed_patterns:
  allowed_fusion_mode: none | reference_only | clean_room_summary | eval_seed | tool_contract | code_import
  prohibited:
    - direct_active_skill_import_when_unverified
    - copy_code_without_license
    - copy_prompt_template_verbatim_when_license_unknown
    - import_stealth_waf_defeat_fingerprint_falsification
  decision: BLOCKED | REFERENCE_ONLY | CLEAN_ROOM_ALLOWED | IMPORT_ALLOWED
  reviewer: Claude
```

### 17.2 三个外部来源的默认状态

在没有 URL/path/license 事实前，默认状态如下：

| source | default decision | allowed now | blocked now |
|---|---|---|---|
| `ai-reverse-toolkit` | `REFERENCE_ONLY` | 抽象 intake/routing/evidence/scope 思路 | 复制模板、导入 skill、声称已融合 |
| `jshook-skill` | `REFERENCE_ONLY` | 抽象 runtime hook tracing 证据字段 | 复制 hook 代码、stealth、WAF defeat、指纹伪造 |
| `hello_js_reverse_skill` | `REFERENCE_ONLY` | 抽象 demo/eval/onboarding 用例 | 作为生产 skill 或成功案例 |

### 17.3 外部融合验收规则

```yaml
external_fusion_acceptance:
  required_before_any_fusion:
    - external_repo_fact_pack exists
    - existence.status in [observed, not_found, unverified]
    - license.status is not incompatible
    - allowed_fusion_mode is not none
  reference_only_pass_if:
    - no external code copied
    - no external template pasted verbatim
    - capability described as derived/abstracted
    - source uncertainty preserved
  import_allowed_only_if:
    - existence.status == observed
    - license.status == observed
    - license permits intended use
    - attribution plan exists
    - security boundary scan pass
    - Claude audit PASS
  fail_if:
    - unknown license but copied code/template
    - WAF defeat / stealth / fingerprint falsification imported
    - active skill created without 99 governance
    - source claimed observed without evidence
```

### 17.4 外部来源验收命令建议

这些命令只是示例，真实执行前需用户授权目标 URL/path：

```yaml
external_source_checks:
  local_dir:
    - test -e <path>
    - find <path> -maxdepth 3 -type f \( -name 'LICENSE*' -o -name 'SKILL.md' -o -name '*.md' \)
  public_repo:
    - git ls-remote <url>
    - fetch LICENSE/README via authorized read-only method
  repo_scan:
    - scan for LICENSE
    - scan for stealth / webdriver hiding / proxy evasion / captcha / waf defeat terms
```

---

## 18. Schema 化计划：从 YAML 模板到强校验

上一版 YAML 仍是模板；本节定义临时 schema 存放、命名和验收。当前只写设计，不新增工具时，至少按这些 schema 手工检查。

### 18.1 临时 schema 目录

所有未正式落库的 schema 放入低 LOOP 临时目录，不直接散落根目录：

```text
.loop/tmp/<loop_id>/schemas/
├── codex-task-package.schema.json
├── branch-execution-ledger.schema.json
├── external-repo-fact-pack.schema.json
├── final-landing-acceptance-pack.schema.json
├── mcp-healthcheck.schema.json
├── crypto-chain-graph.schema.json
└── reset-cleanup-ledger.schema.json
```

### 18.2 schema 最小要求

每个 schema 必须约束：

```yaml
schema_minimum:
  $schema: required
  title: required
  type: object
  required: non_empty_array
  additionalProperties: false_or_documented
  enums_for_status_fields: required
  artifact_paths: string
  commands: array
  evidence_level: observed | derived | assumed | unverified
```

### 18.3 schema 验收规则

```yaml
schema_acceptance:
  pass_if:
    - schema file exists in .loop/tmp/<loop_id>/schemas or formal schema path
    - sample fixture validates
    - required fields reject incomplete sample
    - status enum rejects unknown values
  fail_if:
    - YAML template exists but no schema plan
    - schema allows arbitrary status strings
    - schema lacks evidence_level
    - schema lacks artifact path fields
```

---

## 19. 真实工程版 Backlog 拆分文件

上一版 backlog 仍在工程包里。正式执行时，backlog 必须拆到临时任务目录，避免文档越写越大。

### 19.1 Backlog 临时路径

```text
.loop/tmp/<loop_id>/backlog/
├── branch-task-backlog.yaml
├── LCL-YYYYMMDD-01.yaml
├── LCL-YYYYMMDD-02.yaml
└── completed/
```

### 19.2 Backlog 文件规则

```yaml
backlog_file_rule:
  one_file_per_task: true
  branch_required: true
  allowed_files_required: true
  validators_required: true
  merge_gate_required: true
  next_on_success_required: true
  status_enum:
    - PLANNED_REQUIRES_USER_APPROVAL
    - PLANNED
    - IN_PROGRESS
    - CODEX_DONE
    - CLAUDE_AUDITED
    - VALIDATED
    - MERGED_TO_TEST
    - BLOCKED
    - HUMAN_REVIEW_REQUIRED
```

### 19.3 Backlog 验收

```yaml
backlog_acceptance:
  pass_if:
    - branch-task-backlog.yaml exists
    - every task has a branch
    - only one task is IN_PROGRESS
    - all PLANNED_REQUIRES_USER_APPROVAL tasks have empty or explicit allowed_files
    - completed tasks have validation and merge records
  fail_if:
    - two active branches
    - task lacks validators
    - task can merge without Claude audit
```

---

## 20. 本地 demo 验收路径

为避免结构虚高，低 LOOP 必须有本地 demo 验收路径。demo 不证明真实站点能力，只证明工程链路可执行。

### 20.1 demo 目录

所有 demo 放临时目录：

```text
.loop/tmp/<loop_id>/demo/
├── js-runtime-demo/
│   ├── source/
│   ├── env/
│   ├── scripts-manifest.json
│   ├── runtime-parity-report.json
│   └── README.md
├── manifest-demo/
│   ├── skills-manifest.sample.json
│   └── validation-report.json
└── codex-loop-demo/
    ├── codex-task-package.sample.yaml
    ├── claude-audit.sample.yaml
    └── final-landing-acceptance.sample.yaml
```

### 20.2 demo 验收等级

```yaml
demo_acceptance_levels:
  DEMO_STRUCTURE_PASS:
    proves: 文件结构和 schema 可读
    does_not_prove: 工具真实可用
  DEMO_COMMAND_PASS:
    proves: 本地命令可执行
    does_not_prove: 真实站点能力
  DEMO_PARITY_PASS:
    proves: demo 输入下 Browser/Node 格式对照成立
    does_not_prove: 服务端接受
```

### 20.3 demo 必须包含负例

```yaml
demo_negative_cases:
  - missing_required_field_should_fail
  - unknown_status_enum_should_fail
  - raw_secret_placeholder_should_fail
  - capability_overclaim_should_fail
  - external_unknown_license_import_should_fail
```

---

## 21. MCP Healthcheck 强任务

MCP / 动态执行基座是 Web/H5 逆向短板之一，必须从普通验证矩阵中单独拆出来。

### 21.1 MCP healthcheck 任务包

```yaml
mcp_healthcheck_task:
  task_id: LCL-MCP-HEALTHCHECK
  branch: loop/<date>-mcp-healthcheck
  topic_type: mcp_healthcheck
  checks:
    - mcp_server_available
    - browser_or_js_reverse_tool_available
    - can_open_test_page_or_local_fixture
    - can_capture_network_or_script_inventory
    - can_evaluate_runtime_expression
    - can_collect_call_stack_or_error
    - can_export_redacted_artifact
  outputs:
    - mcp-healthcheck-report.json
    - redaction-report.json
  must_not:
    - use_real_credentials
    - bypass_access_control
    - persist_cookie_token_profile
```

### 21.2 healthcheck 验收

```yaml
mcp_healthcheck_acceptance:
  pass_if:
    - report exists
    - every check has status pass | fail | skipped_with_reason
    - skipped checks explain missing tool or authorization
    - no raw secret persisted
  fail_if:
    - MCP availability assumed without report
    - dynamic execution claim made without runtime evidence
    - healthcheck uses real target without authorization
```

### 21.3 与 LOOP 的关系

- MCP healthcheck PASS 只证明动态执行基座可用。
- MCP healthcheck FAIL 不阻断纯文档任务，但阻断 JS runtime、Hook、Browser parity、真实网页侦察任务。
- MCP healthcheck 不等于真实业务 API 成功。

---

## 22. 复杂加密链证据治理

简单 sign/token 不够。必须覆盖链式加密：`a` 结构 + 时间戳加密，`b` 使用 `a` 的加密结果，`c` 完整使用 `b` 的加密数据。

### 22.1 加密链图谱

```yaml
crypto_chain_graph:
  schema_version: 1.0
  chain_id:
  inputs:
    - name:
      source: request_body | query | header | timestamp | nonce | storage | server_seed
      fact_level:
  nodes:
    - id: a
      type: transform | encrypt | sign | encode | hash | timestamp_bind
      inputs:
      outputs:
      algorithm_observed:
      script_ref:
      function_ref:
      sample_in:
      sample_out:
      fact_level:
    - id: b
      type:
      depends_on: [a]
      input_from_previous:
      outputs:
      fact_level:
    - id: c
      type:
      depends_on: [b]
      input_from_previous:
      outputs:
      fact_level:
  edges:
    - from: a.output
      to: b.input
      evidence:
    - from: b.output
      to: c.input
      evidence:
  final_request_binding:
    endpoint:
    fields:
    headers:
    body_paths:
  validation:
    browser_sample:
    node_sample:
    replay_result:
    mismatch_reason:
```

### 22.2 链式加密验收规则

```yaml
crypto_chain_acceptance:
  pass_if:
    - every node has input/output sample or explicit unverified marker
    - every edge has evidence
    - timestamp/nonce source is labeled
    - intermediate value reuse is documented
    - final request field binding is documented
    - Browser vs Node parity covers final and intermediate outputs when possible
  fail_if:
    - only final sign is recorded but intermediate dependencies missing
    - timestamp treated as constant
    - b/c dependency on a/b is assumed without sample
    - replay success claimed without backend evidence
```

### 22.3 复杂加密链任务类型

```yaml
complex_crypto_task_types:
  chain_discovery:
    output: crypto_chain_graph
  node_parity:
    output: node-level browser/node samples
  edge_validation:
    output: dependency evidence
  final_replay:
    output: backend acceptance or rejected reason
  regression_fixture:
    output: stable sample set with freshness
```

---

## 23. Reset / 临时目录 / Cleanup 强任务

多轮 LOOP 最大风险是状态污染和清理不干净。所有工具设计、demo、schema、backlog、Codex 输出、临时报告必须放入 `.loop/tmp/<loop_id>/`，并有 reset/cleanup 验收。

### 23.1 临时目录结构

```text
.loop/tmp/<loop_id>/
├── README.md
├── state/
│   ├── branch-state.yaml
│   └── loop-state.yaml
├── backlog/
├── codex/
│   ├── prompts/
│   └── results/
├── schemas/
├── demo/
├── evidence/
├── reports/
├── validation/
├── cleanup/
│   ├── cleanup-plan.yaml
│   ├── cleanup-report.yaml
│   └── kept-evidence.yaml
└── archive/
```

### 23.2 reset 任务

```yaml
reset_task:
  task_id: LCL-RESET
  when:
    - before_new_loop
    - after_merge_to_test
    - after_validation_failed
    - before_mcp_or_js_runtime_task
  actions:
    - verify_current_branch
    - record_git_status
    - clear_or_archive_tmp_outputs
    - reset_demo_state
    - remove_stale_generated_reports
    - preserve_unique_evidence
  forbidden:
    - delete_unique_evidence_without_migration
    - reset_git_worktree_without_user_approval
    - remove_site_memory
```

### 23.3 cleanup 验收

```yaml
cleanup_acceptance:
  pass_if:
    - cleanup-plan.yaml exists
    - cleanup-report.yaml exists
    - kept-evidence.yaml lists preserved artifacts
    - no raw secrets in tmp reports
    - stale generated files archived or removed
    - unique evidence preserved or migrated
  fail_if:
    - tmp files scattered outside .loop/tmp/<loop_id>
    - cleanup deletes only evidence
    - raw secret remains in reports
    - generated demo files remain without index
```

### 23.4 临时目录生命周期

```yaml
tmp_lifecycle:
  create: BRANCH_CREATED
  update: every_state_transition
  freeze: MERGE_READY
  archive_or_cleanup: MERGED_TO_TEST | STOPPED
  retention:
    keep:
      - final_landing_acceptance_pack
      - validation summaries
      - redacted evidence
    remove:
      - raw generated scratch
      - stale demo output
      - failed transient reports without evidence value
```

---

## 24. 本次 LOOP 规则与不足边界

本工程包补的是**本次 low-cost structure loop 的执行规则、审查规则、分支规则、Codex 任务规则和不足处理规则**，不是在本文件里直接改造整个项目。

### 24.1 当前边界

```yaml
current_scope:
  purpose: design_current_loop_execution_rules_and_gaps
  not_purpose: directly_modify_all_project_governance_files
  allowed_now:
    - document current loop execution rules
    - define Codex task package
    - define Claude audit and validation rules
    - define temporary folder layout
    - define future landing map
  not_allowed_now:
    - modify INSTALL.md without a dedicated loop task
    - modify SKILL.md without a dedicated loop task
    - modify tools without a dedicated loop task
    - create active skill from external sources
    - scatter generated artifacts outside fixed loop folder
```

### 24.2 固定文件夹规则

所有本次 loop 产生的中间文件、schema、demo、backlog、Codex prompt/result、validation report、cleanup report 必须放在固定目录：

```text
.loop/tmp/<loop_id>/
```

禁止乱堆到根目录。只有两类文件可以离开 `.loop/tmp/<loop_id>/`：

1. 用户明确要求修改的目标文件。
2. 某一轮正式落库任务明确允许修改的项目文件。

### 24.3 真实项目文件修改规则

```yaml
project_file_change_rule:
  default: do_not_modify_project_files
  allowed_only_when:
    - branch_task_explicitly_names_target_file
    - allowed_files_contains_target
    - merge_gate_defined
    - validation_defined
    - rollback_defined
  examples:
    install_change:
      requires_task: LCL-*-install-safe-uninstall
      allowed_files_must_include: INSTALL.md
    skill_change:
      requires_task: dedicated_skill_task
      allowed_files_must_include: specific_SKILL.md
    tool_change:
      requires_task: dedicated_tool_task
      allowed_files_must_include: specific_tools_path
```

---

## 25. 文件关系与职责边界

后续只保留清晰职责，避免两个文件继续膨胀和互相重复。

| 文件 | 职责 | 是否执行源 | 后续处理 |
|---|---|---|---|
| `低LOOP执行-拉取卸载与再生成方案.md` | 设计方案、早期规则草案、用户可读背景 | 否 | 可保留为历史设计稿或迁移索引 |
| `低LOOP-Codex执行工程包.md` | Codex 可执行包、Claude 审核包、分支状态工程包 | 是 | 当前 low-cost loop 的主执行包 |
| `.loop/tmp/<loop_id>/` | schema/demo/backlog/prompt/result/report 临时工程目录 | 是，临时 | 每轮结束后 cleanup/archive |
| 正式治理文件 | 99/SKILL/tool/contract 等项目长期规范源 | 只有专门落库任务才改 | 按任务逐项迁移 |

规则：

- `低LOOP-Codex执行工程包.md` 是当前执行入口。
- `低LOOP执行-拉取卸载与再生成方案.md` 不再继续扩写为第二套执行规范。
- 当某个章节成熟并正式落库后，本工程包只保留索引和验收记录。

---

## 26. 最小第一轮完整样例

本样例只用于说明当前 loop 如何执行，不代表已经建分支、合并或提交。

```yaml
codex_task_package:
  schema_version: 1.0
  task_id: LCL-20260708-02
  title: 建立 Codex 可执行工程包
  base_branch: test
  branch: loop/20260708-02-codex-engineering-pack
  topic_type: doc
  objective: 补齐 Codex 可执行、Claude 可审核、工具可验证的 low-cost loop 工程包。
  allowed_files:
    - 低LOOP-Codex执行工程包.md
  forbidden_files:
    - INSTALL.md
    - CHERRY_STUDIO.md
    - tools/**
    - 99-SKILLS治理/**
    - 1-业务流程层/**
    - 2-JS逆向工具层/**
    - .github/**
  hard_constraints:
    - only_edit_allowed_file
    - do_not_create_active_skill
    - do_not_copy_external_code_or_template_verbatim
    - do_not_persist_raw_cookie_token_profile_storage
    - do_not_claim_real_site_success
    - put_temporary_artifacts_under_.loop/tmp/<loop_id>/
  validation_commands:
    - command: git diff -- 低LOOP-Codex执行工程包.md
      expected: only_allowed_file_changed
      required_for_merge: true
    - command: python3 tools/web_h5/verify_delivery.py --domain none
      expected: exit_code_0
      required_for_merge: true
  success_criteria:
    - codex_task_package_template_complete
    - branch_execution_ledger_defined
    - validation_matrix_defined
    - claude_audit_rubric_defined
    - formal_landing_plan_defined
    - license_isolation_defined
    - final_acceptance_pack_defined
  stop_conditions:
    - forbidden_file_modified
    - validation_failed
    - scope_expansion_needed
    - raw_secret_risk
    - human_review_required
```

对应 Claude audit 示例：

```yaml
claude_audit:
  task_id: LCL-20260708-02
  result: PASS
  score: 92
  scope_control: PASS
  branch_discipline: PASS_OR_NOT_APPLICABLE_FOR_DOC_ONLY_CURRENT_SESSION
  validation_truth: PASS
  safety_boundary: PASS
  capability_claim: PASS
  rollback: PASS
  blockers: []
  next_loop_allowed: true_if_merged_to_test_and_post_merge_validation_passes
```

---

## 27. 文件膨胀与拆分策略

工程包不能无限增长。超过阈值后必须拆分到 `.loop/tmp/<loop_id>/` 或正式落库目标。

```yaml
document_growth_policy:
  soft_limit_lines: 1200
  hard_limit_lines: 1800
  if_soft_limit_exceeded:
    - move examples to .loop/tmp/<loop_id>/demo
    - move schemas to .loop/tmp/<loop_id>/schemas
    - move per-task backlog to .loop/tmp/<loop_id>/backlog
    - keep only index and rules in this file
  if_hard_limit_exceeded:
    - stop adding new sections
    - create split task
    - mark large sections as STAGED_DOC or SUPERSEDED
```

允许保留在本文件：

- 总控规则。
- 状态机。
- Codex/Claude 职责。
- 验收规则。
- 正式落库映射。

应该拆出去：

- 大量样例。
- 每轮具体 backlog。
- JSON schema 文件。
- demo 输出。
- Codex 原始 prompt/result。
- validation 报告。

---

## 28. 冲突解决与回滚策略

### 28.1 merge conflict 策略

```yaml
merge_conflict_policy:
  when_conflict_detected:
    state: MERGE_CONFLICT
    auto_continue_allowed: false
  codex_may_propose_resolution: true
  claude_must_review_resolution: true
  conflict_types:
    doc_only:
      action: Claude review and resolve if within allowed file
    generated_tmp_only:
      action: prefer_regenerate
    governance_or_skill_file:
      action: human_review_or_dedicated_loop
    unknown:
      action: stop
  validation_after_resolution:
    - rerun task validators
    - rerun verify_delivery when applicable
```

### 28.2 回滚策略

```yaml
rollback_policy:
  before_merge:
    action: abandon_or_reset_loop_branch
    requires_human_review: false_if_no_unique_evidence
  after_merge_to_test:
    action: revert_merge_commit_or_revert_specific_commit
    requires_validation_after_revert: true
  after_push_origin_test:
    action: no_force_action_without_human_review
    requires_human_review: true
  evidence_rule:
    - never_delete_unique_evidence_without_migration
    - preserve_final_acceptance_pack
    - archive_redacted_validation_summary
```

### 28.3 回滚记录

```yaml
rollback_record:
  task_id:
  branch:
  rollback_type: abandon_branch | revert_commit | regenerate_tmp | human_review
  reason:
  evidence_preserved:
  commands:
  validation_after_rollback:
  final_state:
```

---

## 29. Codex 失败再分配规则

Codex 失败不是自动重试的理由。必须先分类。

```yaml
codex_failure_policy:
  CODEX_BLOCKED:
    first_time: Claude narrows scope or fixes task package
    second_same_blocker: STOPPED or HUMAN_REVIEW_REQUIRED
  CODEX_OVER_SCOPE:
    action: reject diff and restart from clean branch
  CODEX_PARTIAL_SUCCESS:
    action: accept reviewed subset only if separable, create new task for remaining work
  CODEX_VALIDATION_FAILED:
    action: Claude reviews failure, either return to Codex with narrower prompt or stop
  CODEX_UNSAFE_OUTPUT:
    action: reject, record safety finding, do not reuse output
```

### 29.1 是否复用 Codex session

```yaml
codex_session_policy:
  resume_allowed_if:
    - same_task_id
    - same_branch
    - same_allowed_files
    - failure_is_minor_or_validation_fix
  fresh_required_if:
    - scope_changed
    - branch_recreated
    - codex_over_scope
    - unsafe_output
    - second_same_blocker
```

---

## 30. 外部仓库事实采集命令包

本节只定义事实采集，不授权导入外部代码。没有用户提供的 URL/path 时，不猜测具体仓库。

### 30.1 未提供 URL/path

```yaml
unknown_source_only:
  action: mark_unverified
  allowed:
    - record source_name
    - record requested capability
    - define required evidence
  forbidden:
    - guess_github_url
    - claim_observed
    - copy_code
    - create_active_skill
```

### 30.2 本地目录事实采集

```yaml
local_source_fact_commands:
  precondition: user_provided_local_path
  commands:
    - command: test -e <path>
      evidence: path_exists_or_not
    - command: find <path> -maxdepth 3 -type f \( -name 'LICENSE*' -o -name 'README*' -o -name 'SKILL.md' -o -name '*.md' \)
      evidence: inventory
  required_outputs:
    - existence.status
    - license.status
    - content_inventory
```

### 30.3 公共仓库事实采集

```yaml
public_repo_fact_commands:
  precondition: user_provided_repo_url_or_explicit_search_authorization
  commands:
    - command: git ls-remote <url>
      evidence: repo_exists_or_not
    - command: fetch README/LICENSE via read-only method
      evidence: license_and_scope
  forbidden:
    - cloning_and_importing_without_license_review
    - assuming_same_name_repo_is_user_intended_source
```

### 30.4 三个来源的事实采集要求

| source | 如果没有 URL/path | 如果有 URL/path | 可进入下一步条件 |
|---|---|---|---|
| `ai-reverse-toolkit` | `unverified`, reference-only | 采集 README/LICENSE/模板目录 | license 非 incompatible，且不复制原文 |
| `jshook-skill` | `unverified`, reference-only | 采集 README/LICENSE/SKILL/tool 文件 | 无 stealth/WAF defeat/指纹伪造导入 |
| `hello_js_reverse_skill` | `unverified`, demo-only | 采集 README/LICENSE/demo/eval | 只作为 eval/onboarding |

---

## 31. Final acceptance pack 完整样例

```yaml
final_landing_acceptance_pack:
  task_id: LCL-20260708-02
  branch: loop/20260708-02-codex-engineering-pack
  target_landing:
    status: DESIGN_ONLY
    target_files:
      - 低LOOP-Codex执行工程包.md
    reason: 当前任务只补本次 loop 的执行规则和不足，不正式改项目治理源
  codex:
    result_status: CODEX_DONE
    diff_summary:
      - added formal landing plan
      - added license isolation
      - added branch backlog engineering version
      - added schema plan and acceptance pack
    commands_run:
      - git diff -- 低LOOP-Codex执行工程包.md
      - python3 tools/web_h5/verify_delivery.py --domain none
    known_gaps:
      - schemas are planned, not implemented as files
      - validators are planned, not implemented in tools
  claude:
    audit_score: 92
    audit_result: PASS
    blockers: []
    required_fixes: []
  validation:
    commands:
      - command: git diff -- 低LOOP-Codex执行工程包.md
        exit_code: 0
        key_output: only target doc changed
      - command: python3 tools/web_h5/verify_delivery.py --domain none
        exit_code: 0
        key_output: blockers empty
    required_passed: true
  safety:
    raw_secret_check: PASS
    license_gate: NOT_APPLICABLE_FOR_DESIGN_ONLY
    capability_claim_check: PASS
  merge:
    merge_allowed: true_if_branch_gate_passes
    merged_to_test: false
    post_merge_validation: NOT_RUN
  next_loop:
    auto_continue_allowed: false_until_merged_to_test
    next_task_id: LCL-20260708-03
    reason: next task requires dedicated branch and explicit allowed_files
```

---

## 32. 文档到工具化路线图

```yaml
toolization_roadmap:
  phase_1_manual_strong_check:
    input: markdown engineering pack
    output: Claude audit + final acceptance pack
    completion: manual required fields checked
  phase_2_schema_files:
    input: YAML templates
    output: JSON Schema files under .loop/tmp/<loop_id>/schemas or formal schema path
    completion: sample pass/fail fixtures validate
  phase_3_python_validators:
    input: schema + sample ledgers
    output: validate_low_cost_loop_package.py family
    completion: validators reject incomplete/invalid examples
  phase_4_ci_gate:
    input: validators
    output: PR/schedule checks
    completion: CI fails on missing branch task, unknown license import, raw secret example
  phase_5_loop_runner_integration:
    input: stable validators and ledgers
    output: low_cost_structure profile in runner
    completion: runner can init/record/validate low-cost loop ledger
```

当前文件只完成 Phase 1 的设计与手工强校验；Phase 2-5 需要后续专门分支任务。

---

## 33. 工程包章节到正式治理源映射

| 工程包章节 | 未来正式落库目标 | 说明 |
|---|---|---|
| 1-6 Codex/Claude/分支/验证 | `web-h5-loop-engineering` references / runner profile | 形成正式 low_cost_structure profile |
| 7 外部融合执行包 | `99-SKILLS治理/04`、相关 2 层 references/evals | 外部能力准入和 eval seed |
| 11 正式落库拆分 | `99-SKILLS治理/20/21` 或索引 | 防止旁路规范 |
| 12 license 隔离 | 99 准入规约 / future external source gate validator | 未知许可证禁止导入 |
| 13 backlog 工程版 | `.loop/tmp/<loop_id>/backlog` / future validator | 不长期塞主文档 |
| 14 schema 强校验 | `.loop/tmp/<loop_id>/schemas` / tools validators | 从模板走向校验 |
| 20 demo 验收 | `.loop/tmp/<loop_id>/demo` | 防止结构虚高 |
| 21 MCP healthcheck | MCP/tooling healthcheck validator | 动态执行基座验证 |
| 22 复杂加密链 | encryption-algorithm-graph / js parity contract | 覆盖 a->b->c 依赖链 |
| 23 reset/cleanup | `99-SKILLS治理/17` / cleanup policy | 多轮干净性 |
| 28 conflict/rollback | loop ledger / branch ledger | 失败可恢复 |
| 29 Codex failure | Codex task package policy | 失败不盲重试 |
| 30 external fact commands | external source fact pack | 事实先于融合 |
| 31 final acceptance sample | final landing acceptance pack | 每轮合并前验收 |
| 32 toolization roadmap | future tool tasks | 工具化路线 |

---

## 34. 最终口径

- 本工程包是“让 Codex 可执行、让 Claude 可审核、让工具可验证”的执行层设计。
- 它不替代正式治理源。
- 它不证明真实站点能力。
- 它约束每一轮必须：新分支、Codex 执行、Claude 审核、工具验证、合并回 `test`、再决定下一轮。
