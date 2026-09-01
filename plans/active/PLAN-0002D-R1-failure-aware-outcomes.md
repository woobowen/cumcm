# PLAN-0002D-R1 — Failure-Aware Outcome Adjudication

Status: `IN_PROGRESS`
Phase: `PHASE-EVIDENCE-EXPANSION-002D`
Subphase: `PHASE-002D-R1-FAILURE-AWARE-OUTCOME-ADJUDICATION`
Owner: main agent
Started: `2026-09-01T23:12:32+08:00`
Branch: `feat/evidence-expansion-002d`
Base commit: `d59f4b8a36fa3c15e06ec0aceb948cd2bafd2abc`
Predecessor: `plans/archived/PLAN-0002D-evidence-expansion.md`

## 1. Purpose and current state

Resolve the frozen Phase 002D experiment as observed outcomes instead of treating every non-success
as missing. The source experiment has 24 planned slots, 28 scored attempts, 20 completed outputs,
18 primary-eligible observations, eight completion failures, two completed exclusions, seven
policy violations, six authoritative `HARD-FAIL-003` findings and one recorded infrastructure
failure. It stopped at 6,228.480778 seconds after crossing the immutable 6,197-second elapsed cap.

The old Gate remains `INSUFFICIENT`: its primary-eligibility coverage reported three of four
balanced cases and eligible repeat depth one of two. R1 does not overwrite that historical record;
its stricter quality projection excludes oracle-failing terminal negatives and therefore has two
balanced cases at repeat depth one. The legacy runner-wide complete-repeat depth is zero. The
original budget is closed and may not be edited or expanded. Architecture is null, accepted
components are empty, base selection and third-party integration are false, and the formal Skill
remains `0.1.0-foundation`/`SCAFFOLD_ONLY`.

## 2. Scope

- Freeze Phase 002–002D evidence byte-for-byte into a separate R1 manifest.
- Classify all 28 attempts through one closed, evidence-backed failure taxonomy.
- Resolve all 24 `case × anonymous arm × repeat` slots without best-of-N selection.
- Separate quality, reliability, outcome-completeness and component-gap evidence.
- Replace ambiguous reporting with four explicit repeat-depth metrics while retaining the legacy
  field as deprecated compatibility data.
- Detect retry-until-success bias and preserve every attempt in reliability and cost denominators.
- Run five independent native read-only first-round audits with no peer visibility or voting.
- Convert every testable BLOCKER/ERROR finding to deterministic test requests and evidence.
- Decide whether a new, separate supplemental tranche is authorized only for censored slots.
- Generate failure-aware decisions, run an independent post-decision Auditor and replay label/order
  variants before the main agent changes terminal state.
- Update the existing Draft PR #3 without readying, approving or merging it.

## 3. Non-goals and prohibitions

Do not mutate any Phase 002–002D result; edit or expand `PHASE-002D-FROZEN-BUDGET-001`; turn a
terminal failure into a success or numeric zero; retry a resolved success, terminal negative or
unknown; choose the highest-scoring retry; use an API key or API billing; train/fine-tune a model;
execute or integrate third-party code/Skills; use web/MCP in formal audits; use a human technical
Gate or Agent majority vote; force acceptance; modify `main`; create another branch/PR; ready or
merge PR #3; force-push; or enter Phase 003.

## 4. Failure taxonomy and attribution

Every attempt receives exactly one of `ELIGIBLE_SUCCESS`, `VALID_OUTPUT_ORACLE_FAIL`,
`TERMINAL_POLICY_FAILURE`, `TERMINAL_MODEL_SCHEMA_FAILURE`,
`TERMINAL_UNSUPPORTED_CLAIM_FAILURE`, `INFRASTRUCTURE_CENSORED`, `HARNESS_CENSORED`,
`UNKNOWN_CENSORED`, or `SUPERSEDED`, plus zero or more closed secondary flags. Attribution uses
completion, Schema, oracle, process, hard-failure, trace category, stderr hash, output presence,
input mutation, network/MCP and parser/harness evidence. Identity and output quality are excluded.

`HARD-FAIL-003` means a fabricated run/source/file/metric/test/status claim under the existing
dynamic-evaluation rule. It is terminal only when preserved observations and runner evidence show
the candidate output made the unsupported claim; harness-originated false positives remain
`HARNESS_CENSORED` pending an equivalence test. Mixed failures use deterministic precedence and
retain every secondary flag.

## 5. Slot resolution and evidence scopes

The matrix contains exactly 24 unique slots and all attempt IDs in stable start order. Quality uses
the earliest `ELIGIBLE_SUCCESS` (including oracle PASS) per slot and never a best score. A verified terminal negative
without eligible success resolves the slot negatively and blocks further retries. Infrastructure-
only, harness-only and unknown slots stay censored/unresolved.

