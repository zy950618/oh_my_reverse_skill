# my_reverse_skill — Claude 工作指南

Web/H5 逆向工程 SKILLS 总库。进入本仓库工作时,请先按下面规则行动,**不要直接跳进 reverse-js-crawler 写代码，所有逆向需要依据，最后实现纯算和能高并发的调用处理**。

---

## 首要入口(强制)

收到"网页逆向 XXX 网站"、"实现 XXX 站点纯接口"、"把 XXX 接入 314"、"破解 XXX 的 sign/token"、"做一下 XXX 的爬虫"类请求时:

**第一步:读 `99-SKILLS治理/06-网页逆向标准规划.md`,按六阶段输出规划再开干。**

规划格式固定:

```
目标:<URL + 业务目标>
分类:<纯HTTP / JS加密 / 补环境 / WAF / 接口化沉淀 / 314服务化>
难度评估:<低/中/高> + 关键不确定点 3 个
阶段化计划:
  1. 侦察    skill: <name>    产出: <什么>
  2. 入口    skill: <name>    产出: <什么>
  3. 还原    skill: <name>    产出: <什么>
  4. 复现    skill: <name>    产出: <什么>
  5. 沉淀    skill: <name>    产出: <什么>
  6. 一致性  skill: <name>    产出: <什么>
  7. 收尾    skill: governance    产出: cleanup ledger + encryption algorithm graph
逆向经验库检查:<是否已有 逆向工程经验库/domains/<domain>/reverse-memory.md,已有则先读完>
站点经验库检查:<是否已有 站点经验库/<domain>/,已有则先读完 known-failures.md>
WAF 预判:<是否存在 reese84/incapsula/akamai/cloudflare 痕迹>
风险与红线:<是否涉及真实扣款 / 是否涉及登录态 / 是否需要授权>
证据口径:<哪些结论必须给 URL/HAR/调用栈/JSON Pointer/命令输出>
范围账本:<domain/market/locale/currency/stage/auth_state/target_api>
并发会话边界:<是否涉及批量/并发/指纹/session/cache,若涉及如何隔离>
```

输出后等用户确认或修正,再进入执行。

---

## 仓库分层速查

| 层 | 目录 | 角色 |
|---|---|---|
| 1 | `1-业务流程层/` | 顶层入口(4 个 skill),按需求调度 2/5 层 |
| 2 | `2-JS逆向工具层/` | Web/JS 原子工具(4 个) |
| 4 | `4-通用规范层/` | 行为守则(karpathy-guidelines) |
| 5 | `5-沉淀工具层/` | 接口稳定后的标准化(site-api-adapter) |
| 6 | `6-验证码逆向层/` | 验证码/验证服务逆向(captcha-service-delivery) |
| 99 | `99-SKILLS治理/` | 生命周期/分类/评分/漂移/准入 |
| - | `站点经验库/` | 站点案例(按 domain/market/locale 拆分) |
| - | `逆向工程经验库/` | run/capture/replay、旧新证据、工具失败和复测经验 |
| - | `验证码经验库/` | 验证码 provider 与站点绑定经验 |
| - | `tools/` | 仓库辅助脚本(`sync_site_memory.py`、`ci_gate.py`、`post_task_reminder.py`) |

完整入口见 `00-SKILLS索引.md`,标准入口与目录详解见 `README.md`。

---

## 站点经验库使用约定(强制)

任何 domain 相关任务,**先查 `逆向工程经验库/domains/<domain>/reverse-memory.md`**,再查 `站点经验库/<domain>/known-failures.md`:

- 已有 run/capture/replay 经验 → 不要重新开荒
- 已知失败模式 → 不要重复踩
- 已知路由决策 → 不要重新调研
- 已知 market/locale 矩阵 → 不要重新枚举

新 domain 没有 reverse memory 时,从 `逆向工程经验库/_templates/reverse-memory.md` 建立 `逆向工程经验库/domains/<domain>/reverse-memory.md`。
新 domain 没有目录时,从 `站点经验库/_templates/` 复制 7 文件模板再开始。

---

## AI 自理能力(强制)

逆向任务中所有重要结论必须按 `99-SKILLS治理/11-AI事实证据规约.md` 标注事实等级:

- `observed`: 当前任务直接观察到
- `derived`: 有证据推导
- `assumed`: 明示假设
- `unverified`: 未验证

跨 market / locale / currency / stage / auth_state / session 的结论,必须按 `99-SKILLS治理/12-反泛化与任务收敛规约.md` 维护范围账本。没有进入 `in_scope` 的内容,最终答复不能说"已支持"。

涉及批量、并发、指纹、WAF、cookie、session、token cache 时,必须按 `99-SKILLS治理/13-并发指纹与会话隔离规约.md` 做隔离和阶梯验证。未跑并发阶梯时,只能说"单线程已验证"或"连续请求已验证"。

端点、字段、状态、保护、实现或 eval 每次更新,必须按 `99-SKILLS治理/14-知识图谱行程与关联规约.md` 更新 `knowledge-graph.md` 的节点和边。

每次改动后,必须按 `99-SKILLS治理/15-AI变更风险与回归校验规约.md` 在 `impact-regression.md` 写 Impact Record,列明 direct_impact、downstream_impact、required_regression 和 data_validation。

涉及基础逆向、浏览器抓包、验证码、token、cookie/storage/cache、旧/新 HAR、多轮复测时,必须按 `99-SKILLS治理/16-实战复测与证据新鲜度规约.md` 写 run 账本和 Fresh Evidence Table。没有 run_id / capture_id / captured_at / browser_profile_id / state_reset / network_log_id / source_freshness 的关键结论,不能标成 observed。

