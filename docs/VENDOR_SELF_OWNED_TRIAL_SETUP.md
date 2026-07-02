# Vendor Self-Owned Trial Setup

Source run_id: `run-20260630-163000-phase3-10-realism-hardening`

This document defines the minimum private configuration required before Codex can run an official Shumei or Aliyun self-owned trial. Compatible labs cannot substitute for official trials.

## Shumei Trial

Required local config path:

- `configs/private/vendor_trial.shumei.json`

Required fields:

- `organization_id`
- `app_id`
- `scene_id`
- `test_domain`
- `allowed_host`
- `server_verify_endpoint`
- `rate_limit`
- `stop_condition`
- `evidence_redaction`

Rules:

- The config must stay outside source control.
- The trial must use a self-owned test domain or explicitly authorized host.
- Server verify must be performed by a controlled backend endpoint.
- Business success requires final business API and ledger assertions.
- Missing config must be reported as `BLOCKED`; fake credentials are prohibited.

## Aliyun CAPTCHA 2.0 Trial

Required local config path:

- `configs/private/vendor_trial.aliyun.json`

Required fields:

- `scene_id`
- `captcha_config`
- `test_domain`
- `allowed_host`
- `client_integration`
- `server_verify_endpoint`
- `business_data_assertions`
- `evidence_redaction`

Rules:

- AccessKey, AccessKeySecret, tokens, and passwords must never be committed.
- Client integration must be tied to a self-owned scene/captcha config.
- Server verify must be performed by an owned backend.
- `no_trace` or one-click flows are state-machine diagnostics unless final business data assertions pass.
- Missing config must be reported as `BLOCKED`; compatible labs must not be used as official trial evidence.

## Adapter Command

```powershell
python tools/vendor_trial_adapter.py --target shumei --run-id <run_id>
python tools/vendor_trial_adapter.py --target aliyun --run-id <run_id>
```

If the private config is missing, the adapter must output:

- `status=BLOCKED`
- `missing_self_owned_credentials`
- `missing_scene_id`
- `missing_allowed_host`
- `next_required_user_input`
- `no_fake_credentials_used=true`

## Promotion Boundary

Official vendor trial evidence can only become `positive_candidate` after provider diagnostics, state observer, server verify flow, business data assertions, negative eval, evidence redaction, scope contract, and capability promotion gates pass for the same run_id.
