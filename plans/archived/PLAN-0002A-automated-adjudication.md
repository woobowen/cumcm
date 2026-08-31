# PLAN-0002A — Automated Evidence Adjudication

Status: `IN_PROGRESS`
Phase: `PHASE-AUTOMATED-ADJUDICATION-002A`
Owner: main agent
Started: `2026-08-31T21:57:10+08:00`

## 1. Purpose

Replace Phase 002's human technical selection Gate and score-led proposal mechanism with a frozen,
replayable, evidence-lexicographic adjudication pipeline. Preserve all Phase 002 evidence, exclude
recovery-affected cells from comparison, attack every decision path, and permit acceptance,
rejection, retest, insufficiency, abstention, or staleness without forcing a winner.

## 2. Environment and authority

- Repository: `<REPO_ROOT>` on `feat/upstream-dynamic-eval`; continue Draft PR #2.
- Phase 002 evidence subject commit: `6a046822c33bcdf8a6821a96333bc92720e764c0`.
- Main agent is the sole formal-state writer; all attack/Judge agents are read-only.
- `WORKFLOW.md`, `rules/`, `contracts/`, and `state/` remain the normative chain.
- The formal Skill stays `0.1.0-foundation` and `SCAFFOLD_ONLY`.

## 3. Scope

Freeze tracked Phase 002 evidence; separate structured coverage, oracle correctness, process and
robustness evidence; calculate balanced complete cases; synthesize tests from serious findings;
run independent blind Judges, Dissent, Meta-Adjudicator and Decision Auditor; generate three
machine decisions and derived reports; migrate verification state to a non-self-referential model.

## 4. Non-goals

Do not rerun the original 20 candidate cells, execute or copy candidate code, install candidate
dependencies, read historical answers or the benchmark vault, integrate a component, modify the
formal Skill, start Phase 003, create a branch/PR, merge, mark ready, modify main, rebase, or force
push. Team compliance review cannot choose or override a technical result.

## 5. Frozen evidence and eligibility

Every tracked Phase 002 evidence file is SHA-256 and Git-blob bound at the Phase 002 final commit.
Mutation is `EVIDENCE_FREEZE_BROKEN` and stops adjudication. Recovery records remain available only
for parser-gap discovery and test synthesis. Comparative evidence requires original COMPLETED,
Schema-valid, hard-failure-free, non-recovery cells with identical task/model/budget settings across
all arms. A minimum of four balanced cases and two repeats is required for comparative adoption;
otherwise the result is `EVIDENCE_INSUFFICIENT` or `AUTOMATED_ABSTAINED`.

## 6. Evidence order and decisions

Apply lexicographically: hard Gates; E1/E2/E3 scientific correctness and reproducibility;
relative utility. E0 Agent assertions cannot replace executable evidence, and confidence/consensus
never passes a Gate.
Allowed decisions are `AUTOMATED_ACCEPTED`, `AUTOMATED_REJECTED`, `RETEST_REQUIRED`,
`EVIDENCE_INSUFFICIENT`, `AUTOMATED_ABSTAINED`, and `STALE`. Hard failures are non-compensable.

## 7. Independent roles

First-round attack roles are scoring, recovery, report provenance, sandbox/isolation, state
semantics, and Dissent. Runtime adjudication roles are Correctness, Scientific Validity,
Engineering Reproducibility, Dissent, Evidence Meta-Adjudicator, and Decision Auditor. Judges see
anonymous frozen bundles and never see peer output. Meta applies frozen rules; Auditor must pass
before the orchestrator changes formal state. No majority vote is used.

## 8. Milestones and acceptance

1. M1 preflight/read/audit: exact environment, 93-test baseline, and six independent attacks.
2. M2 freeze/contracts: immutable manifest, evidence hierarchy, policies, Schemas and fixtures.
3. M3 engine: eligibility, scores, test synthesis, Judges, Meta, audit, replay, reporting and state.
4. M4 adversarial suite: at least 30 meaningful new unit/integration/fault nodes; all offline.
5. M5 real adjudication: at most 12 real Codex attempts, retained failures, fixed model/settings.
6. M6 replay/decision: identity/order stability, three Schema-valid decisions and audit result.
7. M7 governance/reporting: remove active human technical Gates, define team compliance boundary.
8. M8 delivery: full validation, atomic commits, normal push, SHA equality, Draft PR/CI verification.

