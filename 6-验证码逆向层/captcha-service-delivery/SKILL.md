---
name: captcha-service-delivery
standard_type: captcha_model_delivery
description: >-
  Conditional CAPTCHA/verification-service skill for Web/H5 reverse-engineering
  tasks with explicit CAPTCHA evidence or provider terms: Google reCAPTCHA,
  hCaptcha, Cloudflare Turnstile, slider/click-select CAPTCHA, sitekey/action,
  challenge config, captcha token/state, backend verify endpoint,
  verified-vs-unverified API delta, token TTL, session binding, or business API
  unlock blocked by CAPTCHA. It maps provider flow, site binding, token
  lifecycle, repeat verification, knowledge graph, impact regression, and
  backend acceptance boundaries. Do not trigger for generic
  "验证/validation/test" wording, ordinary sign/x-sign entry location, WAF
  without CAPTCHA, or provider test-key checks that lack a real site/business
  acceptance target.
platforms: [web, h5]
---

# captcha-service-delivery

验证码逆向层的总入口。目标是把验证码/验证服务当成真实服务链路处理:

```text
provider widget/challenge
  -> site binding
  -> challenge/config request
  -> verification token/result
  -> backend verify endpoint
  -> session/risk state
  -> business API unlock/deny
```

Version: 0.1.7

Change log:
- 0.1.7 adds Phase 2.1 business data assertion gate: CAPTCHA/WAF/risk positive claims require final business API acceptance plus server-side business ledger data assertions; challenge/verify success, HTTP 200, direct repeat, or worker PASS alone are not positive.
- 0.1.6 adds Phase 2 high-fidelity local risk-lab boundary: self-owned localhost evidence can be positive for server-side risk state, one-time token lifecycle, final business API direct repeat, negative token/session/action/worker evals, and business API worker isolation; it remains non-positive for third-party CAPTCHA/WAF/risk-control bypass or production fingerprint handling.
- 0.1.5 adds Phase 1 local execution boundary: localhost CAPTCHA dummy and Turnstile dummy runs with screenshot/network/state evidence may create negative or boundary evals, but local dummy pass states remain non-positive without real provider token/state, final business API backend acceptance, and repeat direct verification.
- 0.1.4 adds public-range harness boundaries: allowlisted official demos/testing keys can create boundary or negative eval evidence, but provider test-key success cannot become positive capability without real site token/state, final business API backend acceptance, and repeat verification.
- 0.1.3 adds validation-to-eval evolution: fresh blocked/incomplete CAPTCHA validation can create negative or boundary evals, but cannot raise positive SKILLS capability without verified, repeat-verified backend acceptance.
- 0.1.2 clarifies automation/human-review evidence modes: browser automation can be claimed only after authorized backend acceptance and repeat verification; blocked challenges cannot be written as auto-pass capability.
- 0.1.1 adds delivery/memory/SKILLS separation: project delivery code cannot become positive SKILLS capability; only successful, repeat-verified experience memory can feed positive scoring.
- 0.1.0 creates the Web/H5 CAPTCHA reverse layer with structured evals, provider/site memory, graph/impact examples, and real capture freshness gates.

## Workflow

1. Read `4-通用规范层/karpathy-guidelines/SKILL.md`.
2. Read `99-SKILLS治理/11-AI事实证据规约.md`, `12-反泛化与任务收敛规约.md`, `13-并发指纹与会话隔离规约.md`, `14-知识图谱行程与关联规约.md`, `15-AI变更风险与回归校验规约.md`, and `16-实战复测与证据新鲜度规约.md`.
3. Read existing experience before new capture:
   - `站点经验库/<domain>/known-failures.md`
   - `站点经验库/<domain>/test-log-lessons.md`
   - `验证码经验库/providers/<provider>.md`
   - `验证码经验库/domains/<domain>/captcha-memory.md`
4. Classify provider and type: `recaptcha`, `hcaptcha`, `turnstile`, `slider`, `click-select`, `custom-risk-state`, or `unknown`.
5. Capture at least three states: `clean_unverified`, `verified`, `repeat_verified`.
6. If provider interaction requires a manual challenge, stop the success path, read `references/human-review-protocol.md`, output the protocol, and mark the task `blocked` until a solved capture exists.
7. Compare old vs new evidence, verified vs unverified response, token TTL, session binding, and business API unlock.
8. Update graph and impact records before final output.
9. For public-range training, read `public-range-evidence/_allowlist.yaml` first and write one sanitized evidence JSON under `public-range-evidence/<target_id>/`. Official provider demos or testing keys are `boundary_eval` / `negative_eval` unless a real site/business flow also satisfies the positive gate.

## Hard Delivery Gate

Every final output must include:

