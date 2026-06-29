---
name: captcha-service-delivery
description: Conditional CAPTCHA/verification-service skill for Web/H5 reverse-engineering tasks with explicit CAPTCHA evidence or provider terms: Google reCAPTCHA, hCaptcha, Cloudflare Turnstile, slider/click-select CAPTCHA, sitekey/action, challenge config, captcha token/state, backend verify endpoint, verified-vs-unverified API delta, token TTL, session binding, or business API unlock blocked by CAPTCHA. It maps provider flow, site binding, token lifecycle, repeat verification, knowledge graph, impact regression, and backend acceptance boundaries. Do not trigger for generic "验证/validation/test" wording, ordinary sign/x-sign entry location, WAF without CAPTCHA, or provider test-key checks that lack a real site/business acceptance target.
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

Version: 0.1.3

Change log:
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