Quality evidence keeps the unchanged four-balanced-case/two-repeat Gate. Reliability includes all
28 attempts, their retries, failures, tokens and elapsed time but does not interpret infrastructure
censoring as candidate failure. Outcome completeness counts only eligible successes and terminal
negatives as resolved. Component-gap evidence requires repeated, cross-case or cross-repeat E1/E2
gaps and cannot use an isolated failure, identity, recovery success or vote.

## 6. Repeat semantics and retry-bias controls

Record `quality_balanced_case_count`, `quality_minimum_repeat_depth`,
`outcome_resolved_case_count`, `outcome_minimum_repeat_depth`,
`schedule_attempted_repeat_depth` and `reliability_observed_repeat_depth`. The old `repeat_depth`
remains only as explicitly deprecated runner compatibility data.

The retry audit records retry burden, attempts to first eligible result, terminal failures before
success, success after retry and per-cell attempt efficiency. Deleting failed attempts, converting
failures to zero, highest-score selection, later-success erasure, post-hoc budget expansion,
identity permutation and attempt-order permutation are deterministic fault tests.

## 7. Native Subagent design

First round roles are `failure_attribution_auditor`, `retry_bias_prosecutor`,
`evidence_scope_statistician`, `experiment_protocol_auditor`, and `cost_and_stop_auditor`. Each
receives an independent identity-blind, read-only bundle, no peer output, no expected conclusion and
no later decision. They write nothing and return structured JSON to the main agent. The main agent
validates Schema, bundle hash, references, peer isolation and workspace cleanliness before storing
normalized outputs. `failure_aware_decision_auditor` runs only after decisions exist and may return
only `PASS`, `FAIL`, or `RETEST_REQUIRED`.

## 8. Automated decisions

Generate the seven requested IDs for failure semantics, slot resolution, supplemental authorization,
quality sufficiency, reliability sufficiency, architecture and component readiness. The decisions
are lexicographic and evidence-driven, never a vote. Post-hoc failure-aware policy may support
`POLICY_ONLY` semantics or independently justified `SPECIFICATION_ONLY` component scope, but cannot
prove positive performance superiority on the same observations.

Architecture candidates are `NATIVE_SINGLE_SKILL_CLEAN_ROOM`, `RETAIN_SCAFFOLD_ONLY`,
`EVIDENCE_INSUFFICIENT`, `AUTOMATED_ABSTAINED`, and `AUTOMATED_REJECTED`. Components are decided
independently for accepted-versus-done state, claim-evidence support, hash-bound reproducibility and
leakage-safe comparison. No component is implementation-ready in this subphase.

## 9. Supplemental authorization and frozen budget

Only `CENSORED_INFRASTRUCTURE`, or `CENSORED_HARNESS` after
`HARNESS_SEMANTIC_EQUIVALENCE_PASS`, may be authorized. Resolved success, terminal negative and
unknown slots are prohibited. If no eligible censored slot exists, the supplemental budget has zero
starts and no model is launched.

If authorized, create `PHASE-002D-R1-SUPPLEMENTAL-BUDGET-001` with at most four starts, at most two
per authorized slot, concurrency one, the prompt-specified elapsed/input formulas and exact original
cohort/model/reasoning/prompt/Schema/fixture/package/scorer/oracle/profile hashes. Any protocol
change yields `NEW_PROTOCOL_COHORT_REQUIRED` instead of pooling. The tranche is immutable after
freeze and never changes the original budget.

## 10. Real-run preconditions and stop conditions

Before any real start require freeze PASS, taxonomy decision, slot matrix, five valid first-round
audits, all BLOCKER tests, authorization decision, authorization pre-audit PASS, frozen supplemental
budget and an explicit slot allowlist. Stop at the first resolved outcome, per-slot cap, global cap,
elapsed/input cap, infrastructure recurrence, hash/cohort drift or any hard Gate. Preserve every
start and checkpoint. Missing preconditions mean zero starts, not a workaround.

## 11. Milestones and acceptance

1. **M1 Subphase start:** preflight and 535/1 baseline pass; plan/state/freeze exist; freeze check,
   contract test and strict validation pass; atomic commit and push.
2. **M2 Taxonomy/matrix:** 28 classifications and 24 stable unique slot records validate; targeted
   attribution/slot tests pass; atomic commit and push.
3. **M3 Evidence scopes:** quality/reliability/outcome/component and repeat/retry records validate;
   focused tests pass; atomic commit and push.
4. **M4 Native attacks:** five isolated outputs validate; no peer reference/write/vote exists; all
   testable serious findings have executed evidence; atomic commit and push.
