# CUMCM C-Problem Target Policy

`rules/target_problem_policy.yaml` is the machine source for
`DECISION-C-TARGET-TRAINING-POLICY-004C`. This document explains that policy; it does not select a
model architecture or replace project state.

## Target and allocation

The primary competition target is `CUMCM_C_PROBLEM`. Priority is: first complete solution on an
unfamiliar C problem, transfer across distinct C structures, contest-time efficiency, then only the
cross-type capability needed to avoid regressions. Independent C Development work must account for
at least 80% of the historical-plus-preregistered independent allocation. A problems are
`AUXILIARY_TRANSFER_ONLY`; B problems are `EXCLUDED_BY_DEFAULT` unless a later explicit policy
decision changes the strategy.

Planned allocation and realized evidence are reported separately. A preregistered case cannot be
claimed as a completed or strictly blind first run. Stress and same-case Development regression do
not count as independent C evidence. Success on an A problem cannot substitute for C Validation.

## Batch freeze and revision admission

`C-TARGET-BATCH-001` contains three structurally different C Development positions and binds formal
Skill `0.2.0-competition-rc3`, release commit `8a2a813ff34d8c2701c64ff9d959848e7b88c27c`,
and Skill tree `a4551c8aa0b6b119823f6ce9df3f0f948339bb33`. Every answer begins `SEALED`; model-prior
exposure is `MODEL_PRIOR_EXPOSURE_UNVERIFIABLE`.

All three first runs must be frozen, checked, independently committed, pushed, and remote-SHA
verified before any reference unlock or formal Skill mutation. A case may freeze as successful,
partial, blocked, rejected, STALE, or failed. Failed Runs remain evidence.

Only a defect repeated independently in at least two C cases, or one universal non-compensable hard
failure, may support a formal Skill change. A neutral case-independent test is mandatory. The
formal Skill may not contain a historical year, problem number/title, attachment or field name,
entity, answer, optimum, or case-specific parameter. No acceptable general change means RC3 is
retained; producing RC4 is not itself a success criterion.

The frozen batch produced one eligible repeated failure and exactly one revision cycle. The sole
formal Skill is now `0.2.0-competition-rc4`, implementation commit
`297cad0a29c659b18484d4f3b67d69a942ad415c`, tree
`d041ca38de030ae04813ef02dbe12f7f2b7a1c22`. RC4 remains case-neutral and is frozen for the 2024 C
one-shot Validation; the original RC3 batch identity and first-run evidence remain unchanged.

## Validation and Held-out

Validation, Held-out, and final simulation must all use C problems. Validation uses a frozen Skill,
fresh isolated worker, sealed answer, preregistered rubric, and one terminal first run. After the
terminal freeze, a new Run is prohibited; later work on that problem is Development only. Answer or
solution exposure before freeze invalidates strict Validation eligibility.

The 2025 C Held-out is reserved in this phase by the hash of its official annual-page URL only. Its
title, archive, problem, attachments, references, and answer remain unaccessed. The reservation is
not Development or Validation evidence.

## Scope and limits

This is a training-target and evidence-accounting decision, not an architecture decision. It does
not prove broad C generalization, production readiness, or a 2026 solution. Technical acceptance
continues to depend on deterministic Gates, captured Runs, feasible Finals, Claim evidence,
reproducible handoffs, and the formal state machine; Agent votes cannot override a rejection.
