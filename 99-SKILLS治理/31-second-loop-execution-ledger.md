# Second LOOP Execution Ledger

## Failed Gate Observations

OBSERVED: First release attempt failed because generic public-range validators scanned dedicated lab artifacts and because CAPTCHA validators required positional arguments.

OBSERVED: A later release attempt failed because `validate_real_execution_proof.py` could not resolve old absolute evidence paths from `E:\SKILLS\oh_my_reverse_skill` to the current local project root.

OBSERVED: Another release attempt failed because `validate_scope_contract.py` scanned internal/list JSON artifacts as evidence objects.

OBSERVED: Final pre-pass failure was `cleanup_check` with one generated `tools/__pycache__` candidate.

## Fix Ledger

- Added default no-argument paths to CAPTCHA validators while preserving explicit positional-argument behavior.
- Scoped generic public-range, real-execution, business-data, and scope-contract scans away from dedicated second-loop lab roots already covered by their own validators.
- Added old-root and cleanup-archive path resolution for real-execution and business-data evidence checks.
- Added second-loop release subchecks to `tools/ci_gate.py --release`.
- Disabled bytecode writing in `tools/ci_gate.py` and subprocesses so the release gate does not create its own cleanup candidate.
- Added CAPTCHA root-level delivery files and sample image/label aliases.
- Added/validated real-site observation pack schema, sample fixture, runbook, and authorization input files for 7 airline targets.
- Added airline deep validation runner and report with 13 passing cases.

## Commands Actually Run

VERIFIED:

- `python tools/ci_gate.py .ci-out`: PASS, 25 active skills passed default structure gate.
- `python tools/ci_gate.py .ci-out --release`: PASS, release gate and second-loop subchecks passed.
- `python tools/verify_delivery.py --domain none`: exit 0, score output `7/10`, honesty boundary must be enforced in final answer.
- `python tools/fixture_freshness_report.py 站点经验库`: PASS.
- `python tools/validate_web_h5_crawler_gate.py`: PASS.
- `python tools/validate_web_h5_loop_gate.py`: PASS.
- `python tools/validate_web_h5_real_execution_gate.py`: PASS.
- `python tools/validate_pure_api_delivery.py public-range-evidence/pure-api-lab`: PASS.
- `python tools/validate_pure_api_delivery.py public-range-evidence/airline-lab-order-flow`: PASS.
- `python tools/validate_captcha_action_schema.py`: PASS.
- `python tools/validate_captcha_dataset.py`: PASS.
- `python tools/validate_captcha_training_report.py`: PASS.
- `python tools/validate_captcha_model_package.py`: PASS.
- `python tools/validate_captcha_pass_rate.py`: PASS.
- `python public-range-evidence/captcha-model-lab/inference/sample_infer.py`: PASS, 3 predictions.
- `python public-range-evidence/captcha-model-lab/eval/evaluate_pass_rate.py`: PASS, 3 attempts / 3 passes.
- `python tools/validate_fingerprint_surface_lab.py`: PASS.
- `python tools/validate_block_reason_lab.py`: PASS.
- `python tools/validate_browser_context_isolation.py`: PASS.
- `python tools/validate_captcha_fingerprint_linkage.py`: PASS, 7 packs.
- `python tools/validate_real_site_observation_pack.py public-range-evidence/real-site-observation-pack`: PASS, 7 targets.
- `python public-range-evidence/airline-lab-order-flow/replay/replay.py`: PASS.
- `python public-range-evidence/airline-lab-order-flow/tests/run_order_flow_tests.py`: PASS, 13 cases.
- `python tools/cleanup_workspace.py --plan`: PASS.
- `python tools/cleanup_workspace.py --apply`: PASS.
- `python tools/cleanup_workspace.py --check`: PASS, candidate_count 0.

## Remaining Boundary

NOT VERIFIED: live airline production execution, live third-party CAPTCHA success, live WAF bypass, production fingerprint evasion, and remote repository state.