- Fresh Evidence Table: `capture_id`, `captured_at`, `browser_profile_id`, `state_reset`, `auth_state`, `network_log_id`, `script_hash`, `source_freshness`.
- Provider Flow: widget/config/token/verify/state/business API chain.
- Site Binding: domain, sitekey, action/mode, token field, verify endpoint, business endpoint, auth/session boundary.
- Verified-vs-Unverified Diff: request fields, response JSON Pointers, cookie/storage writes, unlock behavior.
- Old-vs-New Diff: stale captures invalidated and reused captures revalidated.
- Graph Delta: provider, binding, token, verify endpoint, state, business endpoint, eval nodes and edges.
- Impact Regression: direct/downstream impact, required retests, TTL/session/concurrency risk.
- Validation Commands or Artifacts: HAR path, DevTools request ids, replay/diff commands, or explicit blocker.
- Fact Labels: observed, derived, assumed, unverified.
- Scope Ledger: target domain, flow, auth_state, requested capability, evidence source, and unresolved blockers.
- Completion Status: `complete`, `blocked`, or `incomplete`. If `verified` or `repeat_verified` is missing, the status cannot be `complete`.
- Verification Mode: `browser_automated_verified`, `human_reviewed_verified`, `blocked_by_manual_challenge`, `blocked_by_protection`, or `unverified`.
- Human Review Protocol: required when a CAPTCHA challenge blocks `verified` capture.
- Delivery / Memory / Skills Separation: project delivery artifact, experience memory path, delivery status, and skills participation. CAPTCHA adapters, recorder scripts, and site-specific demos are delivery artifacts or tools; they do not become SKILLS positive capability unless the corresponding experience memory is successful and repeat-verified.

## Success Criteria

- Use `captcha-service-delivery` only after CAPTCHA or verification-service evidence exists.
- Produce provider flow, site binding, fresh evidence table, verified-vs-unverified diff, old-vs-new diff, graph delta, and impact regression.
- Write new lessons to `验证码经验库/domains/<domain>/captcha-memory.md` and relevant known failures/test log entries.
- Mark stale captures, old tokens, old script ids, and uncleared browser profiles as `unverified` until revalidated.
- This skill is not responsible for ordinary crypto-entry location, generic WAF token work, or site-api-adapter standardization.
- Treat `clean_unverified` plus a blocked challenge as a valid failure sample, not as a completed delivery.
- Do not pass delivery as complete unless `clean_unverified`, `verified`, and `repeat_verified` are all backed by fresh evidence or the final status is explicitly `blocked`.
- Do not promote project delivery code, provider adapters, or blocked recorder output into SKILLS positive examples. Only successful, repeat-verified `验证码经验库/domains/<domain>/captcha-memory.md` entries may feed positive SKILLS scoring. Blocked and negative samples may feed only known-failures, test-log lessons, human-review/refusal ledgers, or negative evals.
- Do not claim "automatic pass" for Turnstile, Akamai, Cloudflare, hCaptcha, reCAPTCHA, or any managed challenge unless an authorized browser automation run produced token/state evidence and the final business API accepted it in both `verified` and `repeat_verified` rounds.
- Public-range provider demos, Turnstile testing keys, standalone siteverify responses, widget/script observations, and manual challenge blockers may update evals and evidence, but they must not set `skills_participation: positive_allowed`.
- Local CAPTCHA or Turnstile dummy labs with real browser screenshots, DOM, network summaries, and state observers are still dummy boundary evidence. A local `dummy_passed`, `always_pass`, or duplicate-token state cannot become positive CAPTCHA capability without real provider token/state and final protected business API repeat acceptance.
- `execution_status: REAL_EXECUTION_PASS` only means the local or provider-testing flow actually ran. CAPTCHA/WAF positive capability requires `capability_status: positive_allowed` plus real provider token/state, final protected business API backend acceptance, and repeat direct interface acceptance.
- Local dummy CAPTCHA, Turnstile testing keys, and siteverify dummy results must stay `negative_eval_only` or boundary eval unless they are attached to a real authorized site/business flow that satisfies the positive gate.

## Evidence-Backed Phase 1 Update

- Evidence run_id: `run-20260629-091645-gocaptcha-local-dummy`, `run-20260629-091645-cloudflare-turnstile-local-dummy`.
- Triggered failure: a local dummy CAPTCHA pass state or testing-key boundary could be mistaken for real CAPTCHA automation success.
- Skill change: explicitly keep localhost dummy CAPTCHA/Turnstile evidence in negative or boundary participation unless real provider and business API acceptance gates are satisfied; split execution success from capability success.
- Added eval: `evals/017-negative-local-dummy-captcha-boundary.yaml`.
- Regression commands: `python tools/validate_real_execution_proof.py public-range-evidence`; `python tools/validate_public_range_evidence.py public-range-evidence`.

Phase 1 classification: local dummy and testing-key runs are accepted only as proof that the local execution framework, screenshot/network capture, state observer, and boundary negative eval flow work. They do not prove real CAPTCHA automation, WAF/risk-control passage, or third-party provider positive capability.

## Evidence-Backed Phase 2 Update

