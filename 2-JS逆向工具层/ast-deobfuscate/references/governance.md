Version: 0.5.0

# ast-deobfuscate governance

Change log:
- 0.5.0: Added hard delivery gate, structured eval expectations, equivalence validation, graph lineage, impact regression, and anti-overreach evidence checks.

## Workflow

Use this reference when a task asks for deobfuscation, readable code, AST transformation, string-table recovery, control-flow reconstruction, or code cleanup that may affect API fields.

1. Collect evidence: original file path/URL, bundle hash, obfuscation features, AST health report, and target functions.
2. Preserve source files as read-only and write every transform to `intermediate/`.
3. Prefer deterministic AST transforms over manual string replacement.
4. Validate each step with parser checks and sampled function equivalence.
5. Write graph deltas and impact-regression records when function names, module ids, crypto entries, or request fields change.

## Hard delivery gate

Every final output must include:

- Evidence Map: original source, transform script, intermediate files, final output, and sampled equivalence evidence.
- Graph Delta: changed script/module/function nodes and edges to request fields or evals.
- Impact Regression: downstream entry-finding, replay, schema, fixtures, and eval checks.
- Validation Commands: parse check, transform run, sample equivalence, replay/diff if API behavior is touched.
- Fact Labels: observed, derived, assumed, unverified.
- Scope Ledger: source files changed, unknown branches preserved, replay claims excluded unless separately verified, and unresolved blockers.

## Known failures

- Semantic rename hallucination: renaming variables from guessed meaning instead of deterministic patterns.
- Dead-code deletion bug: removing a branch that has side effects hidden behind computed conditions.
- Offset drift: a string-table offset changed after rotation but the old decoder index remained hardcoded.
- Pretty-print false success: minified code was formatted but not actually deobfuscated.
- Missing impact record: recovered function name changed, but crypto-entry graph still points to the old obfuscated symbol.

## Drift policy

Treat bundle hash change, parser failure, transform mismatch, output mismatch, new obfuscation prefix, string-table layout change, and control-flow shape change as drift.

## Site memory

When deobfuscation affects endpoint fields or generators, update `站点经验库/<domain>/knowledge-graph.md` and `站点经验库/<domain>/impact-regression.md`. Do not keep transform-only facts outside site memory.
