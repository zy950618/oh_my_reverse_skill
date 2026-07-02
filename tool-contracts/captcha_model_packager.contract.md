## Purpose
Package an accepted local CAPTCHA model with metadata, reproducibility files, and deployment boundaries.

## Allowed Scope
- Local model artifact packaging, registry metadata, and benchmark references.
- Do not package live bypass workflows or unauthorized provider automation.

## Inputs
- Accepted model artifact.
- Model card, metrics, dataset manifest, and license notes.
- Registry destination.

## Outputs
- Packaged model bundle and registry entry.
- Version, checksum, and usage boundary documentation.

## Evidence Files
- `model-package.zip`
- `model-registry-entry.json`
- `checksums.txt`
- `usage-boundaries.md`

## Command Examples
```powershell
python tools/captcha_model_registry.py --register <model_dir> --out <evidence_dir>
```

## Failure Modes
- Bundle misses config or label schema.
- Checksum does not match artifact.
- Usage notes overstate capability.

## Retry Strategy
- Rebuild package from immutable accepted run artifacts.
- Re-check metrics and boundary text before registry update.

## Cleanup Rules
- Remove unpacked staging files after checksum generation.
- Keep only versioned accepted packages in registry evidence.

## Acceptance Checks
- Package can be traced to training config, dataset, and metrics.
- Boundary documentation forbids unsupported third-party claims.

## Related Skills
- `captcha-model-training`
- `captcha-open-source-model-stack`
- `skills-evaluation-governance`