- Evidence run_id: `run-20260630-013842-high-fidelity-risk-lab`.
- Triggered failure evidence: earlier local dummy challenge evidence had no server-side risk state machine, no final business API unlock, no direct repeat, no token expiry/duplicate/wrong-session/wrong-action/cross-worker negative matrix, and no business API concurrency ladder.
- Skill change: allow a self-owned high-fidelity local risk lab to count as `positive_allowed` only for local risk-state delivery mechanics when final business API acceptance, direct and repeat direct replay, negative lifecycle evals, and worker isolation are all observed. Do not convert it into real CAPTCHA automation, managed challenge bypass, WAF bypass, or production fingerprint capability.
- Added eval: `evals/018-high-fidelity-local-risk-lab-boundary.yaml`.
- Regression commands: `python tools/run_phase2_high_fidelity_risk_lab.py`; `python tools/validate_public_range_evidence.py public-range-evidence`; `python tools/validate_real_execution_proof.py public-range-evidence`.

Phase 2 classification: local risk-lab positive evidence is valid for server-generated one-time token lifecycle and final business API repeat acceptance on localhost. Real provider token/state, authorized protected business API acceptance, and repeat direct verification are still required before any third-party CAPTCHA/WAF/risk-control positive capability claim.

## Evidence-Backed Phase 2.1 Update

- Evidence run_id: `run-20260630-022227-high-fidelity-risk-lab`.
- Triggered failure evidence: challenge endpoint success, verify endpoint success, browser success, direct repeat, and worker PASS can still miss wrong item, missing detail, stale version, duplicate order, orphan order, wrong owner, or negative-eval side effects.
- Skill change: CAPTCHA/WAF/risk-control acceptance must use the final business API and server-side business ledger as the source of truth. Negative evals must prove `ledger_delta=0`; concurrency must prove order/session/worker ownership.
- Added eval: `evals/019-business-ledger-required-for-risk-positive.yaml`.
- Regression commands: `python tools/validate_business_data_assertions.py public-range-evidence`; `python tools/validate_public_range_evidence.py public-range-evidence`; `python tools/validate_real_execution_proof.py public-range-evidence`.

Phase 2.1 classification: the local lab is positive only for localhost business-data assertion mechanics. It is not evidence of third-party CAPTCHA/WAF bypass, production fingerprint handling, or external target concurrency.

## Scope Ledger

For every CAPTCHA or verification-service task, record the engineering scope instead of embedding assistant capability boundaries in the skill:

- target domain, market, stage, route, and auth_state;
- provider/type evidence and why this skill was selected;
- requested deliverable: flow mapping, interface replay, adapter handoff, regression, or incident analysis;
- current evidence state: fresh, stale, unknown, or blocked;
- old captures being reused and the fresh capture that revalidated them;
- unresolved blockers and the next concrete capture or replay needed.

If evidence is missing, mark the relevant claim `unverified` and write the capture requirement. Do not convert a stale token, stale HAR, stale script id, or stale browser profile into current observed fact.

## Governance

- Drift policy: treat provider script hash changes, sitekey/action changes, token field movement, verify endpoint changes, cache/service-worker effects, and verified/unverified response drift as blocking drift.
- Before any concurrency claim, require session/cache/cookie/storage isolation and a replay ladder.
- Before reusing prior experience, record the old capture and the fresh capture that revalidated it.
- Every new real failure must update `known-failures.md`, `test-log-lessons.md`, or `验证码经验库/domains/<domain>/captcha-memory.md`.
- Every fresh validation that exposes a blocked or incomplete CAPTCHA path should update or add a negative/boundary eval so the SKILLS library evolves, but only successful `verified` plus `repeat_verified` backend acceptance may become positive capability.
- Official provider test keys, provider config responses, and standalone siteverify calls may be used only as boundary evidence or negative eval material. They must not become reusable positive capability without real site token/state evidence, final business API backend acceptance, and repeat verification.
- Public-range harness runs must stay inside the allowlist. Non-allowlist targets are observation-only, and real third-party production CAPTCHA/WAF behavior must not be converted into a reusable bypass or auto-pass rule.

## Output Template

```text
Provider:
Captcha Type:
Scope Ledger:
Fresh Evidence Table:
Provider Flow:
Site Binding:
Verified-vs-Unverified Diff:
Old-vs-New Diff:
Token/State Lifecycle:
Business API Unlock:
Graph Delta:
Impact Regression:
Validation Artifacts:
Fact Labels:
Verification Mode:
Scope Ledger:
Unverified / Blockers:
Completion Status:
Human Review Protocol:
```

## References

- `references/governance.md`: hard process, evidence freshness, and failure handling.
- `references/provider-flow.md`: provider common flow abstraction.
- `references/site-binding.md`: site-specific binding schema.
- `references/real-capture-protocol.md`: browser cleanup, HAR capture, multi-round comparison.
- `references/human-review-protocol.md`: visible browser/profile/user-action/listener protocol when a CAPTCHA challenge requires human completion.
- `references/graph-impact-examples.md`: graph and impact examples.
