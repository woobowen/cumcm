# RC6 requirement evidence and selection design

Status: `FROZEN_FOR_IMPLEMENTATION`
Phase: `PHASE-SKILL-C-TARGET-EVIDENCE-REPAIR-004C3`
Architecture: `ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL`

## Problem and design boundary

RC5 is historically frozen but release-blocked because its Skill `VERSION` is RC4 while the
runner, `SKILL.md`, and manifest identify RC5. The 2019 C terminal evidence also exposes two
case-neutral failures: empirical requirements can reach expensive execution with simulation-only
inputs, and a global selection can bind a policy Claim to a baseline Run that never executes the
policy. RC6 repairs those defects in the existing centralized runner. It does not create another
Skill, architecture, state source, model role, or natural-language theorem prover.

The 2024 and 2019 Validation verdicts, Runs, Claims, handoffs, and freezes are immutable. Successor
diagnostics consume hash-bound frozen artifacts and never write into their case workspaces. The
2025 C reservation remains `SEALED_NOT_ACCESSED` with all six access flags false.

## Contracts and decision order

New RC6 cases use four compatible structured views:

1. `requirement-evidence/v1` declares each primary requirement's required/allowed evidence classes,
   minimum fields, time/entity scopes, acquisition and substitution policy, dependencies, and
   completion rule. Each source declares evidence class, provenance, authority, retrieval/licence,
   scopes, schema, hash, freshness, and limitations.
2. `data-sufficiency/v1` runs after `DATA_AUDIT` and before expensive modeling. Each requirement is
   `SUFFICIENT`, `ACQUISITION_REQUIRED`, `PARTIAL`, `UNSATISFIABLE_WITH_CURRENT_INPUTS`, or `UNKNOWN`.
   Unknown never passes. Acquisition-required work must bind a source plan and rerun the Gate.
3. `requirement-selection/v1` selects `GLOBAL_JOINT`, `PER_REQUIREMENT`, or `JOINT_PORTFOLIO`.
   Selection binds requirement-specific metrics, Runs and outputs. A portfolio additionally proves
   shared inputs/scenarios and constraint compatibility.
4. `claim-evidence/v3` retains v2 lineage and aggregate coverage while adding claim type, evidence
   class, Run/output/metric/comparator IDs, structured predicates, uncertainty, counter-evidence,
   limitations, strength, and status. Legacy v1/v2 are read through deterministic derived views;
   historical artifacts are never rewritten.

The Gate order is:

`DATA_AUDIT -> DATA_SUFFICIENCY_PREFLIGHT -> acquisition/recheck when allowed -> EXPERIMENT_DESIGN
-> execution -> requirement/portfolio selection -> semantic Claim predicates -> aggregate handoff`.

An independently satisfiable requirement may continue after another requirement becomes partial or
unsatisfiable, but the aggregate result cannot claim complete primary coverage. Fail-closed reason
codes are stable machine outputs, not prose explanations.

## Evidence semantics

The evidence enum is `PROVIDED_EMPIRICAL`, `ACQUIRED_EMPIRICAL`, `DERIVED_EMPIRICAL`, `SIMULATION`,
`THEORETICAL`, `ASSUMPTION`, `EXPERT_JUDGMENT`, and `UNKNOWN`. Simulation and assumptions can support
only bounded conditional Claims, never empirical conclusions. Scope compatibility is conjunctive
over fields, time, entities, provenance, licence/use status, and freshness.

Claim types are `DESCRIPTIVE`, `EMPIRICAL`, `PREDICTIVE`, `COMPARATIVE`, `POLICY_EVALUATION`,
`FEASIBILITY`, `OPTIMALITY`, `CAUSAL`, and `SIMULATION_CONDITIONAL`. Their predicates are deliberately
bounded: empirical provenance, comparable inputs/metrics, policy execution and nonzero exposure,
comparator, benefit/cost, independent feasibility recomputation, global optimality certificate,
causal identification, predictive holdout, scope bounds, and counter-evidence disposition. Failed
predicates reject or downgrade a Claim; they do not attempt arbitrary natural-language entailment.

## Selection semantics

`GLOBAL_JOINT` is legal only when the same selected successful, sealed, current Run/output set
materially supports every primary requirement under its own metric. `PER_REQUIREMENT` permits
different Runs when requirements are independent. `JOINT_PORTFOLIO` permits multiple Runs only
after exact input/scenario hashes and cross-requirement constraints are compatible. Ties are broken
within one requirement and one comparable metric only. A baseline remains a comparator and cannot
stand in for a policy Run with zero exposure.

## Validation and compatibility

Before implementation, case-neutral offline tests freeze all 53 requested scenarios without years,
problem identifiers, titles, entities, or historical fields. Implementation may take at most two
formal revision cycles and cannot change frozen expectations. Read-only successor diagnostics cover
2019 and 2024; historical regressions cover 2020--2023 C, auxiliary 2020 A, two synthetic E2E cases,
30 original negatives, RC4 output preflight, and RC5 multi-requirement Claims.

RC6 can be frozen only after release consistency, focused and full tests, strict validation, local
CI, anti-hardcoding, leakage/secrets, one-Skill discovery, both historical diagnostics, and the first
read-only Auditor all pass. Only the remotely verified freeze may unlock the official 2018 C input
suitability preflight. A clean-context worker then performs the answer-sealed four-hour one-shot;
the Skill, tests, rubric, evidence rules, and verdict policy remain frozen throughout.

## Risks and stop conditions

Structured predicates establish declared contract support, not truth of arbitrary prose. Source
licence, authority, availability, and the model's prior exposure may remain unknown and must be
reported. Stop on historical mutation, 2025 access, hardcoding, test expectation drift, more than
two Skill cycles, missing official inputs, answer exposure, Skill drift, unbound external data,
post-terminal Runs, or any failed release hard Gate. Failure is retained and routed; it is never
converted into a pass by aggregate score or Agent vote.
