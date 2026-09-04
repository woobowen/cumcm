# Project goals

## Objective

Create a durable, evidence-first modeling system for a three-person CUMCM team. The repository owns the chain from contest inputs through validated models, experiments, frozen final runs, and a structured evidence package consumed by a separate paper team.

## Current priority

Deliver one runnable Competition RC Skill quickly, then spend the primary effort on answer-sealed historical Development problems to expose real generalization failures. RC1 is the starting instrument, not proof of unseen-problem effectiveness: each blind first run is frozen before answer access, generalizable failures feed RC2, and problem-specific findings remain isolated.

## Success criteria

- One formal Skill routes every stage and can recover from repository state without chat memory.
- Raw inputs, sources, decisions, models, runs, metrics, and handoff claims are traceable and reproducible.
- Deterministic checks enforce invariants; judgmental reviews produce explicit findings and evidence.
- Technical selections use frozen lexicographic evidence rules, Blind Judges, Dissent,
  Meta-Adjudication, and Decision Audit; neither humans nor agent votes select a result.
- Development, validation, held-out, and live-contest modes prevent answer leakage.
- Upstream mechanisms are evaluated in isolation before adoption and remain license/security traceable.
- A versioned modeling-to-paper contract prevents prose edits from rewriting experimental facts.

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

The later Competition RC1 repair sprint preserves that historical boundary and old blocked decision,
then accepts new project-owned K1/W1 revisions through the unchanged eight public hard Gates. K1 is
integrated under the frozen K1-first rule. The next authorized task is
`PHASE-SKILL-DEVELOPMENT-EVAL-004`, not additional meta-governance.
