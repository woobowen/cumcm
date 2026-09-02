# Failure-aware evidence policy

Phase 002D-R1 treats every frozen attempt as an observed categorical outcome. Exactly one primary
classification is assigned from authoritative completion, Schema, oracle, process, runner,
transport and harness evidence; secondary flags preserve mixed causes. Failure is never converted
to a numeric zero, silently discarded, or replaced by a later attempt.

Quality, reliability, outcome completeness and component gaps are separate scopes. Quality uses
only the earliest oracle-passing eligible record in each slot. Reliability retains all attempts and
costs. Terminal negatives resolve outcome completeness and may support repeated gap descriptions,
but cannot fill the quality Gate. Infrastructure, harness and unknown censoring do not rank an arm.
Recovery-affected evidence is gap evidence only. Identity, Agent votes and human technical approval
are prohibited inputs.

The machine truth is `evals/results/phase-002d-r1/`; its input freeze binds immutable Phase
002–002D evidence. Any changed historical input makes dependent R1 artifacts `STALE`.
