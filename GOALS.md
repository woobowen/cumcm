# Project goals

## Objective

Create a durable, evidence-first modeling system for a three-person CUMCM team. The repository owns the chain from contest inputs through validated models, experiments, frozen final runs, and a structured evidence package consumed by a separate paper team.

## Current priority

Within finite contest time, improve the formal Skill's first-pass completion rate, professional
modeling quality, real execution, robustness, and paper-team handoff completeness on unfamiliar
C problems. Freeze one RC across a diverse C-problem batch, finish and independently freeze every
answer-sealed first run before any Skill change or reference unlock, then admit only repeated
cross-case failures or universal hard failures into one unified revision. A problems are auxiliary
transfer/regression evidence only; B problems are excluded by default.

## Success criteria

- One formal Skill routes every stage and can recover from repository state without chat memory.
- Raw inputs, sources, decisions, models, runs, metrics, and handoff claims are traceable and reproducible.
- Deterministic checks enforce invariants; judgmental reviews produce explicit findings and evidence.
- Technical selections use frozen lexicographic evidence rules, Blind Judges, Dissent,
  Meta-Adjudication, and Decision Audit; neither humans nor agent votes select a result.
- Development, validation, held-out, and live-contest modes prevent answer leakage.
- Upstream mechanisms are evaluated in isolation before adoption and remain license/security traceable.
- A versioned modeling-to-paper contract prevents prose edits from rewriting experimental facts.
- C-problem evidence accounting never treats same-case regression, Stress, or A-problem success as
  an independent C Validation result.

## Scope

Problem decomposition, mechanism/source research, data audit, formalization, baselines, candidate models, implementation verification, experiment design, run orchestration, validation, robustness/uncertainty, cross-question consistency, Final Run freeze, and evidence-package handoff.

## Non-goals

Final paper prose, figure styling, table beautification, typesetting, submission packaging, human-only websites, automatic paid resources, unreviewed integration of third-party Skills, answer leakage, model/API training, and claims of production readiness. RC1 does not establish sealed Stage 1, Stage 2 effectiveness, full ablation, external validity, production fitness, or monetary cost.

## Safety and reproducibility

Third-party inputs are untrusted until audited. Candidate code is never executed in foundation. Formal outputs require Run IDs, input hashes, Git commits, environment/seed/config capture, sources, reviewer findings, and staleness rules. Secrets, private vaults, and global Codex settings remain outside scope.

## Team boundary

This repository supplies facts, formulas, tables, figure-ready data, validation, uncertainty, limitations, reproduction commands, and claim-evidence mappings. The paper team may render and explain those facts but must not alter experiment truth; corrections return through a new modeling decision/run.

## Undecided

- Base/third-party adoption remains unset. The project-authored K1 architecture is selected only for
  `COMPETITION_RC_IMPLEMENTATION_ONLY`; this is not upstream superiority or third-party integration.
- Project license: `PROJECT_LICENSE_UNDECIDED`.
- Production modeling methods, reviewer thresholds, and benchmark cases: `NEEDS_REVIEW`.
- Official 2026 rule extraction: registered but `NEEDS_EXTRACTION`.

Phase 002D-R1 completes failure-aware adjudication while quality remains insufficient at two
balanced cases and quality repeat depth one. Its next legal route is a redesigned, newly frozen
Phase 002D acquisition; it cannot integrate a candidate, select a base, or start Phase 003.

Phase 002D-R2 uses that bounded authorization only to freeze four clean-room specifications and a
prospective architecture-comparison protocol. It may authorize a later isolated shadow prototype,
but cannot implement components, select an architecture, change the formal Skill, or enter Phase 003.

## Phase 004C3 active objective

Phase 004C3 preserves the blocked RC5 and both negative Validation histories while repairing the
single formal Skill as RC6. The authorized scope is release metadata consistency, requirement-level
evidence/data sufficiency, external-data acquisition planning, per-requirement or compatible
portfolio selection, and bounded machine-checkable semantic Claim predicates. Case-neutral tests
must be frozen before implementation; the Skill has at most two revision cycles.

Only a remotely verified, fully regressed RC6 may be used for one fresh answer-sealed C Validation.
The preferred/fallback official cases are preregistered, the worker is context-isolated, the
one-shot is limited to four hours, and no Skill/test/rubric change is allowed after it starts. The
2025 C Held-out remains completely unaccessed. A Validation pass may route to 004D; any other valid
RC6 outcome routes to 004C4 or remains blocked, without a generalization or 2026-solved claim.

