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
