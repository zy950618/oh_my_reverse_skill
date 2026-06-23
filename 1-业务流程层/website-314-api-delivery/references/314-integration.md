# Local Base Framework Integration

## When To Use A Local Base Framework

Start with Python/FastAPI interface test delivery. Use a local base framework only after:

- the target Python/FastAPI interfaces pass against the real upstream stage requirements
- the user confirms whether to integrate a local base framework
- the user chooses `314` or names another local framework

Use 314 only when:

- the user explicitly chooses 314, `flight_cwl_common_314`, or the 314 base framework after FastAPI tests pass
- the project already imports and depends on the 314 framework and the user confirms that branch
- the final output must be a 314 service rather than the standalone FastAPI test API

## Service Boundaries

Recommended split:

```text
api/
  routes/<vendor>/
  services/<vendor>/
  anti_bot/<vendor>/
  crypto/<vendor>/
  tests/
reverse/<vendor>/
```

Responsibilities:

- routes: HTTP endpoint mapping and request/response DTOs
- services: business flow orchestration
- anti_bot: WAF, captcha, Reese84, challenge state
- crypto: sign/token/cookie generation that is not WAF-specific
- reverse: extracted scripts, Node runners, debug artifacts
- tests: service-level and HTTP API tests

## Logging Requirements

Chinese API logs should include:

- 接口名称
- 路径
- session_id / trace_id
- 入参摘要
- 阶段
- 耗时
- 返回码
- 信息 / 原始信息
- 返回摘要

Do not log full tokens, cookies, card data, or passenger sensitive data.

## Test Requirements

- FastAPI HTTP tests must pass before framework rewrite starts
- direct service tests
- HTTP router tests
- 2-3 stability loops for key endpoints
- negative tests for invalid route/date/passenger
- WAF marker tests when applicable
- payment dry-run or sandbox tests only, unless real payment is explicitly authorized

