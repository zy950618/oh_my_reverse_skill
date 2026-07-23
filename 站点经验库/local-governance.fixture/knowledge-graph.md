# local-governance.fixture Knowledge Graph

## Delivery State

```yaml
domain: local-governance.fixture
last_run_id: LL-0004-R7
delivery_status: unverified
verification_mode: not_applicable
skills_participation: negative_eval_only
completed_confirmations:
  - fixture-gate-engine structure, freshness, and current-target contextual artifact binding have local automated evidence
incomplete_confirmations:
  - current target lineage is still UNKNOWN outside trusted expected_out byte equality
  - no endpoint, network replay, real-site, production capability, or historical invocation identity is confirmed
next_skip_paths:
  - do not infer historical invocation proof, current-target lineage, or real-execution evidence from artifact presence, report names, or source labels
```

## Nodes

| Node ID | Type | Scope | Status | Evidence | Notes |
|---|---|---|---|---|---|
| fixture-gate-engine | implementation | local-governance.fixture | derived | `tools/replayer/fixture_gate.py` | stdlib structure/freshness engine only |
| fixture-gate-cli | implementation | local-governance.fixture | derived | `tools/replayer/validate_fixtures.py`; `tools/web_h5/fixture_freshness_report.py` | compatibility producers |
| fixture-gate-workflow-consumer | implementation | local-governance.fixture | derived | `.github/workflows/consistency-replay.yml` | exact strict producer/schema/domain binding |
| fixture-gate-r7-eval | eval | local-governance.fixture | derived | `tools/replayer/tests/test_replayer_tools.py` | unpublished-forgery and contextual publication matrices |
| current-target-contextual-bytes | state | local-governance.fixture | derived | `tool-contracts/fixture_freshness_check.contract.md` | trusted expected_out can prove only current path/digest/byte equality |
| historical-invocation-identity | state | local-governance.fixture | unverified | `tool-contracts/fixture_freshness_check.contract.md` | explicitly out of scope for revision 6 |

## Edges

| From | Relation | To | Status | Evidence | Regression |
|---|---|---|---|---|---|
| fixture-gate-cli | implementation->endpoint | fixture-gate-engine | derived | shared `run_gate` entry | unit and CLI gates |
| fixture-gate-workflow-consumer | implementation->endpoint | fixture-gate-engine | derived | shared exact validator and selector | actual workflow shell-block tests |
| fixture-gate-r7-eval | eval->node | fixture-gate-engine | derived | named F014 contextual and forged unpublished tests | full replayer suite |
| fixture-gate-engine | implementation->endpoint | current-target-contextual-bytes | derived | trusted expected_out byte/path/digest verifier | no historical invocation claim permitted |
| fixture-gate-engine | implementation->endpoint | historical-invocation-identity | unverified | explicit contract boundary | future nonce/challenge required before any positive proof claim |

## Scope Rule

These implementation/eval nodes are governance evidence only. They do not add
a real endpoint node or upgrade `skills_participation` to `positive_allowed`.
