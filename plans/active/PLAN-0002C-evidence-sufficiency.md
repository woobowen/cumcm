# PLAN-0002C — Deterministic Evidence Sufficiency Adjudication

Status: `COMPLETE`
Phase: `PHASE-AUTOMATED-EVIDENCE-SUFFICIENCY-002C`
Owner: main agent
Started: `2026-09-01T11:57:13+08:00`

## 1. Purpose and current environment

Resolve the Phase 002B deadlock without rerunning the twenty candidate experiments and without
starting another nested Codex transport. The phase inserts a deterministic
`PRE_ADJUDICATION_EVIDENCE_GATE` before candidate-quality semantic Judges, attacks the Gate with
project-scoped read-only native Subagents, emits audited automated decisions, replays them offline,
and routes the result to the next eligible phase.

The verified starting environment is the repository root on `feat/upstream-dynamic-eval`, with
clean HEAD and Draft PR #2 head both at
`67a858fe8c3ed36d2ff0043476654eabb1d1faf0`. Baseline CI passed with 262 tests. Phase 002 retained
20 attempts (13 completed, 7 failed), 5 recovery-affected cells, 2 balanced cases against a frozen
minimum of 4, and 1 independent repeat against a frozen minimum of 2. Phase 002B completed zero
formal roles after two Correctness `RESPONSES_CONNECT_RESET` failures.

## 2. Scope

- Freeze and verify Phase 002, 002A, and 002B evidence without changing historical artifacts.
- Resolve Phase 002C configuration from Phase 002B and the Phase 002A policy instead of creating
  conflicting threshold authorities.
- Compute primary eligibility, balanced complete cases, independent repeats, cross-arm task-input
  hash consistency, recovery exclusion, and target-specific hard Gates.
- Short-circuit candidate-quality semantic Judges when frozen sufficiency fails or a mandatory
  hard Gate already determines rejection.
- Create four independent first-round native Subagent audits and one post-decision native Decision
  Audit, all read-only and non-voting.
- Emit architecture/evidence-sufficiency, whole-package adoption, recovery-policy, and component-
  readiness decisions through the existing automated-decision contract.
- Produce deterministic replay, generated reports, formal state, a self-contained Phase 002D
  evidence-expansion plan, atomic Git delivery, and a verified Draft PR update.

## 3. Non-goals and immutable boundaries

- Do not rerun a Phase 002 candidate experiment or start Phase 002D experiments.
- Do not run nested `codex exec`, `codex app-server`, Codex SDK, Responses API, OpenAI API, or API
  key flows.
- Do not integrate, install, execute, or copy a third-party Skill or candidate repository.
- Do not delete or rewrite Phase 002B adapters, checkpoints, diagnostics, manifests, or the two
  connect-reset findings.
- Do not select a base, start Phase 003, mark PR #2 ready, merge, rebase, force-push, or modify
  `main`.
- Do not edit `reports/current_state.md` manually; regenerate it from formal state.

## 4. Frozen policy and execution order

The inherited thresholds remain `balanced_case_minimum=4`, `minimum_repeats=2`, and
`recovery_policy=GAP_EVIDENCE_ONLY`. The order is:

1. Verify all three historical freezes and the Phase 002C input manifest.
2. Evaluate target-specific mandatory hard Gates.
3. Build the primary eligible set; exclude failed, recovery-affected, superseded, and NOT_RUN
   observations from comparative evidence.
4. Compute cross-arm balanced complete cases and independent repeats from data.
5. Emit a deterministic sufficiency record.
6. If insufficient, emit `EVIDENCE_INSUFFICIENT`, skip candidate-quality semantic Judges and
   ranking, and route only to `PHASE-EVIDENCE-EXPANSION-002D` after Audit PASS.
7. If a whole-package hard Gate fails, emit `AUTOMATED_REJECTED` for that adoption target.
8. Only a sufficient comparison without blocking hard Gates may require semantic Judges and become
   eligible for a future Phase 003 route.

## 5. Native Subagent design

Project-scoped definitions live under `.codex/agents/` and contain `name`, `description`,
`developer_instructions`, and `sandbox_mode="read-only"`. Model and reasoning are omitted so all
five roles inherit the parent session consistently.

