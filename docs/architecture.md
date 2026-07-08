# Architecture

Source of truth for repository shape.

- Public entry docs: `README.md`, `USAGE.md`, `TRIGGERS.md`, `INSTALL.md`, `AGENTS.md`, `CLAUDE.md`, `00-SKILLS索引.md`.
- Active skill roots: `1-业务流程层/`, `2-JS逆向工具层/`, `4-通用规范层/`, `5-沉淀工具层/`, `7-指纹风控层/`.
- Governance rules: `99-SKILLS治理/`.
- Evidence and local labs: `public-range-evidence/`.
- Utility scripts: `tools/` stable wrappers plus grouped implementations under `tools/governance/`, `tools/validators/`, `tools/evidence/`, `tools/web_h5/`, `tools/js_runtime/`, `tools/fingerprint/`, `tools/site_memory/`, and `tools/lifecycle/`.

Active skill count and score are generated, not handwritten. Use `python3 tools/score_skills.py --repo .`.
