# Human review protocol for CAPTCHA verification

Use this when a provider challenge prevents the `verified` or `repeat_verified` capture from completing through normal observation.

## Required status

If `verified` or `repeat_verified` is missing, set:

```yaml
completion_status: blocked
blocked_stage: verified | repeat_verified
blocked_reason: manual_challenge_required
verification_mode: blocked_by_manual_challenge
```

Do not call the task complete. Do not use provider config, widget load, iframe load, or HTTP 200 as a substitute for verified business acceptance.

If an authorized browser automation flow completes the challenge without human action, record it as `browser_automated_verified` only after the site backend accepts the final business API in both `verified` and `repeat_verified` rounds. Until then, keep the status `blocked` or `incomplete`; do not write "automatic pass".

## Assisted capture protocol

Output these fields before asking for human action:

```yaml
Human Review Protocol:
  visible_browser:
    required: true
    launch_command_or_tool: <how the operator opens a visible browser>
    browser_profile_id: <new profile id or user data dir>
    state_reset: <cookies/storage/cache/service workers cleared or recorded>
  target:
    url: <exact URL>
    variant: <widget/sitekey/mode>
    auth_state: <anonymous/login/etc>
  user_action:
    instruction: <complete only the visible CAPTCHA challenge; do not perform out-of-scope actions>
    stop_after: <what UI/result means the user should stop>
  live_capture:
    listener: <DevTools/HAR/webparity/MCP/Playwright trace>
    must_capture:
      - provider challenge/config requests
      - site verify endpoint request/response
      - cookie/localStorage/sessionStorage writes
      - screenshot after completion
  completion_criteria:
    token_state: <token field non-empty or provider callback fired>
    backend_acceptance: <site verify/business endpoint JSON Pointer success>
    repeat_verified_required: true
    evidence_required:
      - request URL/method/status
      - redacted request fields
      - response JSON Pointer
      - capture_id and timestamp
  repeat_flow:
    action: <new context or refresh/reopen>
    expected: <same verified effect without reusing old token unless explicitly observed>
    failure_handling: <record blocker/failure path and do not claim repeat_verified>
  artifact_paths:
    har: <path>
    summary: <path>
    screenshot: <path>
    memory_update: <path>
```

## Evidence rules

- Store token presence, token length, and field names; do not store token values.
- Redact provider payloads, challenge IDs, motion data, image IDs, and token-like long values.
- Record any manual step as `human_reviewed_verified`, not `browser_automated_verified`.
- Record browser automation as `browser_automated_verified` only when authorized, backend-accepted, and repeat-verified.
- If the user cannot complete the challenge, write `known-failures.md`, `captcha-memory.md`, and `impact-regression.md` with `verified: blocked_by_manual_challenge`.

## Continuation protocol

After a solved capture is provided:

1. Validate artifact freshness and profile identity.
2. Compare `clean_unverified` vs `verified`.
3. Run `repeat_verified` with a new context or documented refresh.
4. Update graph and impact records.
5. Re-run `tools/verify_delivery.py --domain <domain>`.
