# 逆向工程经验库

这个目录沉淀 Web/H5 逆向工程的真实实战经验,重点解决:

- 每次重新开荒,不吸收上次经验。
- 反复测试时分不清旧数据和新数据。
- 旧 HAR、旧 token、旧 scriptId、旧 browser profile 被误写成当前事实。
- 改 A 伤 B 后没有影响回归。
- 抓包、断点、补环境、回放、数据校验的失败样本没有进入下一轮流程。

它不是 `站点经验库/` 的替代品:

- `站点经验库/` 记录 domain 的业务链路、路由、market、图谱、adapter 和站点级失败。
- `验证码经验库/` 记录验证码 provider 和站点绑定。
- `逆向工程经验库/` 记录逆向过程本身的 run/capture/replay 证据、旧新数据判断、工具失败、复测策略和下次进入任务前必须先看的经验。

## GitHub 边界

GitHub 只保留本目录的 README、`_templates/` 和 `_example.com/` 示例。`domains/<真实域名>/` 是本地项目经验库，默认不上传。

经验库只写能帮助下次不从头开始、不重复犯同类错误的操作细节: 入口判断、断点/抓包顺序、保护状态识别、旧新数据判定方法、失败纠正、影响回归和加密算法图谱摘要。禁止写入真实业务数据、完整接口响应、token/cookie、账号、订单、支付、旅客、浏览器 profile、HAR/jsonl 原始数据或可还原请求载荷。

需要保留证据时,本地保存原始数据,可上传材料只写脱敏后的 observed / derived 摘要和复现步骤。

## 正式沉淀准入

研发阶段可以保留完整抓包、脚本、失败尝试和假设,但这些只属于本地临时项目库。进入正式经验库必须满足:

- 已完成确认或未完成确认已经写清。
- 有真实接口测试、replay、最终业务 API 后端接受,或明确的 blocked/negative 证据。
- 记录下次不再重复的踩坑点和错误路径。
- 内容精炼为操作顺序、状态判断、字段/算法含义、验证命令、影响回归和剩余风险。
- 不包含真实 token/cookie/profile/完整 payload/订单或账号数据。

## 目录结构

```text
逆向工程经验库/
├── README.md
├── _templates/
│   ├── reverse-memory.md
│   ├── capture-run.md
│   ├── old-new-diff.md
│   ├── tool-failure.md
│   ├── replay-validation.md
│   ├── encryption-algorithm-graph.md
│   └── delivery-cleanup.md
└── domains/
    └── _example.com/
        └── reverse-memory.md
```

## 使用规则

每个真实逆向任务开始前:

1. 先读 `逆向工程经验库/domains/<domain>/reverse-memory.md`。
2. 再读 `站点经验库/<domain>/known-failures.md`、`test-log-lessons.md`、`knowledge-graph.md`、`impact-regression.md`。
3. 若涉及验证码,再读 `验证码经验库/providers/<provider>.md` 和 `验证码经验库/domains/<domain>/captcha-memory.md`。
4. 创建新的 `run_id`,不要复用旧 HAR/旧 token/旧 profile 作为当前 observed。

每个真实逆向任务结束前:

1. 写回本轮 run 账本。
2. 写回 old-vs-new diff。
3. 写回工具失败样本和下次排查顺序。
4. 写回数据偏移、字段漂移、脚本 hash 变化和影响回归入口。
5. 涉及 sign/token/加密时写整体加密算法细节图。
6. 验证完成后写 cleanup ledger,删除已替代的临时测试文件、历史输出、废代码和废注释。

缺少这些记录时,只能说"本轮未沉淀真实经验",不能说"经验已吸收"。
