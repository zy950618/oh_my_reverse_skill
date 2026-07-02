Version: 0.1.3

# captcha-service-delivery governance

## Why this exists

CAPTCHA reverse work fails when the agent treats an old token, old HAR, old browser profile, or old script hash as current evidence. This skill requires real capture freshness and repeated comparison before any delivery claim.

## Mandatory sequence

1. Read prior experience.
2. Create a fresh capture plan.
3. Clear browser state or record why it cannot be cleared.
4. Capture `clean_unverified`.
5. Complete verification through authorized/manual flow.
6. Capture `verified`.
7. Restart/refresh and capture `repeat_verified`.
8. Compare all three captures plus any old evidence.
9. Update graph and impact regression.

## Completion gate

Set an explicit completion status for every CAPTCHA task:

```yaml
completion_status: complete | blocked | incomplete
```

Use `complete` only when `clean_unverified`, `verified`, and `repeat_verified` all have fresh evidence. If a provider challenge blocks token generation or backend acceptance, use `blocked`, write a Human Review Protocol, and do not claim delivery success. A negative baseline is useful evidence, but it is not a completed verification flow.

Record the verification mode for every run:

```yaml
verification_mode: browser_automated_verified | human_reviewed_verified | blocked_by_manual_challenge | blocked_by_protection | unverified
backend_acceptance: <final business API JSON Pointer / status / code>
repeat_verified: true | false
authorization_scope: <user-approved scope>
```

`browser_automated_verified` requires an authorized browser automation run, token/state evidence, final business API backend acceptance, and repeat verification. A managed challenge, provider config response, token endpoint response, or 403 challenge page is not enough.

## Delivery / memory / skills separation

CAPTCHA work must keep three layers separate:

```yaml
project_delivery_artifact: <single file/package/tool path>
experience_memory_path: 验证码经验库/domains/<domain>/captcha-memory.md
completion_status: complete | blocked | incomplete
skills_participation: positive_allowed | negative_eval_only | memory_only | prohibited
```

Rules:

- Project delivery code, recorder tools, adapters, demos, and one-off scripts are deliverables or tools, not SKILLS positive capability.
- Experience memory is a summarized, cleaned, post-run record. Do not place delivery code inside it.
- `positive_allowed` requires fresh `clean_unverified`, `verified`, and `repeat_verified` evidence plus backend acceptance.
- `blocked`, `incomplete`, `negative_baseline_only`, or `adapter_only` may only produce failure memory, human-review/refusal ledger, monitoring items, or negative evals.
- Never use a blocked CAPTCHA run to raise the skill's positive score.
- Never write a blocked managed challenge as "auto passed"; write the blocker, the evidence gap, and the next authorized capture step.

## Validation-to-eval evolution

Fresh validation should evolve the skill library through controlled artifacts:

- If the run is `complete` with verified and repeat-verified backend acceptance, it may feed positive experience memory and later positive evals.
- If the run is `blocked`, `incomplete`, `negative_baseline_only`, or only proves provider test endpoints, it may feed known failures, human-review ledgers, monitoring items, or negative/boundary evals.
- Do not let local demo success, provider config responses, official test tokens, or blocked manual challenges increase positive SKILLS capability.
- After adding or changing an eval, rerun local scoring and the CI gate before claiming the SKILLS library evolved.

## Provider test-key boundary

Official provider test keys, provider config responses, and standalone `siteverify` responses are useful only as boundary evidence, negative controls, or debugging references. They do not prove real visible challenge completion, production token lifecycle, or protected business API acceptance.

Rules:

- Do not add provider test-key tools as positive SKILLS capability.
- Do not write provider endpoint success as `browser_automated_verified`.
- Use provider test-key observations to create negative/boundary evals when an agent tries to overclaim them.
- Continue the real task loop on a public authorized target only when it can produce real site token/state evidence, backend acceptance, and `repeat_verified`.

## Fresh evidence fields

Use the exact fields from `99-SKILLS治理/16-实战复测与证据新鲜度规约.md`:

```yaml
capture_id:
captured_at:
browser_profile_id:
state_reset:
network_log_id:
script_hash:
auth_state:
session_id_hint:
source_freshness:
```

## Failure modes to catch

- Old token reused as fresh token.
- Verified cookie confused with anonymous cookie.
- Browser cache served old script.
- Service worker kept stale response.
- Same HAR replayed after provider changed sitekey/action.
- Single successful verified session generalized to concurrency.
- Captcha challenge classified by UI only, without backend verify endpoint evidence.
- Provider script/config 200 treated as verified success.
- Manual challenge blocker hidden behind a passing score.

## Known failures and test log

Write real failures to `站点经验库/<domain>/known-failures.md` and test lessons to `站点经验库/<domain>/test-log-lessons.md`. CAPTCHA-specific details also go to `验证码经验库/domains/<domain>/captcha-memory.md`.

## Drift policy

Phase 2 local risk-lab update: `run-20260630-013842-high-fidelity-risk-lab` is positive only for self-owned localhost server-side token lifecycle, final business API direct repeat, negative token/session/action/worker evals, and localhost business API worker isolation. It is not third-party CAPTCHA, WAF, managed challenge, stealth, or production fingerprint capability.

Phase 2.1 business-data update: `run-20260630-022227-high-fidelity-risk-lab` is the first positive local evidence that also includes server-side business ledger assertions. Any CAPTCHA/WAF/risk evidence without `business_data_status=DATA_ASSERTION_PASS` remains non-positive, even if challenge/verify endpoints, direct repeat, or worker ladder pass.

Treat provider script hash changes, sitekey/action drift, token field movement, verify endpoint changes, response JSON Pointer drift, cache/service-worker effects, and changed business unlock behavior as drift. Drift must invalidate old mappings until fresh capture revalidates them.

## Delivery gate

Do not claim success unless:

- provider common flow is mapped;
- site binding is mapped;
- verified/unverified API delta is shown;
- `verified` and `repeat_verified` have fresh captures, or the final status is explicitly `blocked`;
- token/state lifecycle is measured or marked unverified;
- old evidence is invalidated or revalidated;
- graph and impact records are updated;
- scope ledger is present, and every reused old capture is explicitly revalidated or marked stale.
- `business_data_status=DATA_ASSERTION_PASS` is present before any positive capability claim.
- server-side business ledger proves final business API data consistency and no negative-eval side effects.
