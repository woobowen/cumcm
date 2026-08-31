# Changelog

## 0.2.1-automated-adjudication — 2026-08-31

- Replaced the active human technical gate with frozen, lexicographic automated adjudication and a
  separate non-overriding team compliance/challenge contract.
- Froze all Phase 002 evidence; separated structured coverage, deterministic correctness, and process
  evidence; excluded five recovery-affected cells from rank.
- Added Blind Judge, Dissent, test synthesis, Meta, Auditor, replay, generated reports, 18 protocol
  cases, and more than 30 offline regression nodes.
- Recorded `AUTOMATED_ADJUDICATION_INCOMPLETE` after three consecutive Codex transport failures;
  no machine decision, Phase 003 transition, or third-party integration was fabricated.

## 0.2.0-dynamic-eval — 2026-08-31

- Completed the historical, then-human-gated upstream dynamic evaluation evidence phase; its
  proposals are now archived/superseded by Phase 002A.
- Added the isolated synthetic-evaluation architecture, ADRs, runbook, and machine rules.
- Kept the formal Skill at `0.1.0-foundation` and `SCAFFOLD_ONLY`.

## Unreleased

### Changed

- Added persistent, machine-readable Git remote-delivery policy, tracked-path redaction, and remote SHA verification requirements.

## 0.1.0-foundation — 2026-08-31

### Added

- Foundation governance, single-Skill scaffold, upstream isolation/evaluation harness, machine rules/contracts/state, validators, tests, and local CI.

### Changed

- None; initial project version.

### Fixed

- None.

### Removed

- None.

### Security

- Upstream code is isolated and statically inspected only; secrets, answer leakage, discovery pollution, and dangerous instructions are checked locally.

### Known limitations

- The formal Skill is `SCAFFOLD_ONLY` and lacks complete modeling capability.
- Upstream candidates have only provisional static reviews; no historical or dynamic evaluation is complete.
- No final base Skill has been selected and the project license remains undecided.