5. **M5 Authorization:** automated authorization and independent pre-audit exist; zero or bounded
   immutable budget is frozen.
6. **M6 Optional runs:** run only when every Gate passes; at most four targeted fresh starts; each
   is checkpointed, classified, validated, committed and pushed. Otherwise record zero starts.
7. **M7 Adjudication:** all seven decisions are Schema-valid and trace to frozen evidence/tests.
8. **M8 Audit/replay:** post-decision Auditor passes; deterministic replay, order permutation and
   anonymous-label permutation are stable.
9. **M9 State/reports/delivery:** derived reports/state/docs are current; at least 60 meaningful new
   test nodes and full offline CI pass; commits are pushed; Draft PR #3 is updated and remote SHA/CI
   verified.

## 12. Validation and evidence recording

Run every command listed in the task, including Ruff lint/format, full pytest, contract/upstream/
leakage/secret/Skill checks, both Phase 002D freezes, all R1 CLIs, status generation/check, strict
validation, `bash scripts/ci.sh`, `git diff --check`, and final branch/status. Record command, exit
code, duration, execution type, result, blocker, evidence hash, model-start count and observable
token use. `--check` is offline, idempotent and never starts a model.

## 13. State migration and phase boundary

At start set the R1 subphase, `FAILURE_AWARE_ADJUDICATION_IN_PROGRESS`, current R1 plan and
`next_phase_allowed=null`; preserve null architecture, empty components, false base/integration and
scaffold capability. Only a complete audited chain may set `AUTOMATED_ADJUDICATION_COMPLETE` and
route according to its decisions. Incomplete supplemental work routes to the same Phase 002D;
failed audit or broken replay yields `AUTOMATED_ADJUDICATION_INCOMPLETE` and null next phase;
historical mutation yields `STALE`. This task never executes Phase 003.

## 14. Risks, recovery and rollback

Principal risks are post-hoc positive inference, retry-until-success bias, mixed transport/model
failure attribution, insufficient small-sample reliability evidence, hidden identity leakage,
historical hash drift and Codex/GitHub transport resets. Unknown monetary, cached/reasoning-token,
CPU, queue, operator and maintenance costs stay `UNKNOWN`.

After interruption, verify branch/worktree, R1 freeze and latest remote SHA, then resume the earliest
incomplete milestone. Never repair historical evidence in place. Published changes roll back only
through scoped `git revert`; generated R1 artifacts are superseded append-only. After three failed
repair cycles, preserve evidence and report the applicable incomplete state.

## 15. Git and PR

Inspect status, whitespace, stats and full unstaged/staged diffs; stage explicit paths only. Use
atomic milestone commits and normal pushes to `feat/evidence-expansion-002d`. GitHub TLS failures
receive at most five bounded retries and may receive one process-local no-proxy control. Never
reset/clean/rebase/force-push/merge. PR #3 remains OPEN/DRAFT and is updated only from machine truth.

## 16. Progress, findings and next step

- `2026-09-01T23:12:32+08:00`: preflight passed at clean local/remote SHA `d59f4b8...`; origin and
  Draft PR #3 matched the required target; remote CI passed.
- `2026-09-01T23:13:00+08:00`: baseline `bash scripts/ci.sh` passed with 535 tests, one expected
  skip, 45 valid/35 rejected-invalid contract fixtures and strict zero errors/warnings.
- Current finding: source records include mixed attempts where a transport label coexists with a
  Schema-valid observation and authoritative hard failure; R1 attribution must test evidence
  precedence rather than copying the historical summary label.
- `2026-09-02T01:59:30+08:00`: recovery preflight reconfirmed local/remote SHA `d59f4b8...`,
  OPEN/DRAFT/MERGEABLE PR #3 and successful remote CI; inherited dirty scope matched M1 only.
- `2026-09-02T02:00:00+08:00`: wrote an ignored recovery snapshot. Patch/status/files SHA-256 are
  `f23db21517e88ec21304b3876707b44147c1ff0986c1addbcb14f193cd0ab4bd`,
  `2e4df203e347385e5c743033ef45d150ee8dca5ac915de5276fcc295537b0ff0`, and
  `a6e46bd42759c0b7f784b057b0638b41b4ca20e4eb33d38f21c199a89a211ba0`.
- `2026-09-02T02:04:39+08:00`: M1 recovery loop 1 reproduced the focused failure. Root cause was
  cross-layer drift: Schema/state used `FAILURE_AWARE_ADJUDICATION_IN_PROGRESS`, while the
  fault test had an independent closed allowlist and WORKFLOW/rules/transition invariants were not
  registered. DEC-0032 retains the distinct status, makes Schema the legal-enum/invariant truth,
  and leaves transition edges in workflow rules. Focused test passed (`1 passed`), new contract
  tests passed (`11 passed`), and contract fixtures passed (`45 valid`, `35 invalid rejected`).
