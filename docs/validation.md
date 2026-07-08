# Validation

Current local gate set uses stable top-level wrappers under `tools/`; implementations are grouped under `tools/governance/`, `tools/validators/`, and related subdirectories.

```bash
python3 tools/validators/validate_structure.py
python3 tools/validators/validate_links.py
python3 tools/validators/validate_routing.py
python3 tools/evidence/validate_evidence_policy.py
python3 tools/governance/score_skills.py --repo .
python3 tools/governance/ci_gate.py .ci-out
python3 tools/governance/ci_gate.py .ci-out --release
python3 tools/lifecycle/cleanup_workspace.py --check
```

Release passing does not convert structure-only evidence into real-site success. Capability claims still require scope, direct interface repeat, and business-data assertions where applicable.
