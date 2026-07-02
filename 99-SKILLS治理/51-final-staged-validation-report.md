# Final Staged Validation Report

status: STAGED_VALIDATION_PASS

generated_at: 2026-07-02T01:12:48.229573+00:00

commit_performed: NO

push_performed: NO

## Groups

| group | files | status | validators |
|---|---:|---|---|
| group 1: routing and governance reports | 66 | PASS | common staged gates, ci_gate, ci_gate --release, verify_delivery --domain none |
| group 2: tool contracts and pure API gates | 81 | PASS | common staged gates, pure-api-lab, airline pure API, ci_gate --release |
| group 3: CAPTCHA model delivery lab and validators | 824 | PASS | common staged gates, sample_infer, evaluate_pass_rate, CAPTCHA schema/dataset/training/package/pass-rate, ci_gate --release |
| group 4: fingerprint risk lab and validators | 53 | PASS | common staged gates, fingerprint surface, block reason, context isolation, captcha linkage, ci_gate --release |
| group 5: airline lab and real-site observation packs | 109 | PASS | common staged gates, real-site observation pack, airline replay/tests/pure API, ci_gate --release |
| group 6: release gate, artifact reference, cleanup tools | 131 | PASS | common staged gates, ci_gate, ci_gate --release, artifact reference, cleanup, staged sensitive, staged large artifacts |

## Security

staged_secret_count: 0

staged_cookie_count: 0

staged_token_count: 0

staged_har_count: 0

staged_profile_count: 0

## Large Artifacts

staged_large_files: 5

staged_gt_5mb_files: 0

staged_model_files: 0

staged_dataset_files: 0

staged_manual_review: 0

## Validation

cached_file_count: 1264

release_gate: PASS

artifact_reference: PASS artifact_count=533 unreferenced=0 unknown=0

cleanup: PASS candidate_count=0 remaining=0 unclassified=0

staged_sensitive_scan: PASS scanned=1264

staged_large_artifact_scan: PASS scanned=1264

## Excluded From Stage

- `public-range-labs/vendor/OpenCaptchaWorld/` OBSERVED embedded Git repository; ignored to avoid accidental gitlink.
- `public-range-labs/vendor/go-captcha-example/` OBSERVED embedded Git repository; ignored to avoid accidental gitlink.
- `public-range-labs/vendor/go-captcha-service/` OBSERVED embedded Git repository; ignored to avoid accidental gitlink.

## Notes

- OBSERVED: Git emitted LF-to-CRLF warnings while staging existing text files.
- VERIFIED: no `git add .`, `git add -A`, or `git add *` was used.
- VERIFIED: no commit or push was performed.
- NOT VERIFIED: live third-party execution; real-site observation validator reports `NOT_RUN_NO_AUTHORIZATION_INPUT` for live observation.
