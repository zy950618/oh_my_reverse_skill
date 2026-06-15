# env-patch graph and impact examples

Use these examples when runtime stubs or Node wrapping change downstream behavior.

## Example 1: Minimal navigator dependency

Graph Delta:

```text
node js_function:buildSearchSign
node env_dep:navigator.userAgent
node request_field:header.x-sign
node script:env/run.js
node eval:env-patch/browser-node-parity

edge js_function:buildSearchSign -> env_dep:navigator.userAgent reads
edge env_dep:navigator.userAgent -> script:env/run.js stubbed_in
edge request_field:header.x-sign -> js_function:buildSearchSign generated_by
edge js_function:buildSearchSign -> eval:env-patch/browser-node-parity covered_by
```

Impact Regression:

```text
change: add observed navigator.userAgent stub to run.js
impacted:
  - js_function:buildSearchSign
  - request_field:header.x-sign
  - storage/cache assumptions for the active session
  - replay fixture for /api/search
must_run:
  - node env/run.js
  - browser-vs-Node signature comparison
  - snapshot_replay if request replay is claimed
risk:
  - copied UA from one session generalized to all sessions
  - fake browser profile grows beyond observed dependencies
```

## Example 2: Risk/fingerprint observation only

Graph Delta:

```text
node protection:fingerprint-observed
node env_dep:window.screen
edge js_function:buildRiskFields -> env_dep:window.screen reads
edge env_dep:window.screen -> protection:fingerprint-observed contributes_to
```

Boundary:

```text
allowed: record observed read path, stability, and missing value
stale_or_unverified: broad screen/webgl/canvas profile values without capture evidence
```
