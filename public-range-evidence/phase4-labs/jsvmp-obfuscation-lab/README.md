# JSVMP / Obfuscation Lab

This Phase 4 lab is a local synthetic evidence package. It documents solver/parity/drift behavior without live-site credentials or production traffic.

## Files

- `manifest.json`
- `negative_cases.json`
- `validation_report.json`
- `reports/replay_or_trace_report.md`

## Coverage

- string array obfuscation
- control flow flattening
- dead code
- virtual dispatch mock
- dynamic function call
- anti-debug signal mock
- AST deobfuscation report
- runtime trace report
- pure solver output

## Validation

- `tools/validate_jsvmp_obfuscation_lab.py`
