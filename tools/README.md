# tools/ — 仓库辅助脚本

## sync_site_memory.py

把项目 memory 中的 `type: project` / `type: feedback` 条目同步到 `站点经验库/<domain>/` 的 7 个标准文件。

### 用法

```bash
# dry-run（默认，只预览）
python tools/sync_site_memory.py \
    --project E:/flight-cwl/flight-cwl-vj-baggage \
    --domain vietjetair.com

# 真正写入
python tools/sync_site_memory.py \
    --project E:/flight-cwl/flight-cwl-vj-baggage \
    --domain vietjetair.com \
    --apply

# 同时同步 feedback 类（默认只同步 project 类）
python tools/sync_site_memory.py \
    --project E:/flight-cwl/flight-cwl-vj-baggage \
    --domain vietjetair.com \
    --apply --include-feedback
```

### 行为

1. 扫 `<project>/memory/*.md` 和 `~/.claude/projects/<sanitized>/memory/*.md` 两处
2. 跳过 `MEMORY.md` 索引文件
3. 根据 frontmatter 的 `type` 过滤
4. 根据内容关键词归类到 `known-failures.md` / `route-decisions.md` / `market-matrix.md` 等
5. 站点目录不存在时从 `站点经验库/_templates/` 复制 7 文件模板
6. 追加写入（不覆盖），每条加 `<!-- synced from: ... -->` 注释方便溯源

### 何时跑

任务结束、做总结时手动跑一次。**不建议接 Stop hook 自动跑**（会污染无关项目）。

---

## backfill_from_site_memory.py

从 `站点经验库/<domain>/` 和 `逆向工程经验库/domains/<domain>/reverse-memory.md` 反推真实任务下限，写进指定 Skill 的 `metrics/real-task-summary.md`。

任务下限 = `## Failure:` 计数 + `## Pattern:` / `## Lesson:` 计数 + change-log 表格版本行数 + reverse-memory 的 Run Ledger 行数。

### 用法

```bash
# dry-run (默认)
python tools/backfill_from_site_memory.py \
    --domain thaiairways.com \
    --skill-metrics "1-业务流程层/website-314-api-delivery/metrics/real-task-summary.md"

# 真正写入
python tools/backfill_from_site_memory.py \
    --domain thaiairways.com \
    --skill-metrics "1-业务流程层/website-314-api-delivery/metrics/real-task-summary.md" \
    --apply

# 多 domain 累加
python tools/backfill_from_site_memory.py \
    --domain thaiairways.com --domain vietjetair.com \
    --skill-metrics "..." --apply

# 覆盖已写入的反推段
python tools/backfill_from_site_memory.py ... --apply --rewrite
```

### 行为

1. 用区段标记 `<!-- backfill-from-site-memory:start -->` / `:end` 包裹反推段
2. 默认追加；已存在反推段时跳过，加 `--rewrite` 才覆盖
3. 写入的数字会被 `score_skills.py` 检测为真实数据，撤销 v0.3.4 metrics 占位虚高

### 何时跑

每次新建 / 更新 `站点经验库/<domain>/` 或 `逆向工程经验库/domains/<domain>/reverse-memory.md` 后跑一次，让该 domain 真实参与的 Skill metrics 反映真实任务下限。

---

## scaffold_evals.py

给指定 Skill 生成 `evals/*.yaml` + `agents/openai.yaml` 骨架。骨架用 `TODO:` 占位 prompt 和 criteria，需要后续手动或交 agent 填真实内容。

### 用法

```bash
# 单个 Skill
python tools/scaffold_evals.py --skill 2-JS逆向工具层/find-crypto-entry

# 批量
python tools/scaffold_evals.py \
    --skill 2-JS逆向工具层/find-crypto-entry \
    --skill 2-JS逆向工具层/ast-deobfuscate \
    --skill 2-JS逆向工具层/env-patch

# 覆盖已有骨架
python tools/scaffold_evals.py --skill ... --force
```

### 行为

1. 读 SKILL.md frontmatter 提取 `name` 和 `description`
2. 写 `agents/openai.yaml`（不存在时）
3. 写 `evals/001-positive-placeholder.yaml`（expect_skill: true）
4. 写 `evals/002-negative-placeholder.yaml`（expect_skill: false）
5. 写 `evals/003-regression-placeholder.yaml`（expect_skill: true）
6. 默认不覆盖已存在的文件

### 何时跑

新增工具层 Skill 时跑一次生成骨架，然后用 agent 填真实 case 内容，避免长期保留 TODO 占位。

---

## post_task_reminder.py / append_drift_history.py

Stop hook 与 CI 周更 drift snapshot 的脚本。详见 `99-SKILLS治理/05-当前评分与回测结果.md` 的 v0.3.4 章节。

---

## replayer/validate_fixtures.py

验证 `站点经验库/<domain>/fixtures/snapshots/` 下的 req/resp/meta 三件套。

### 用法