验证和沉淀完成后,必须按 `99-SKILLS治理/17-交付收尾清理与加密算法图谱规约.md` 做最终清理:删除已替代的临时测试文件、历史输出、废代码和过期注释;涉及 sign/token/加密时,写 `逆向工程经验库/domains/<domain>/encryption-algorithm-graph.md`。

---

## 任务结束的强制沉淀(5 步)

任务结束**强制**走以下五步,否则不算完成:

1. 写 `站点经验库/<domain>/known-failures.md`(失败模式:symptom / stage / market / currency / status / marker / root cause / correct handling)
2. 写 `站点经验库/<domain>/test-log-lessons.md`(这次测试学到什么)
3. 写 `站点经验库/<domain>/change-log.md`(变更记录)
4. 写 `逆向工程经验库/domains/<domain>/reverse-memory.md`(run/capture/replay、旧新 diff、工具失败样本)
5. 接口已稳定 → 调用 `5-沉淀工具层/site-api-adapter` 产出 adapter.yaml / schema.json
6. 调用 `skills-evaluation-governance`:给本次用到的 skill 打分,新失败模式补 eval
7. 写 cleanup ledger,完成临时文件/历史数据/废代码/废注释清理
8. 涉及加密/sign/token 时,写整体加密算法细节图

详见 `99-SKILLS治理/06-网页逆向标准规划.md` 第 2 节阶段 E。

---

## 任务结束的进化 6 问

1. 有没有新触发词? → 更新对应 skill 的 description
2. 有没有新失败类型? → `known-failures.md` + 新增 eval
3. 有没有新分类规则? → `99-SKILLS治理/02-新网站接入分类.md` 加行
4. 有没有新加解密或反爬模式? → `references/` 新增章节
5. 有没有应该加入 eval 的场景? → `evals/`
6. 需不需要升版本号? → 看 `99-SKILLS治理/03-测试评分漂移.md`

---

## memory 同步

任务结束需要同步项目 memory 到站点经验库时:

```bash
python tools/sync_site_memory.py --project <项目路径> --domain <domain> --apply
```

dry-run 见 `tools/README.md`。**不要接 Stop hook 自动跑,会污染无关项目**。

---

## 红线

- 真实扣款一律不在自动化测试环境跑,除非用户**明示**授权
- 不把一次失败硬编码成只适配一个站点的规则
- 不用"评分高"代替真实任务成功
- 不把 assumed / unverified 写成 observed 事实
- 不把单接口、单 market、单 session 成功泛化成全链路成功
- 不声称支持并发,除非有并发阶梯记录和会话隔离证据
- 不改端点/字段/请求头/指纹/实现/eval 而不更新知识图谱和影响回归记录
- 不把旧 HAR、旧 token、旧 scriptId、旧浏览器 profile 当成本次新证据
- 不跳过 reverse-memory/site-memory/captcha-memory 直接重新抓包
- 不把已验证完成后的临时测试文件、旧历史数据、废代码、废注释留在交付面
- 不交付没有整体加密算法细节图的 sign/token 逆向结果
- 不把编码代理规则混入逆向 Skill(代码纪律走 `4-通用规范层/karpathy-guidelines`)
- 不把所有经验塞进一个超长 SKILL.md

---

## 完成前自评铁律

声明"完成 / done / 交付 / 收尾"前,必须跑:

```bash
python tools/verify_delivery.py --domain <当前任务的 domain,或 none>
```

exit_code != 0 时,**不许向用户输出"完成"**。需先补完 blockers 列表中的项,重跑直到 exit 0。

规则源:`99-SKILLS治理/08-完成度自评.md` 的 6 维(Code/Docs/Integration/Regression/Honesty/Cleanup)。

verify_delivery.py 是二级 quality gate;Stop hook 的 `post_task_reminder.py` 是三级(任务结束自动检查)。两者互补。

---

## 自动提醒机制

`.claude/settings.json` 注册了 Stop hook(`tools/post_task_reminder.py`)。
Claude 完成响应时,脚本会扫 transcript:

- 若检测到本次涉及业务 domain
- 且对话中未出现 `sync_site_memory.py` / `score_skills.py` / `skills-evaluation-governance` / `站点经验库` 等沉淀标记
- 则输出 reminder 给 Claude

reminder 是软提示,不阻断流程。脚本异常时静默退出,不影响主任务。

### 触发范围(重要)

Stop hook 由**项目级** `.claude/settings.json` 注册,**只在 Claude Code 的 cwd 是本仓库或其子目录时生效**:

- ✓ 在 `E:/SKILLS/my_reverse_skill/` 内任何子目录工作时,hook 自动触发
- ✗ 在外部项目(如 `C:/Users/Administrator`、`flight-cwl-vj-baggage`)中工作时,**hook 不会触发**

跨项目场景下,任务结束请手动核对 06 规划的阶段 E 沉淀、阶段 F 一致性验证和阶段 G 收尾清理,或在 Claude 中说"按 my_reverse_skill 的完整收尾核对一遍"。

跨项目自动触发需要在 `~/.claude/settings.json` 用户级配置中加 Stop hook 指向本仓库脚本绝对路径,会污染所有项目,**默认不开启,按需手动配**。

### 校准数据

hook 每次触发会写一条记录到 `tools/.reminder-stats.jsonl`(在 `.gitignore` 中,不入 git)。累积 2 周后用于校准 `EXCLUDE_DOMAINS` / `REVERSE_MARKERS` / `PERSIST_MARKERS` 词表。

### 跨平台 python 命令

hook 命令默认 `python`。Windows 上若 `python` 不在 PATH(只装了 Microsoft Store 版可能叫 `py`),把 `.claude/settings.json` 中的 `"python"` 改为 `"py"`。