Phase 004C3 terminated before fresh Validation. Auditor 1 reproduced 13 fail-open probes across the
RC6 data-sufficiency, portfolio-selection, semantic-Claim and compatibility Gates and found that the
fresh-completion controller hardcodes a global descriptive/empirical path. The two formal revision
cycles are exhausted, so RC6 is not released and no third repair is permitted in this phase. No
2018/2017 official input or answer was accessed; 2025 remains fully sealed. The exact next phase is
`null`.

## Phase 004C4 active objective

Phase 004C4 preserves that terminal block and opens a separate bounded repair window for the actual
completion controller. Thirteen controller-level CLI probes must be frozen before implementation;
the formal chain must execute hash-bound data, selection, Run, compatibility, semantic, aggregate,
finalization and handoff Gates and emit a replayable gate trace. Three neutral end-to-end cases and
an independent adversarial audit are required before RC7 release eligibility.

That repair and its independent audit are now complete. The candidate snapshot passed full pytest,
strict validation and local CI, and the live release advances RC7 to
`C_TARGET_RC7_READY_VALIDATION_PENDING`; release delivery remains the final prerequisite before
official 2018 C input access.

Only a candidate/live-consistent, fully regressed and remotely frozen RC7 may access the fresh
official C Validation input. The answer remains sealed, the one-shot remains four hours, and 2025 C
remains wholly unaccessed. A released RC7 with a non-PASS fresh result routes to 004C5; release
failure remains in 004C4 with no next phase. This work does not prove full generalization,
production readiness or a 2026 solution.

The later Competition RC1 repair sprint preserves that historical boundary and old blocked decision,
then accepts new project-owned K1/W1 revisions through the unchanged eight public hard Gates. K1 is
integrated under the frozen K1-first rule. That checkpoint authorized
`PHASE-SKILL-C-TARGET-BATCH-GENERALIZATION-004C`: three diverse C Development first runs on frozen
RC3, one unified evidence-based revision at most, unified regression, and a separate one-shot C
Validation. Existing 2023 C and 2020 A results remain Development evidence and do not establish
broad C-problem generalization.

The single evidence-admitted revision is frozen as `0.2.0-competition-rc4` after unified
regression. The answer-sealed, rubric-frozen 2024 C one-shot produced 4/4 successful actual Runs
and valid outputs for all six main requirements, but the frozen Claim Gate imposed contradictory
global-scope and first-requirement-scope equalities. The terminal result is therefore
`C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT`, not a pass; no handoff was accepted and RC4 was not
changed. That terminal checkpoint authorized a newly frozen C batch repair using a different C case.

## Phase 004C2 terminal result

The case-neutral Claim implementation passed the frozen tests within two revision cycles.
Post-decision audit found an unresolved release blocker: the frozen Skill VERSION file still says
RC4 while the runner, SKILL.md and manifest say RC5. Release acceptance is BLOCKED_VERSION_METADATA;
the frozen Skill cannot be changed in this episode.
The one Skill runs the hash-frozen `0.2.0-competition-rc5` implementation, K1, `COMPETITION_RC`;
its inconsistent VERSION label is preserved as audited evidence.
Release truth: `evals/results/phase-004c2/rc5_release.json`; execution record:
`plans/active/PLAN-0004C2-claim-scope-repair-and-fresh-validation.md`.
The 2024 terminal verdict and original artifacts remain unchanged.
RC5 release `24265710b3f4b154ccf6eff19614eea7fb3fb0d4` was remotely verified before
2019 official input access. The pre-run freeze was remotely delivered before all nine actual Runs.
`CUMCM-2019-C-VALIDATION-002` terminated as `C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT`:
Q2 requires actual airport/city observations, which are absent. Native Run/Claim/handoff contracts
passed structurally; Q4 semantic support is incomplete in the selected baseline Claim.
The frozen rubric rejected paper dispatch and the
final case state is `REJECTED`. No whole-problem completion or joint optimum is claimed.
The machine decision and terminal freeze live under
`evals/results/phase-004c2/CUMCM-2019-C-VALIDATION-002/`.
RC5, case code, rubric and neutral tests remain frozen; no model retry or later same-case Validation
is permitted. Answers remain sealed. The next phase is `null`; Held-out 004D is locked and all six
2025 access flags remain false. Later work on this case can only be Development under new scope.
