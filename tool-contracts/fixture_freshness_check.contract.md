# Fixture Freshness Check Contract

## Boundary

`tools/replayer/validate_fixtures.py` and
`tools/web_h5/fixture_freshness_report.py` are stdlib-only compatibility entries
over one `FixtureGateResult` engine. The result proves only the stated fixture
structure/freshness checks. It never proves a network replay, current target,
adapter/business success, real execution, consistency, or release readiness.
Freshness modes therefore emit `replay_lineage: UNKNOWN`; offline emits
`NOT_CHECKED`.

## Modes

| Mode | Freshness | Positive capability | No data | Stale |
|---|---|---|---|---|
| `offline` | no | `STRUCTURE_ONLY` | `NO_DATA/0` | not checked |
| `diagnostic` | yes | `DIAGNOSTIC_ONLY` | `NO_DATA/0` | `STALE/0` |
| `strict` | yes | `FRESH_FIXTURE_GATE` | `NO_DATA/4` | `STALE/3` |
| `refresh` | yes | `REFRESH_NOT_REQUIRED` or `REFRESH_PLAN` | `RECERTIFICATION_REQUIRED/3` | `RECERTIFICATION_REQUIRED/3` |

`strict`, `--strict-review`, and `--strict-fresh` imply require-data.
`--require-data` makes offline/diagnostic no-data exit 4. Structure,
argument, and handled internal failures are respectively
`STRUCTURE_INVALID/1`, `INVALID_ARGUMENT/2`, and `INTERNAL_ERROR/5`.
Refresh produces only closed-enum tasks and never captures or replays data.

## Physical selection and reads

The engine imports and uses the shared LL-0001 `select_fixture_layout` selector:
`fixtures/active` wins only when `Path.is_dir()` is true; otherwise legacy
`fixtures` is selected. There is no local precedence override. Selected roots,
snapshots, reports, and consumed artifacts fail closed on symlinks or escape.
`historical` and `_archive` never participate.

A physical domain is NFC, strict UTF-8, 1..253 UTF-8 bytes, neither `.` nor
`..`, has no leading `_` or `.`, no trailing `.`, no `..`, labels do not start
or end `-`, and every non `-`/`.` code point has Unicode category L, N, or M.
Filtered domains are safe, sorted, deduplicated direct lookups and never cause
sibling enumeration. Missing/non-directory filtered domains produce zero-count
DomainResults plus `DOMAIN_MISSING`/`DOMAIN_NOT_DIRECTORY`. Unfiltered discovery
examines fixture-bearing entries only; an unsafe fixture-bearing name produces
only `UNSAFE_DOMAIN` with `domain-sha256-` plus the first 16 hex digits of
SHA-256 over `os.fsencode(name)`, never a replay domain.

## Fixture and report profiles

Every complete prefix has request/response JSON objects and metadata. Metadata
is a unique-key YAML subset with exact required scalar fields `endpoint`,
`recorded_at`, `captured_at`, `expires_at`, `sensitive`, `requires_auth`,
`source`, `schema_version`, and `review_status`; `schema_version` is
`fixture-meta-v2`; booleans are unquoted `true|false` literals and `expires_at`
is always a scalar; optional `category` must be one of
`public-read,search,detail,list,session,config`. Optional `volatile_fields` is a
list, optional `tolerance` a map, and optional `notes` is an exact `|` block.
Duplicate/unbalanced/malformed scalar or container syntax fails closed.

Strict freshness requires a timezone-aware future expiry and no TODO,
auto-extracted, review/edit, or pending marker anywhere in normalized metadata;
`review_status` is `reviewed`. Offline requires the `expires_at` key but ignores
its scalar and emits no expiry/review issues or counters.

The authoritative report is the lexically newest valid
`YYYY-MM-DD-replay.md` filename date at UTC day start. Filesystem mtime is never
used. Future or older-than-window dates are stale. The authoritative file must
validate; there is no fallback to an older file. Exactly one producer profile
is accepted:

- bare profile: exact unindented unique `status`, optional finite
  `consistency_rate`, `total`, `replayed`, and `source` lines, with PASS,
  positive integer `replayed == total == complete_triplets`, and nonempty source;
- canonical profile: one `## Canonical Result` and one JSON fence containing the
  exact 18-field protected `ConsistencyResult`; it must be PASS/0, positive
  equal total/selected/replayed/compared, zero fatal/mismatch counts, valid
  finite rate/threshold/count equations, null failure kind,
  `report_artifact == reports/<filename>`, and
  `trend_artifact == reports/trend.json`.

Bare recognized fields are detected independently of canonical markers. Any
canonical document containing even a partial bare-profile claim is malformed.

The selected report path is exactly one file directly under the bound selected
root's reports directory.

## Exact result and validator

Canonical JSON uses UTF-8, `ensure_ascii=false`, `allow_nan=false`, compact
separators, fixed key order, and sorted unique arrays. Top-level fields are
exactly:

```text
schema_version,tool,mode,status,exit_code,capability,no_data,
freshness_checked,replay_lineage,totals,domains,issues,refresh_tasks,artifact
```

Totals are exactly:

```text
domains_selected,domains_with_snapshots,request_files,response_files,
metadata_files,complete_triplets,valid_triplets,expired_count,
review_pending_count,missing_expiry_count,structure_issue_count,
freshness_issue_count,refresh_task_count
```

