# Scope Capability Levels

## Capability Levels

| level | allowed claim | required evidence |
|---|---|---|
| `structure_only` | files, schemas, validators, and docs exist | local file inspection and validator command |
| `local_lab_ready` | self-owned local lab can be validated | local validator pass and machine-readable report |
| `local_lab_positive` | self-owned lab final API is accepted | direct and repeat direct interface acceptance plus business data assertions |
| `authorized_observation_ready` | real-site task pack is ready for authorized collection | observation templates and authorization checklist |
| `authorized_target_candidate` | real target may be tested after authorization | allowed hosts, stop conditions, redaction, and human review gate |
| `positive_allowed` | skill evidence can support positive capability | final business API backend acceptance, repeat direct interface, business data assertions, and no browser dependency |

## Downgrade Rules

- Browser-only evidence is `structure_only` or `browser_assisted_discovery`, never `positive_allowed`.
- CAPTCHA provider challenge success is not business API success.
- Fingerprint diagnostics are observation-only unless a self-owned lab proves business-data closure.
- Localhost concurrency is not production concurrency.
- Missing cleanup ledger, missing validators, or failed validator commands block PASS.

## Impact Record

change_id: standard-loop-2026-07-01
date: 2026-07-01
changed_node: skill routing, pure API gate, CAPTCHA model delivery, fingerprint lab, cleanup gate
changed_edge: entry skill -> tool contract -> validator -> evidence lab
change_type: add
evidence: local file creation and validator commands
direct_impact: routing now separates entry, escalation, internal tool, policy, lab, and observation types
downstream_impact: score and release gates can reject structure-only or browser-dependent claims
required_regression: standard-loop validators, CI gate, verify_delivery
data_validation: machine-readable validation_report.json in labs
drift_risk: future skill additions may omit type taxonomy
rollback: revert standard-loop artifacts and remove new validator references
owner_notes: no real-site capability is promoted by these structural artifacts
