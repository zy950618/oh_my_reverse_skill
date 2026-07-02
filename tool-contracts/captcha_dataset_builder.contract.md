## Purpose
Build authorized or synthetic CAPTCHA datasets with labels, provenance, splits, and leakage checks.

## Allowed Scope
- Local lab, public allowed targets, or explicitly authorized samples.
- Do not collect third-party protected data outside approved scope.

## Inputs
- Dataset source plan and authorization notes.
- Label schema and split strategy.
- Output dataset directory.

## Outputs
- Dataset manifest, labels, splits, and provenance report.
- Leakage and duplicate checks when applicable.

## Evidence Files
- `dataset-manifest.json`
- `labels.jsonl`
- `splits.json`
- `provenance.md`
- `leakage-audit.json`

## Command Examples
```powershell
python tools/captcha_dataset_builder.py --config <config> --out <dataset_dir>
```

## Failure Modes
- Labels are inconsistent or unverifiable.
- Dataset includes leaked answers or duplicate train/test samples.
- Source scope is missing or ambiguous.

## Retry Strategy
- Rebuild splits after fixing provenance or label defects.
- Quarantine questionable samples instead of silently dropping evidence.

## Cleanup Rules
- Remove temporary downloads not listed in the manifest.
- Keep failure samples only with provenance and redaction.

## Acceptance Checks
- Manifest links every sample to source, label, and split.
- Leakage audit passes or records explicit blockers.

## Related Skills
- `captcha-image-dataset-governance`
- `captcha-dataset-flywheel`
- `captcha-model-training`
