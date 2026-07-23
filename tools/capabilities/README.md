# Capability Matrix generator

This directory owns the repository's sole Capability Matrix generator. Its
finite catalog is `schema.yaml`; discovery cannot add capability IDs. Each
producer, consumer, test, documentation, and external-dependency item is
validated independently, including its repository path, exact byte SHA-256,
and a symbol or consumer command proven present in those exact bytes.

This is shared evidence infrastructure only. It does not claim that an active
Skill consumes the generator, that an external dependency is a native
implementation, or that any real site or external service succeeded.

## Generate and validate

```bash
python3 -B tools/capabilities/capability_matrix.py --schema tools/capabilities/schema.yaml --repo-root .
python3 -B -m unittest discover -s tools/capabilities/tests -p "test_*.py" -v
```

The command always writes deterministic JSON and Markdown reports. It exits
non-zero after writing diagnostics when evidence, command paths, wrappers, or
legacy dispositions have a hard finding. Documentation examples containing
placeholders remain visible in the command inventory but do not count as
executable capability evidence.

## Evidence boundary

- `producer` requires a repository script and an entrypoint found in its source.
- `consumer` requires the exact command in a hashed caller or workflow; a name
  mention is insufficient.
- `test` requires an automated test file and a test symbol found in its source.
- `external_dependency` requires source plus version or an explicit unlocked
  marker, uses a null hash, and never upgrades I or T.
- `documentation` can set only D. Missing or contradictory evidence sets U and
  never receives an optimistic default.

The report separately emits `integration_status`. Only a capability with valid
producer, consumer, and test bindings is `INTEGRATED`; producer plus test without
a consumer is `IMPLEMENTED_TESTED_UNCONSUMED`.

Legacy entries, when introduced, must declare exactly one disposition:
`compatible_wrapper` or `unified_migration`. The generator reports rather than
rewrites old documents.