First-round roles are Evidence Sufficiency Auditor, Adjudication Policy Prosecutor, Dissent and
Cost Auditor, and Reproducibility Auditor. They receive role-specific frozen bundles, cannot see
peer outputs, cannot write files, and return Schema-valid JSON with evidence IDs and file
references. The main agent alone validates, normalizes, hashes, and writes their results. Any
testable BLOCKER becomes an adversarial test; a non-testable assertion remains uncertainty and
cannot independently reject or accept a target.

The Automated Decision Auditor starts only after the four results, tests, automated decisions, and
replay exist. Its `PASS`, plus passing deterministic audit checks, is required for a complete
technical state. Role recommendations are never counted as votes.

## 6. Decision contracts

- `DECISION-EVIDENCE-SUFFICIENCY-002C` decides whether frozen comparative evidence can choose an
  architecture or component combination.
- `DECISION-DIRECT-UPSTREAM-ADOPTION-002C` records separate whole-package results for HANDSOMEZR and
  YUSHUI using license, contamination, scope, second-state, second-orchestrator, security, and
  full-runtime Gates.
- `DECISION-RECOVERY-POLICY-002C` may accept only `POLICY_ONLY`: recovery supports diagnosis, gap
  discovery, test design, and recovery engineering, never comparative ranking or selection.
- `DECISION-COMPONENT-READINESS-002C` records one result for each of the four frozen mechanisms and
  never exceeds `SPECIFICATION_ONLY`.

The existing `contracts/automated_decision.schema.json` remains the sole decision contract and is
versioned to cover these target types and scopes. Reports render records; they do not decide.

## 7. Milestones and acceptance criteria

1. **M1 phase start** — archive the unchanged incomplete 002B plan, create this active plan, update
   state/ledgers/version, and preserve the one-plan invariant.
2. **M2 governance and contracts** — add four ADRs, inherited config/policy, pre-adjudication and
   native-audit rules, four new Schemas plus fixtures, and version the existing decision/state
   contracts. Accept when contract and strict repository checks pass.
3. **M3 deterministic engine** — add evidence sufficiency, pre-adjudication, short-circuit, phase
   routing, input freeze, decision, audit, replay, and reporting modules plus five offline scripts.
   Accept when every script has working `--help` and `--check`, no network/model path, stable JSON,
   and non-zero failure codes.
4. **M4 adversarial suite** — add at least forty meaningful offline tests covering thresholds,
   exclusions, hard Gates, label/order invariance, report derivation, Subagent isolation, routing,
   API/nested-Codex prohibitions, and historical preservation. Accept with all old and new tests
   passing.
5. **M5 first-round audits** — launch four independent read-only native roles without peer-output
   visibility, validate/normalize their JSON, and transform every testable BLOCKER into executed
   test evidence.
6. **M6 decisions and final audit** — generate the four automated decision records from frozen
   inputs and executed tests, run the independent Decision Auditor, require `PASS`, then finalize
   offline replay and phase routing.
7. **M7 state and reports** — update formal state and append-only ledgers from audited records;
   generate all 002C reports and the 002D plan; regenerate current status. Accept when state,
   decisions, Audit, replay, reports, and next-phase route agree.
8. **M8 delivery** — run every requested validation command with a structured command ledger,
   commit explicit paths in atomic groups, push normally, verify local/remote SHA, update only Draft
   PR #2, and confirm remote CI without merging.

## 8. Validation commands

```text
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_instruction_budget.py
.venv/bin/python scripts/check_skill_discovery.py --expected-name cumcm-modeling-evidence --expected-count 1
.venv/bin/python scripts/check_contracts.py
.venv/bin/python scripts/check_upstream_manifest.py
.venv/bin/python scripts/check_answer_leakage.py
.venv/bin/python scripts/check_secrets.py
.venv/bin/python scripts/freeze_phase002_evidence.py --check
.venv/bin/python scripts/freeze_phase002b_inputs.py --check
.venv/bin/python scripts/run_pre_adjudication.py --check
.venv/bin/python scripts/run_phase002c_decision.py --check
.venv/bin/python scripts/audit_phase002c_decision.py --check
.venv/bin/python scripts/replay_phase002c_decision.py --check
.venv/bin/python scripts/summarize_phase002c.py --check
.venv/bin/python scripts/render_status.py
.venv/bin/python scripts/render_status.py --check
.venv/bin/python scripts/validate_repo.py --strict
bash scripts/ci.sh
git diff --check
git status --short --branch
```

