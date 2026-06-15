# find-crypto-entry graph and impact examples

Use these examples as the minimum shape for tool-layer graph and regression records.

## Example 1: Header signature entry

Graph Delta:

```text
node endpoint:/api/search
node request_field:header.x-sign
node js_function:buildSearchSign
node script:https://example.test/static/search.8ad3.js
node eval:find-crypto-entry/header-sign

edge endpoint:/api/search -> request_field:header.x-sign uses
edge request_field:header.x-sign -> js_function:buildSearchSign generated_by
edge js_function:buildSearchSign -> script:https://example.test/static/search.8ad3.js located_in
edge js_function:buildSearchSign -> eval:find-crypto-entry/header-sign covered_by
```

Impact Regression:

```text
change: x-sign entry moved from request wrapper to search SDK
impacted:
  - endpoint:/api/search
  - endpoint:/api/detail
  - request_field:header.x-sign
  - eval:request-replay/search
must_run:
  - snapshot_replay for search and detail
  - snapshot_diff for header/body field movement
  - schema_alert for response version drift
risk:
  - stale bundle hash
  - function renamed by minifier
  - one session success generalized to all sessions
```

## Example 2: Risk-control observation only

Graph Delta:

```text
node protection:risk-token
node request_field:body.riskToken
node js_function:getRiskToken
edge request_field:body.riskToken -> protection:risk-token protected_by
edge request_field:body.riskToken -> js_function:getRiskToken observed_source
```

Boundary:

```text
allowed: observe token creation point, lifetime, refresh timing, and stability across sessions
stale_or_unverified: copied clearance cookie, copied fingerprint, copied CAPTCHA state, copied proxy/session state, or copied risk token
```
