# ast-deobfuscate graph and impact examples

Use these examples when AST work changes the code graph or downstream reverse workflow.

## Example 1: String table recovery exposes sign function

Graph Delta:

```text
node script:https://example.test/static/vendor.1122.js
node module:webpack:431
node js_function:_0x4a3b
node js_function:buildSearchSign
node transform:ast/string-table-recovery
node eval:ast-deobfuscate/string-table-offset

edge script:https://example.test/static/vendor.1122.js -> module:webpack:431 contains
edge transform:ast/string-table-recovery -> js_function:buildSearchSign reveals
edge js_function:buildSearchSign -> js_function:_0x4a3b derived_from
edge js_function:buildSearchSign -> eval:ast-deobfuscate/string-table-offset covered_by
```

Impact Regression:

```text
change: decoded `_0x4a3b` to `buildSearchSign`
impacted:
  - find-crypto-entry mappings that referenced `_0x4a3b`
  - request_field:header.x-sign
  - replay fixture using the old bundle hash
must_run:
  - parse original and final output
  - sample equivalence for buildSearchSign inputs
  - snapshot_diff if request output changes
risk:
  - semantic rename beyond evidence
  - string table offset drift
  - deleted branch with side effects
```

## Example 2: Partial control-flow recovery

Graph Delta:

```text
node transform:ast/control-flow-partial
node unresolved_block:module431/switch-case-7
edge transform:ast/control-flow-partial -> unresolved_block:module431/switch-case-7 incomplete
```

Delivery note:

```text
allowed: mark partial, preserve unresolved block, list missing dynamic trace evidence
invalid_change: flatten guessed switch order or delete unknown branch
```