```bash
# 结构/schema 检查: 允许新转换出来的 meta.yaml 保留待 review 占位,但会给 warning
python tools/replayer/validate_fixtures.py 站点经验库

# 交付/发版检查: TODO、自动抽取占位、待 review 文案都会失败
python tools/replayer/validate_fixtures.py 站点经验库 --strict-review
```

### 何时跑

HAR / CloakBrowser 录制刚转 fixtures 后先跑普通检查,确认三件套齐全。
人工确认 `endpoint` / `category` / `sensitive` / `requires_auth` / `tolerance` 后跑
`--strict-review`,只有严格检查通过的 meta 才能作为语义证据。

---

## validate_web_h5_crawler_gate.py

验证 Web/H5 爬虫 Skill 是否仍包含强制硬化结构：fresh packet evidence、清空 cookies/storage/cache 的多轮复测、反偶发成功、并发阶梯和 session/cache 隔离。

### 用法

```bash
python tools/validate_web_h5_crawler_gate.py
```

### 何时跑

修改 `reverse-js-crawler`、Web/H5 爬虫治理规约、评分 eval、并发/复测/抓包要求后必跑。它只验证能力层结构，不证明某个真实站点当天可用。

---

## validate_web_h5_loop_gate.py

验证 Web/H5 Loop Engineering 是否仍包含至少三角色闭环结构：Executor、Verifier、Governor、最大迭代次数、停止条件、人工复核、fresh evidence、clean-state retest、anti-flake、并发阶梯和 session/cache 隔离。

### 用法

```bash
python tools/validate_web_h5_loop_gate.py
```

### 何时跑

修改 `web-h5-loop-engineering`、Loop Engineering eval、三角色 agent 编排、停止条件、ledger 模板或 CI gate 后必跑。它只验证闭环结构，不实际启动多个 agent，也不证明真实站点当天可用。

---

## web_h5_loop_runner.py

创建、追加和验证 Web/H5 Loop Runner execution ledger。它管理证据账本,不打开网页,不绕过保护。

### 用法

```bash
python tools/web_h5_loop_runner.py init \
    --out loop-ledger.json \
    --domain example.com \
    --stage search \
    --target-api POST:/api/search

python tools/web_h5_loop_runner.py record-iteration \
    --ledger loop-ledger.json \
    --executor-action "capture search API" \
    --verifier-result blocked \
    --governor-result human_review

python tools/web_h5_loop_runner.py validate --ledger loop-ledger.json
python tools/web_h5_loop_runner.py validate --ledger loop-ledger.json --require-complete
```

### 何时跑

真实 Loop Engineering 任务开始时先 `init`;每轮执行后 `record-iteration`;声明完成前 `validate --require-complete`。

`validate` 默认只验证结构,成功状态是 `STRUCTURE_PASS`。`--require-complete` 只有在 fresh evidence、三组 clean-state retest、后端接受、数据验收、fixture freshness 和 stable decision 都齐全时才返回 `SUCCESS_PASS`。证据不齐返回 `BLOCKED`,不能声明完成。

---

## web_h5_acceptance_report.py

生成和验证 Web/H5 crawler acceptance report,覆盖 clean-state retest、anti-flake、1/2/5/10 worker 并发阶梯、risk-control concurrency、UI/API parity、fixture freshness 和 metrics。

### 用法

```bash
python tools/web_h5_acceptance_report.py template \
    --out acceptance-report.json \
    --domain example.com \
    --stage search \
    --target-api POST:/api/search

python tools/web_h5_acceptance_report.py validate --report acceptance-report.json
python tools/web_h5_acceptance_report.py validate --report acceptance-report.json --require-complete
```

### 何时跑

涉及实战执行、并发、风控证据、网页一致性或稳定性声明时必跑。默认 `validate` 只返回 `STRUCTURE_PASS`。没有通过 `--require-complete` 并拿到 `SUCCESS_PASS`,不能声明并发、稳定或真实完成。`BLOCKED` 是有效阻塞结论,不是成功。

---

## fixture_freshness_report.py

输出 fixtures 的新鲜度和 review 状态,包括 expired_count、review_pending_count、recent_report 和 source_freshness。

### 用法

```bash
python tools/fixture_freshness_report.py 站点经验库
python tools/fixture_freshness_report.py 站点经验库 --strict-fresh
python tools/ci_gate.py .ci-out --release
```

### 何时跑

每次声称网页一致性、fresh replay 或真实交付前跑。默认是 report-only;发版/交付前使用 `--strict-fresh` 或 `python tools/ci_gate.py .ci-out --release`。普通 `ci_gate.py .ci-out` 只是结构/评分门禁,不能作为 release freshness 证据。

---

## validate_web_h5_real_execution_gate.py

验证真实实战执行标准化资产是否存在: Loop Runner、acceptance report、fixture freshness report、metrics、references 和 evals。

### 用法

```bash
python tools/validate_web_h5_real_execution_gate.py
```

### 何时跑

修改 runner、acceptance、freshness、metrics、真实执行 references/evals 或 `ci_gate.py` 后必跑。它只验证结构,不证明某个真实站点当天可用。