All schema, exit, totals/domain, and selected-report count values are actual
non-boolean integers. Domain, report, issue, task, artifact schemas, enums,
nullable fields, reason scopes, task mappings, aggregation equations,
mode-aware valid-triplet predicate, no-data cardinality, terminal mapping, and
producer tool binding are recomputed by the total shared validator. A selected
domain with `NO_COMPLETE_TRIPLETS` prevents every positive capability even when
another domain contributes triplets. Domain,
layout, selected-root suffix and report-parent bindings are exact. Repository
paths are nonempty relative POSIX paths without absolute/drive/backslash,
empty, `.`, `..`, or normalization-changing components.

Before-scan INVALID_ARGUMENT and zero-evidence INTERNAL_ERROR contain zero
totals, `no_data=false`, no domains, and their sole root issue. Scan exceptions
retain only prior fully completed domains and recompute all retained evidence.
Process exit equals result exit.

## CLI and workflow compatibility

Both legacy root positionals and default `站点经验库` remain. Relative roots are
resolved from CWD. `--recent-days` is positive, `--out` is refresh-only,
abbreviations are disabled, aliases combine only with explicit strict mode, an
invalid raw mode occurrence anywhere forces diagnostic-mode INVALID_ARGUMENT,
and an explicitly empty `--out=` is invalid. The strict workflow supplies its
expected site root so selected roots bind to the unique repository/domain/shared
selector path. Offline validation rejects every freshness reason, report,
non-`not_checked` source, or nonzero freshness/expiry/review counter. Both
wrappers' stdout is UTF-8. CLI parse/help/unsafe-domain/mode failures return one
canonical INVALID_ARGUMENT JSON plus stderr detail. Core callers must pass a fixed tool
and `Mode` enum or receive `ValueError`.

CI captures strict gate stdout and exit, rejects duplicate JSON keys and
NaN/Infinity, validates with `expected_tool=validate_fixtures`, and requires
positive `PASS/0/FRESH_FIXTURE_GATE` before strict discovery. Discovery repeats
the same validator/tool/root/domain bindings and shared selector. The protected
LL-0002 two-argument discovery path separately preserves successful `[]`.
ReplayResult handoff/mapping/result/continuation and LL-0003 ConsistencyResult
semantics are unchanged.

## Refresh publication protocol

Output is a strict repository descendant whose entire parent chain already
exists. POSIX directory-fd, no-follow, stat, rename, unlink, file-fsync, and
descriptor primitives are mandatory; there is no fallback. Before staging, an
external temporary directory on the trusted-root device performs a same-parent
regular-file-to-existing-directory rename probe. Only EISDIR/ENOTDIR plus exact
source/destination identities, types, source bytes, and namespace nonmutation
admits publication; otherwise publication stops before staging.

The engine prepares the result, canonical committed bytes, digest, artifact
path, and returned result before mutation. Committed bytes are exactly the
semantic result with `artifact:null`, compact canonical JSON, and one LF;
SHA-256 covers exactly those bytes. The returned result differs only by its
non-null `{path,sha256}` artifact. This internal prepared-claim consistency
check is precommit validation only; it is not historical invocation proof.

Publication pins the repository root and each existing output ancestor by
directory fd, validates device/inode identities, records existing regular
target identity or absence, creates one same-parent invocation-owned temp with
`O_EXCL|O_NOFOLLOW`, transfers every raw fd to at most one owner, writes,
flushes, file-fsyncs, closes, reopens and verifies exact bytes and inode, then
performs final chain/target/temp validation. All operations capable of producing
handled INTERNAL_ERROR/artifact-null complete before commit.

One same-parent `os.rename(source,target,src_dir_fd=parent,dst_dir_fd=parent)`
normal return is the sole commit/linearization point. There is no backup,
rollback, directory fsync, namespace cleanup, path stat, or result-affecting
fallible operation after it. If a synthetic post-commit close raises before
closing its exact owned fd, a one-fd stdlib fallback closes it; every remaining
descriptor close is still attempted. Close exceptions never reclassify the
committed result, and the prepared artifact result returns.
EINTR/EIO from the production rename is an unhandled STOP: no retry and no
canonical result.

Before commit, any handled failure preserves exact prior target bytes or
absence, verifies and unlinks only the owned temp, independently closes every
raw/file/directory fd exactly once, and returns rerunnable INTERNAL_ERROR with
artifact null. Ambiguous precommit close or persistent/identity-unsafe cleanup
is STOP. Ancestor replacement cannot redirect retained directory-fd mutation;
successful rename remains committed even if an ancestor or target pathname is
replaced immediately afterward. The exhaustive deterministic tests cover
existing/absent targets, parent/grandparent races, every staging/ownership/
write/flush/fsync/verify/final-validation/rename/cleanup/close boundary,
outside-path nonmutation, stable fd inventory, and rerun behavior.

The shared exact validator fail-closes every non-null artifact unless a trusted
`expected_out` is supplied by the caller. With trusted context, validation
binds only the normalized repository-relative path, SHA-256, regular
non-symlink target, and exact canonical `artifact:null` bytes currently stored
at that target. This proves current trusted-target byte equality only, not
historical invocation identity or exclusive authorship.

Atomic visibility and pre-rename file fsync are guaranteed; directory-entry
crash durability, SIGKILL/power loss, arbitrary cross-root moves of pinned
directories, and crash-residue reclamation are explicit non-goals/STOP cases.
