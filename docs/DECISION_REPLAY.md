# Decision replay

A replay uses only frozen evidence, frozen policy, tracked structured Agent outputs, executed test
evidence, and the decision input record. Canonical JSON hashing excludes no substantive field. Key
order changes preserve hashes; candidate identity/order transformations must preserve the decision.
Any policy, evidence, Judge, Dissent, or test mutation marks Meta, Audit, decision, state, and reports
`STALE`.

`scripts/replay_automated_decision.py --check` verifies recorded hashes without network access. A
missing decision is an error, not an implicit rejection or abstention. Reports consume decision
records and cannot manufacture a replay result.

Recovery checkpoints and failure diagnostics are not decision inputs. A transport-incomplete chain
has no replayable decision: `--check` must fail with the missing-prerequisite error and state/report
must record replay as `NOT_RUN`. Adapter choice, retry order, or unused global budget cannot be
replayed into a technical conclusion.