Every final command record includes command, exit code, duration, deterministic/Subagent type,
result, blocker, and available evidence hash.

## 9. Risks and stop conditions

- A mismatch in any Phase 002/002A/002B artifact yields `INPUT_FREEZE_BROKEN` and stops decisions.
- Missing, invalid, peer-contaminated, or writing Subagent output leaves the phase
  `AUTOMATED_ADJUDICATION_INCOMPLETE`; the main agent never fabricates a role.
- A Subagent BLOCKER stays open until a registered test resolves it or records it as non-testable
  uncertainty.
- A Decision Audit result other than `PASS`, unstable replay, stale generated report, contract
  failure, or remote SHA mismatch prevents completion.
- The interactive environment exposes at most four total concurrent agents including the main
  thread. If four child auditors cannot literally occupy simultaneous slots, preserve first-round
  independence and record the actual launch schedule rather than claiming concurrency not achieved.

## 10. Progress and findings

- `2026-09-01T11:50:20+08:00`: repository, branch, remote, PR, auth, and toolchain preconditions
  passed; local/remote/PR head matched `67a858f...`; workspace was clean.
- `2026-09-01T11:51:00+08:00`: baseline `bash scripts/ci.sh` passed with 262 tests and strict zero
  errors/warnings.
- `2026-09-01T11:57:13+08:00`: Phase 002, 002A, and 002B freeze/recovery checks passed; one formal
  Skill and no forbidden tracked raw/cache/vault paths were confirmed.
- `2026-09-01T12:30:00+08:00`: M1-M4 implementation reached 346 passing tests. The initial native
  audit wave exposed closed-world freeze, missing-hash, explicit hard-Gate, report-provenance, and
  replay-rebuild defects; each testable finding was converted into an offline regression test and
  the deterministic implementation was repaired before formal decisions.
- `2026-09-01T14:23:31+08:00`: M5-M7 completed on freeze
  `cc6397b0aea83d910105b15c5fb2f701ac4ff4def2858deb55c283d7cc396aa9`. Four independent
  first-round native Subagents returned `PASS`; all 24 testable BLOCKER findings map to passing
  adversarial tests; the post-decision Auditor returned `PASS`; the mechanical Decision Audit
  passed; and the offline final replay was stable.
- The formal result is `AUTOMATED_ADJUDICATION_COMPLETE`: comparison and components are
  `EVIDENCE_INSUFFICIENT`, both direct whole-package targets are `AUTOMATED_REJECTED`, recovery is
  accepted only as `POLICY_ONLY`, no architecture/component is selected, and only
  `PHASE-EVIDENCE-EXPANSION-002D` is allowed. Phase 002D has not started.
- Open non-blocking finding: direct-adoption risk fields currently accept arbitrary strings with a
  `LOW` prefix. Both actual packages still have all seven hard Gates false, so the current rejection
  is invariant; no future positive adoption may pass until explicit safe enums are enforced.
- Transport remains historically unresolved. This does not block the audited insufficiency result,
  because no semantic role or transport output is needed after the frozen pre-adjudication Gate
  short-circuits candidate comparison.
- `2026-09-01T14:30:11+08:00`: M8 completed for acceptance commit
  `f9aea6b47de57ed0dba9b84670d95d34ee3f65dc`: normal push succeeded, local and remote SHA matched,
  Draft PR #2 remained open and Draft, and remote `offline-validation` passed in 34 seconds. No
  force-push, merge, `main` mutation, Phase 002D execution, or Phase 003 transition occurred.

## 11. Next step

Wait for explicit authorization to start `PHASE-EVIDENCE-EXPANSION-002D`. The phase is allowed but
not started; Phase 003 remains prohibited.

## 12. Rollback and update rule

Rollback published work only through scoped `git revert`; never reset, clean, rebase, overwrite
historical evidence, or force-push. On interruption, re-read the truth chain and resume the earliest
incomplete milestone after verifying the Phase 002C input freeze. Update this plan after every
milestone, failed validation, new blocker, material finding, or approved design change. Preserve
failed history and mark superseded decisions instead of silently rewriting it.
