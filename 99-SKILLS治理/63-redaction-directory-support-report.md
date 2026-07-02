# Redaction Directory Support Report

problem:
- `tools/redact_live_evidence.py authorized-live-tests/reports` failed because the tool treated a directory path as a file path.

root_cause:
- The previous implementation accepted only one path argument and called `Path.read_text()` directly without checking whether the input was a file or directory.

files_changed:
- `tools/redact_live_evidence.py`
- `tools/validate_redaction_tool.py`
- `authorized-live-tests/redaction-fixtures/sample-live-report.json`
- `authorized-live-tests/redaction-fixtures/sample-live-report.md`
- `authorized-live-tests/redaction-fixtures/sample-live-report.yaml`
- `99-SKILLS治理/63-redaction-directory-support-report.md`

commands_run:
- `git branch --show-current`
- `git status --porcelain=v1 -uall`
- `git check-ignore -v authorized-live-tests/authorized-live-targets.local.yaml`
- `python tools\scan_sensitive_evidence.py`
- `python tools\validate_redaction_tool.py`
- `python tools\redact_live_evidence.py authorized-live-tests/redaction-fixtures --dry-run`
- `python tools\redact_live_evidence.py authorized-live-tests/redaction-fixtures --output authorized-live-tests/redaction-fixtures-redacted`
- `python tools\redact_live_evidence.py authorized-live-tests/reports --dry-run`
- `python tools\validate_authorized_live_config.py`
- `python tools\run_authorized_observation.py --config authorized-live-tests/authorized-live-targets.local.yaml --dry-run`
- `python tools\ci_gate.py .ci-out --release`
- `python tools\validate_artifact_references.py`
- `python tools\cleanup_workspace.py --check`
- `python tools\validate_large_artifacts.py`

results:
- File input works.
- Directory input works.
- Dry-run works and does not write output files.
- Explicit output directory writes redacted copies.
- Raw fixture files are not overwritten.
- Binary supported-suffix files are skipped.
- Console summary JSON includes `scanned_files`, `redacted_files`, `skipped_files`, `findings_count`, and `output_dir`.
- `authorized-live-tests/reports --dry-run` no longer treats the directory as a file.
- Authorized observation dry-run reported `network_performed=false`.
- Artifact reference validation passed with `artifact_count=630` and no unreferenced or unknown files.
- Cleanup, sensitive scan, and large artifact scan passed.

redaction_directory_support: PASS

sensitive_scan: PASS

live_execution_performed: NO
