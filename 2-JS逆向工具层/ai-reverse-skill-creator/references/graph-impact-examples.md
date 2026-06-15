# ai-reverse-skill-creator graph and impact examples

Use these examples when a generated skill changes workflow, evals, or downstream site records.

## Example 1: New crypto-entry skill eval set

Graph Delta:

```text
node skill:find-crypto-entry
node eval:find-crypto-entry/no-evidence
node eval:find-crypto-entry/graph-update
node eval:find-crypto-entry/impact-regression
node delivery_gate:evidence-graph-impact

edge skill:find-crypto-entry -> eval:find-crypto-entry/no-evidence covered_by
edge skill:find-crypto-entry -> eval:find-crypto-entry/graph-update covered_by
edge skill:find-crypto-entry -> eval:find-crypto-entry/impact-regression covered_by
edge skill:find-crypto-entry -> delivery_gate:evidence-graph-impact must_pass
```

Impact Regression:

```text
change: add 7 structured evals and hard delivery gate
impacted:
  - skill trigger behavior
  - score_skills eval count and criteria count
  - CI gate result
  - downstream site memory update requirements
must_run:
  - score_skills.py for the layer
  - tools/ci_gate.py
  - scan for stale boundary-style wording if risk handling changed
risk:
  - placeholder evals counted as coverage
  - name mismatch between folder and frontmatter
  - new gate not referenced by SKILL.md
```

## Example 2: Skill delivery checklist

Generated skills should include this final output contract:

```text
Evidence Map:
Graph Delta:
Impact Regression:
Validation Commands:
Fact Labels:
Scope Ledger:
Open Questions:
```