- `2026-09-02T02:05:00+08:00`: M1 full-suite verification exposed recovery loop 2: editing the
  Phase 002D freeze-bound global `rules/workflow_rules.yaml` correctly made the historical
  sufficiency result `STALE` (`3 failed`, `543 passed`, `1 skipped`). The global file was restored
  byte-for-byte; R1 now owns its migration edge in versioned
  `rules/phase002d_r1_workflow_rules.yaml`, which is included in the new R1 freeze.
- `2026-09-02T02:08:52+08:00`: recovery loop 2 passed the old Phase 002D freeze and sufficiency
  checks, R1 freeze write/check (`4a03c2d8...1c85`), focused test (`1 passed`), full fault file
  (`6 passed`), unit/integration/fault suite (`546 passed`, `1 skipped`), contracts (`45/45` valid,
  `35/35` invalid rejected), status render/check, strict validation (`0 errors`, `0 warnings`), full
  CI (`546 passed`, `1 skipped`) and `git diff --check`.
- `2026-09-02T02:27:21+08:00`: M2 classified all 28 frozen attempts exactly once: 9 eligible
  successes, 9 valid-output oracle failures, 7 terminal policy failures, 1 infrastructure-censored
  attempt and 2 harness-censored attempts. Six `HARD-FAIL-003` flags and all four retries remain
  explicit. The 24-slot matrix accounts for every attempt: 9 resolved successes, 14 resolved
  terminal negatives and 1 harness-censored slot; best-of-N is prohibited.
- `2026-09-02T02:27:21+08:00`: M3 separated the evidence scopes. Quality remains insufficient at
  2/4 balanced cases and repeat depth 1/2; outcome completeness is 23/24 slots across 3 fully
  resolved cases at depth 2; reliability retains all 28 attempts with retry burden 4. The retry
  audit found one primary-eligible result after retry but no oracle-PASS success after retry.
- M2/M3 repair loop 1 fixed 13 Ruff `E501` findings by formatting only; lint then passed. Repair
  loop 2 corrected a test expectation that had confused the 9 oracle failures with the frozen set
  of 6 `HARD-FAIL-003` attempts; the rerun passed 132 tests. Contracts now validate 50 positive
  fixtures and reject 40 negative fixtures; both historical and R1 freezes pass.
- `2026-09-02T03:06:39+08:00`: M4 completed five independent native, read-only first-round audits.
  Two returned `PASS`; three returned `RETEST_REQUIRED` with 10 serious findings. All 10 were
  converted to the existing test-request/test-evidence contracts and closed by 25 passing
  deterministic nodes. The frozen audit bundles and original verdicts remain immutable; seven
  remediated paths are explicitly test-bound rather than silently regenerated.
- M4 repair loop 1 found that exact cost reconciliation had used all-attempt oracle counts while
  the frozen cost contract uses primary-eligible oracle counts. The derivation was corrected and
  now exactly reconciles 28 attempts, 6228.480778 seconds, 5,726,854 input tokens, 272,461 output
  tokens, four retries, eight failed completions, one infrastructure failure and 9/9 eligible
  oracle PASS/FAIL records. Historical queue order `7,35,37,8` and two post-terminal retries remain
  explicit deviations; terminal-first slot resolution is fail-closed.
- `2026-09-02T03:06:39+08:00`: M5/M6 rejected generic supplemental runs. The sole censored slot is
  harness-censored and semantic equivalence is `NOT_ESTABLISHED`; authorization, budget and actual
  starts are all zero. Pre-audit passes, the original budget is unchanged, and every frozen
  protocol-field mutation requires `NEW_PROTOCOL_COHORT_REQUIRED`.
- `2026-09-02T03:15:16+08:00`: M7 generated all seven hash-bound decisions through the canonical
  automated-decision contract plus the R1 scope envelope. Failure semantics and slot resolution are
  `POLICY_ONLY`; supplemental runs are rejected; quality and architecture remain
  `EVIDENCE_INSUFFICIENT`; observed reliability is accepted as `RELIABILITY_ONLY`; four mechanisms
  are accepted as `SPECIFICATION_ONLY`. No architecture, implementation, integration or Phase 003
  claim is made. The formal state remains in progress until the independent Decision Auditor and
  five-variant replay pass.

Next: commit and remotely verify the seven formal decisions, then run the independent native
failure-aware Decision Auditor against the frozen post-decision bundle.
