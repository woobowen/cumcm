# Architecture

## Shape

One discoverable `cumcm-modeling-evidence` Skill routes the lifecycle. Normative documents/rules/contracts define permitted behavior; runtime state and append-only ledgers record execution; generated reports render state without becoming authority. The main agent writes formal state. Read-only reviewers challenge requirements, sources, data, assumptions, code, experiments, and reproducibility.

Third-party repositories are untrusted research inputs stored only under ignored `.cache/upstream/<id>/`. Their identity, license, structure, claims, risks, and evidence paths are recorded in the repository, but their code and Skill text are neither executed nor copied during foundation.

## Data flow

```text
immutable problem/data -> requirement trace -> registered sources/data audit
-> formalization/baseline -> candidate tournament -> verified implementation
-> registered experiments/runs -> validation/robustness -> frozen Final Run
-> schema-valid Evidence Package -> separate paper team
```

Every formal edge carries identifiers/hashes. A changed upstream dependency propagates `STALE` to descendants according to `WORKFLOW.md`.

## Automated adjudication plane

Phase 002A freezes evidence and policy, classifies eligibility, separates coverage from oracle and
process evidence, runs identity-blind Judges plus independent Dissent, converts serious claims to
tests, applies lexicographic Meta-Adjudication, and requires a Decision Auditor. Only the main
orchestrator writes formal state from an audited record. Human compliance review is separate and
cannot change the technical outcome.

## Evaluation isolation

Development cases may inform changes. Validation freezes the Skill during a run. Held-out cases and answers live in an excluded vault; viewing an answer permanently demotes that case to development. Live contest mode forbids current-problem discussion searches. Static scores are provisional and never choose a base without dynamic evidence.

## Evidence-expansion execution plane

Phase 002D uses a frozen cohort, blocked randomized schedule and fresh ephemeral no-remote Git
workspaces. Append-only attempt/run/eligibility/oracle/process records feed a deterministic
sufficiency Gate. Semantic Subagents and automated decisions are downstream consumers only when
that Gate is sufficient; the terminal insufficient route writes no substitute opinion.

## Why not concatenate full Skills

Full-Skill concatenation creates duplicate state machines, contradictory gates, discovery collisions, instruction-budget pressure, uncertain license boundaries, and untraceable behavior. The project instead evaluates mechanisms, then adopts/ports/reimplements only evidence-backed components through explicit ADRs, license review, and tests.
