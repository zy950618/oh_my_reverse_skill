## Purpose
Apply AST-based deobfuscation to make authorized JavaScript analysis readable and reproducible.

## Allowed Scope
- String decoding, control-flow cleanup, dead-code pruning, and symbol notes.
- Do not alter runtime semantics without a before-and-after parity check.

## Inputs
- Original JavaScript file and hash.
- Deobfuscation rule set or target transform list.
- Output directory.

## Outputs
- Deobfuscated JavaScript.
- Transform ledger with changed node types and skipped rules.

## Evidence Files
- `deobfuscated.js`
- `transform-ledger.json`
- `parity-notes.md`

## Command Examples
```powershell
npm install @babel/parser @babel/traverse @babel/generator @babel/types
```

## Failure Modes
- Transform changes executable semantics.
- Obfuscation uses runtime-generated code.
- AST parser cannot parse non-standard syntax.

## Retry Strategy
- Disable risky transforms and re-run smaller passes.
- Preserve parser errors with file offsets for manual review.

## Cleanup Rules
- Keep original hash and transformed hash together.
- Remove intermediate debug dumps unless referenced by evidence.

## Acceptance Checks
- Original and transformed file hashes are recorded.
- Any semantic parity check is explicitly passed or marked not verified.

## Related Skills
- `ast-deobfuscate`
- `find-crypto-entry`
- `reverse-js-crawler`