Each milestone requires focused tests, `git diff --check`, current generated outputs, and an
append-only ledger entry before completion.

## 9. Validation

Run the exact Phase 002A command set from the task, including Ruff, full pytest, instruction/Skill,
contracts/upstream/leakage/secrets, freeze/rescore/adversarial/Judge/Meta/audit/replay/summary checks,
status render/check, strict validation, aggregate CI, whitespace and Git status. Record command,
exit, duration, real/mock, model/role when applicable, result, failure, blocker, tokens and evidence
hash. GitHub CI remains offline and never launches real Codex.

## 10. Risks and stop conditions

- Existing scoring/reporting cannot be trusted for correctness or recommendation until replaced.
- Five recovered cells lack sufficient primary provenance for comparative ranking.
- Workspace-write is not proof of OS network denial; claims must use policy/trace-audited wording.
- Six synthetic cases and one primary run per cell may force abstention.
- Agent unavailability, quota or more than three infrastructure repair failures stops real runtime.
- Evidence freeze mutation, identity leak, policy mutation, unresolved BLOCKER Dissent, failed audit,
  or unstable replay blocks state advancement.

## 11. Findings before implementation

- Scoring uses substring coverage, omits several hard-failure detectors, and lacks observation/run
  provenance binding.
- Reporting consumes directory contents without validating frozen hashes and hardcodes current
  scores, recommendation, counts and interpretations.
- Recovery is post-hoc hash-bound, can be inferred from file existence, and entered unbalanced rank.
- Network enforcement is policy plus observable trace audit, not verified OS denial; command and
  environment isolation need stronger tests and truthful terminology.
- `last_verified_commit` is free-form and self-reference-prone; lifecycle/status vocabularies and
  acceptance truth are duplicated.
- Dissent challenges the portfolio benefit, four-way decomposition, native fallback, and reliable
  semantic automation; these claims require tests and may remain unresolved.

## 12. Progress

- [x] Full Phase 002A prompt, startup truth chain, target policies, code and tests read.
- [x] Preconditions verified; Draft PR #2 is OPEN/DRAFT and local/remote HEAD are equal.
- [x] Unmodified baseline CI passed with 93/93 tests and strict PASS.
- [x] Six independent read-only attack roles completed; no result was shared before completion.
- [x] Phase 002 evidence freeze generated and rechecked: 20 attempts, 13 complete, 7 failed,
  five recovery-affected; freeze hash valid.
- [x] Rules/contracts/engine and 79 new test nodes implemented; full pre-runtime suite reached
  172 passing tests.
- [x] Incomplete reports and v2 formal-state migration generated without fabricating decisions.
- [ ] Real adjudication/replay/decision completion is blocked: three consecutive Correctness Judge
  attempts failed in Codex Responses transport before structured output; Meta and Auditor not run.
- [x] Content commit `fee8aeb157607629e86bbfe5d8cb41e60d12f34f` pushed and remote SHA verified.

## 13. Update, recovery, and rollback

Update this plan after each milestone, failed validation, new blocker or design change. Preserve
failed runs and superseded decisions. Resume from the earliest unchecked item after verifying the
freeze and CI. Roll back published work only with scoped `git revert`; never reset, clean, erase
evidence, rewrite history, or force push.

## 14. Completion condition

Report `AUTOMATED_ADJUDICATION_COMPLETE` only when the frozen evidence, serious-finding tests,
machine decisions, Meta record, Decision Auditor result, replay stability, reports, state, full CI,
remote SHA and Draft PR CI all verify. Otherwise report `AUTOMATED_ADJUDICATION_INCOMPLETE` with the
exact blocker. Completion never starts Phase 003; it only records whether automation permits it.
