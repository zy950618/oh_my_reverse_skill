# captcha-service-delivery failure sample and metric seed

任务总数: 4
真实任务下限: 4

This seed records real engineering failure shapes the skill must catch. It is not a production success-rate claim.

| date | sample | observed failure | required regression |
|---|---|---|---|
| 2026-06-12 | old-token-as-new | Agent reused a token from an old HAR and marked it observed for the current run. | Require capture_id, captured_at, source_freshness, and fresh revalidation. |
| 2026-06-12 | verified-cookie-confusion | Agent mixed verified browser cookies into clean anonymous capture. | Require clean_unverified vs verified browser state separation. |
| 2026-06-12 | stale-script-cache | Browser cache served old widget or business bundle. | Require script hash and cache/service-worker state. |
| 2026-06-12 | no-repeat-test | One verified request succeeded and agent claimed stable support. | Require repeat_verified capture and TTL/session binding check. |

Success rate: 0%

The initial success rate is intentionally 0% until these samples are executed by a real eval harness.
