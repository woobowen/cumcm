# Project goals

## Objective

Create a durable, evidence-first modeling system for a three-person CUMCM team. The repository owns the chain from contest inputs through validated models, experiments, frozen final runs, and a structured evidence package consumed by a separate paper team.

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

Final paper prose, figure styling, table beautification, typesetting, submission packaging, human-only websites, automatic paid resources, and unreviewed integration of third-party Skills. Foundation phase excludes complete modeling capability, historical-problem execution, dynamic upstream evaluation, and final base selection.

## Safety and reproducibility

Third-party inputs are untrusted until audited. Candidate code is never executed in foundation. Formal outputs require Run IDs, input hashes, Git commits, environment/seed/config capture, sources, reviewer findings, and staleness rules. Secrets, private vaults, and global Codex settings remain outside scope.

## Team boundary

This repository supplies facts, formulas, tables, figure-ready data, validation, uncertainty, limitations, reproduction commands, and claim-evidence mappings. The paper team may render and explain those facts but must not alter experiment truth; corrections return through a new modeling decision/run.

## Undecided

- Upstream architecture/base: `EVIDENCE_INSUFFICIENT`; Phase 002D-R1 accepts four component
  specifications only, without implementation, integration or a positive performance claim.
- Project license: `PROJECT_LICENSE_UNDECIDED`.
- Production modeling methods, reviewer thresholds, and benchmark cases: `NEEDS_REVIEW`.
- Official 2026 rule extraction: registered but `NEEDS_EXTRACTION`.

Phase 002D-R1 completes failure-aware adjudication while quality remains insufficient at two
balanced cases and quality repeat depth one. Its next legal route is a redesigned, newly frozen
Phase 002D acquisition; it cannot integrate a candidate, select a base, or start Phase 003.
