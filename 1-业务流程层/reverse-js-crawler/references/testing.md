# Reverse Testing

## Minimum Tests

- Static syntax check for generated code.
- One known-good request with expected response shape.
- One invalid-parameter request to verify error handling.
- Pagination or repeated request loop when the task is collection.
- Data schema check for required fields.

## Stability Claims

Do not say stable unless repeated runs show the same class of result.

Example:

```text
route A x3: code=200, items=20 each
route B x3: code=403, protection=waf-html each
```

## Web/H5 Crawler Hardening

稳定性不是单次成功。Web/H5 爬虫交付必须把以下证据写进 run ledger、validation ledger 或测试报告：

- Packet Evidence: URL/method/status、request/response 摘要、HAR/Network id、initiator、script URL/hash。
- Clean State Retest: `clean_unverified`、`verified`、`repeat_verified` 三组；每组清空 cookie/localStorage/sessionStorage/cache/service worker，或创建新的 isolated browser context。
- Repeat Count: 同一 scope 至少 3 轮同类结果；一成功两失败不能当成功。
- Failure Split: 业务错误、参数错误、token/sign mismatch、环境不匹配、WAF/challenge、频控、数据不可用、实现 bug 分开记录。
- Concurrency Ladder: 涉及批量/并发时按 1/2/5/10 worker 推进，记录请求总数、成功数、失败数、403/429/503、P95、token/cookie 刷新和停止条件。
- Session Isolation: worker 默认不共享 browser context、cookie jar、storage、token cache、账号态；共享必须有当前 run 的后端接受证据。

## Acceptance Report

涉及实战执行、批量、并发、风控证据或网页一致性时，必须生成并验证 acceptance report：

```bash
python tools/web_h5_acceptance_report.py template --out acceptance-report.json --domain <domain> --stage <stage> --target-api <method:url>
python tools/web_h5_acceptance_report.py validate --report acceptance-report.json
```

声明完成、并发或稳定时加 `--require-complete`。没有通过验收报告，只能说 `unverified`、`flaky`、`blocked`、`human_review` 或 `stale`。

验收报告必须覆盖：

- Risk Control: authorization_scope、protected business API backend acceptance、failure split、backoff、jitter、session retirement、kill switch、human review boundary。
- UI/API Parity: 网页可见字段、API JSON Pointer、tolerance、screenshot/DOM evidence、consistency_rate。
- Fixture Freshness: strict-review exit code、expired_count、review_pending_count、recent replay report、source_freshness。
- Metrics: task_count、success_browserless_verified、concurrency_verified、strict_review_pass_count、flaky_count、blocked_by_protection。

风控相关恢复动作只能是隔离、退避、停止并发、retire session、重录 fixtures 或人工复核；不写绕过、指纹伪造、代理轮换或复用旧 clearance cookie。

## Logging

Log:

- input parameters
- trace/session id
- endpoint and method
- status code
- business code/message
- elapsed time
- response summary

Do not print full tokens or sensitive cookies in normal logs.

