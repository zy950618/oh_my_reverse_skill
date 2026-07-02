# Real Website Handling Playbook

Source run_id: `run-20260630-163000-phase3-10-realism-hardening`

This playbook separates training ranges, self-owned labs, authorized targets, official demos, and unknown production sites. CAPTCHA, WAF, fingerprint, and risk-control surfaces are training targets only when scope allows it. Unknown third-party and production-unverified targets remain observation-only.

## 1. Scope Decision

- `localhost_lab`: self-owned local lab. Solver, replay, JS parity, negative eval, business ledger, and concurrency are allowed.
- `localhost_vendor_compatible_lab`: self-owned vendor-like simulation. It can train visual/action logic but must say `compatible_not_official`.
- `localhost_waf_lab`: self-owned JS/WAF challenge simulation. It can prove local challenge-to-business closure but not real WAF bypass.
- `official_demo_readonly`: official page or docs where action replay is not explicitly allowed. Provider diagnostics and state observation only.
- `official_demo_action_allowed`: official demo with explicit interactive testing permission. Action replay can be candidate only.
- `self_owned_trial`: a user-owned vendor test instance with scene/app/organization scope.
- `authorized_vendor_integration`: written/internal authorization with allowed hosts, rate limit, stop condition, and redaction.
- `unknown_third_party` or `production_unverified`: observation-only and manual handoff.

## 2. Block Type

Record the observed blocker as CAPTCHA provider, WAF/five-second shield, JS signature, fingerprint block, rate limit, auth/session expired, or business rule block.

## 3. Route Selection

- Visual solver/action replay: only public range, localhost lab, self-owned trial, or authorized target.
- Human-in-loop: allowed for unknown third-party when automation is not authorized.
- JS runtime parity: only local/self-owned/authorized scope; never token forgery.
- Official API fallback: preferred for production integrations.
- Rate limit/backoff: only within target terms and scope.
- Authorized adapter: requires allowed hosts, stop condition, evidence redaction, and business assertions.
- Stop and ask for authorization: required for unknown third-party or production-unverified challenge handling.

## 4. Evidence Requirements

Evidence must include screenshot, network summary, state transition, JS parity report when JS/WAF is involved, fingerprint surface report when diagnostics are involved, business ledger for business API claims, direct repeat without browser profile or manual cookie reuse, negative eval with ledger delta zero, and concurrency ledger when concurrency is claimed.

## 5. Forbidden Actions

Do not perform or document unauthorized bypass, token forgery, production WAF bypass, fingerprint spoofing, clearance reuse on real sites, proxy evasion, or third-party solver API use.

## 6. Capability Output

Use `observation_only`, `memory_only`, `training_needed`, `positive_candidate`, `positive_verified`, `stable_positive`, or `prohibited`.

Official demo success does not generalize to third-party sites. Compatible lab success does not generalize to official vendor production. Local five-second shield success does not prove real WAF bypass.

## 7. Actual Website Decision Flow

1. Classify scope first:
   - `unknown_third_party`: observation-only, no automated challenge handling.
   - `production_unverified`: observation-only, ask for authorization or official API.
   - `official_demo_readonly`: diagnostics only unless action replay permission is explicit.
   - `compatible_lab`: training only, never official production proof.
   - `self_owned_trial` or `authorized_target`: full workflow only within allowed hosts, rate limit, stop condition, kill switch, and redaction policy.

2. If Shumei is observed:
   - Run provider diagnostics and mode detection.
   - Decide whether it is official demo, self-owned scene, authorized target, or unknown production.
   - For self-owned/authorized scope, collect visual mode, server verify endpoint, final business API, negative eval, and business data assertions.
   - Do not generalize compatible-lab results to third-party production.

3. If Aliyun CAPTCHA is observed:
   - Identify scene/captcha config and client state.
   - Separate client token/state observation from server verify.
   - For `no_trace` or one-click flows, record state machine and backend verify only; do not call it a bypass.
   - Require final business API and ledger assertions before any positive claim.

4. If a five-second shield or WAF-like flow is observed:
   - Record redirect chain, challenge script, runtime contract, clearance lifecycle, and final business API.
   - Validate Browser/Node/PageRuntime parity and mutation parity only in local/self-owned/authorized scope.
   - Do not reuse real-site clearance, do not forge production tokens, and stop automated challenge handling without authorization.

5. If fingerprint blocking is observed:
   - Capture fingerprint surface and profile consistency.
   - Attribute risk signals without spoofing or evasion.
   - Allowed fallbacks are profile isolation, rate limits, human-in-loop, official API, or explicit authorization.

## 8. Output States

- `observation_only`: diagnostics only; no replay.
- `training_needed`: evidence exists but thresholds, realism, or failure replay are insufficient.

## 9. Phase 3.12 Authorized Training Strategy

Source run_id: `run-20260630-183000-phase3-12-model-flywheel`

When a real website is involved:

1. Classify scope before any interaction.
2. If scope is unknown or production-unverified, stay observation-only.
3. If scope is self-owned or explicitly authorized, sampling is allowed only inside the declared allowed hosts and stop condition.
4. Redact samples before writing them to the flywheel:
   - Do not save real tokens.
   - Do not save real cookies.
   - Do not save auth headers.
   - Do not save personal information.
5. Save only the scoped training surface:
   - challenge screenshot or crop.
   - instruction text.
   - allowed action schema.
   - feedback state.
   - failure reason.
6. Store authorized samples under `datasets/captcha_flywheel/authorized/`.
7. Before training, run label, redaction, leakage, blackbox, and anti-solver audits.
8. After training, retest only in the same authorized target scope.
9. Do not generalize authorized target capability to other third-party websites.

Third-party CAPTCHA solving platforms, remote solver APIs, paid human solver services, copied browser tokens, copied clearance cookies, DOM answers, query expected values, server expected values, and provider internal tokens are prohibited solver sources.
- `positive_candidate`: scoped lab/public/authorized result passed single-run gates.
- `positive_verified`: repeat/ledger/business gates passed in scope.
- `stable_positive`: repeat runs and drift gates pass; never from a single run.
- `prohibited`: requested action is outside scope.
- `blocked_authorization_required`: self-owned or authorized configuration is missing.

## 9. Phase 3.10 Experience

Evidence:

- `public-range-evidence/shumei-compatible-lab/run-20260630-163000-phase3-10-realism-hardening.json`
- `public-range-evidence/aliyun-compatible-lab/run-20260630-163000-phase3-10-realism-hardening.json`
- `public-range-evidence/five-second-shield-lab/run-20260630-163000-phase3-10-realism-hardening.json`
- `public-range-evidence/raw/challenge-realism-audit/run-20260630-163000-phase3-10-realism-hardening/challenge-realism-audit.json`

Evals:

- `evals/phase3-10/shumei-compatible-lab-hardening.yaml`
- `evals/phase3-10/aliyun-compatible-lab-hardening.yaml`
- `evals/phase3-10/five-second-shield-lab-dynamic.yaml`

Capability level:

- Shumei/Aliyun compatible families are `positive_candidate` only.
- Shumei/Aliyun official trials are `blocked_authorization_required` until self-owned config exists.
- Five-second shield lab is a local WAF candidate only, not production WAF bypass.

Next training goals:

- Add real self-owned official trial evidence.
- Add repeat-run drift and soak tests.
- Add hard/adversarial failure replay fixes before verified/stable promotion.
