# Challenge State Lab Replay Or Trace Report

status: PASS

scope: local synthetic fixtures only

## Covered Cases

- no_challenge
- captcha_detected
- waf_challenge_detected
- fingerprint_challenge_detected
- login_required
- rate_limited
- forbidden
- token_expired
- manual_review_required
- pure_api_replay_ready
- pure_api_replay_blocked

## Safety

- No live cookies, tokens, HAR, accounts, passenger data, payment data, or browser profiles are committed.
