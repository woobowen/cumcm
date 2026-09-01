# PLAN-0002D — Controlled Evidence Expansion

Status: `REMOTE_DELIVERED_INCOMPLETE`
Phase: `PHASE-EVIDENCE-EXPANSION-002D`
Owner: main agent
Started: `2026-09-01T17:58:44+08:00`
Branch: `feat/evidence-expansion-002d`
Base commit: `8dd43cad3bac58ac25fdbb0d412d894d428472ae`

## 1. Purpose and authorization

Expand the frozen Phase 002 comparison with cohort-compatible, fresh, independent Codex runs until
the unchanged minimum of four balanced cases at repeat depth two is met or a frozen stop condition
fires. The phase is authorized only by the audited Phase 002C decisions, especially
`DECISION-EVIDENCE-SUFFICIENCY-002C`, Decision Audit `PASS`, and stable offline replay. This phase
optimizes the Skill workflow, rules, contracts, runner, deterministic evidence and adjudication; it
does not train or fine-tune a foundation model.

The verified starting state is Phase 002C `AUTOMATED_ADJUDICATION_COMPLETE`, with 13 eligible
primary records, 5 recovery-affected exclusions, balanced cases `CASE-001` and `CASE-006`, repeat
depth 1, `selected_architecture=null`, no accepted component specification, `base_selected=false`,
`third_party_integrated=false`, and the formal Skill at `0.1.0-foundation`/`SCAFFOLD_ONLY`.

## 2. Scope and targets

- Freeze every Phase 002, 002A, 002B and 002C dependency and preserve those result directories.
- Close the Phase 002C arbitrary-`LOW_*` direct-adoption risk predicate before scored runs.
- Select exactly one model/reasoning cohort through machine evidence and a compact pilot.
- Freeze one transport profile, one output contract, one prompt template and one execution budget.
- Run the three existing arms in a fixed-seed blocked randomized schedule on primary cases
  `CASE-001`, `CASE-002`, `CASE-004`, and `CASE-006`.
- Retain every successful, failed, excluded and not-run attempt append-only.
- Admit only Schema-valid, oracle-passing, process-verified fresh sessions as primary evidence.
- Stop scored comparison immediately when minima pass or any hard stop condition fires.
- After sufficiency, run independent native read-only audits, deterministic BLOCKER tests,
  automated decisions, Decision Audit and offline replay.
- Deliver validated atomic commits to the task branch and keep Draft PR #3 open and Draft.

## 3. Non-goals and prohibitions

Do not train/fine-tune a model; use OpenAI API keys, REST endpoints or API billing; install, execute,
copy or integrate third-party Skills/code/dependencies; read historical contest answers/papers;
search for benchmark answers; mutate Phase 002–002C evidence; promote recovery/resume/parser repair;
mix models or reasoning settings; use Agent votes; weaken thresholds; tune cases/oracles/schedule to
observed arm performance; force an acceptance; modify/push `main`; merge or ready the Draft PR; or
enter Phase 003. The formal Skill remains `SCAFFOLD_ONLY` throughout Phase 002D.

## 4. Historical-evidence protection and input freeze

`evals/results/phase-002/`, `phase-002a/`, `phase-002b/`, and `phase-002c/` are immutable. The Phase
002D manifest binds historical freeze/recovery/decision/audit/replay hashes; case, fixture, rubric,
package, policy, Schema, runner, scorer and oracle hashes; subject commit; Codex version; auth mode;
transport profile; and cohort policy. `scripts/freeze_phase002d_inputs.py --check` is read-only and
fails closed as `INPUT_FREEZE_BROKEN`. A freeze failure marks downstream work `STALE`, blocks new
experiments and decisions, and never repairs an old file.

## 5. Risk predicate compatibility repair

Direct-adoption risk levels use the closed enum `LOW_CONFIRMED`, `LOW_REVIEWED`, `MEDIUM`, `HIGH`,
`BLOCKER`, `UNKNOWN`, `UNVERIFIED`. Only the two explicit LOW values are safe. Empty, mixed-case,
unknown and prefix-extended values fail closed. The repair adds Schema fixtures and fault tests and
replays Phase 002C into a new Phase 002D compatibility record without rewriting the historical
decisions. Existing HANDSOMEZR and YUSHUI whole-package rejection must remain invariant.

## 6. Cohort modes and compatibility Gate

`MODEL_COHORT_COMPATIBILITY_GATE` compares model identifier, reasoning, prompt template, output
Schema, case fixture, arm package, sandbox, network/MCP policy, scorer, oracle, task input, auth,
transport and Codex CLI compatibility. Model/reasoning and every content/safety hash are hard-equal.
CLI major changes are incompatible; minor/patch changes require a compatibility pilot.

- `CONTINUATION_COHORT` is permitted only when the historical `gpt-5.4`/`medium` cohort is actually
  available and every compatibility check passes. Exact-match Phase 002 `PRIMARY_COMPLETE`
  non-recovery records may then contribute; the shortfall calculator, not prose, defines targets.
- `NEW_MODEL_COHORT` is mandatory if any hard equality or pilot fails. Phase 002 becomes
  `CROSS_MODEL_EXPLORATORY_GAP_EVIDENCE` only. The target is 4 cases × 3 arms × 2 fresh repeats =
  24 successful eligible primary runs in one new model/reasoning cohort.

The selected model is uniform for all arms and recorded in ADR-0024. It may not change mid-cohort;
unavailability stops the cohort rather than silently migrating it.

## 7. Calibration pilot and transport profile

`CALIBRATION-PILOT-002D-001` uses the selected real model, formal runner plumbing, a compact
deterministic-oracle task, small output Schema, fresh ephemeral session, workspace-write sandbox,
no web/MCP/third-party code/history and no resume. Start with `PROXY_INHERITED`. Only after an
explicit TLS/connect/WebSocket/fallback failure may one independent process-local
`NO_PROXY_PROCESS_ONLY` attempt run. The first successful profile is frozen for every scored run;
two failed fresh starts yield `EVIDENCE_EXPANSION_INFRASTRUCTURE_BLOCKED`.

The pilot records completion, model/reasoning/profile, Schema, observable token fields, duration,
files, command events, failure class, retry and result/raw hashes. It never counts as primary,
repeat or comparative evidence.

## 8. Budget formula and limits

Freeze budget only after a successful pilot and before the first scored attempt. The calculation
uses cohort mode, code-computed target successes, historical success/token/time distributions, the
pilot, per-cell attempt cap and infrastructure policy. The record includes formulas and machine
inputs. Absolute limits are: continuation ≤28 attempts; new cohort ≤48; each cell ≤3 fresh attempts;
fresh retries per cell ≤2; same-cell consecutive infrastructure failures ≤2; global consecutive
infrastructure failures ≤3; estimated input ≤10,000,000 tokens; estimated wall time ≤14,400 seconds;
concurrency 1 unless independently proven safe. Unknown tokens remain `UNKNOWN`; attempts/time are
hard limits. ChatGPT-managed authentication has `monetary_cost=UNKNOWN`; API prices are not used.
The budget cannot be loosened after arm results are visible.

## 9. Arm definitions and anonymity

- `NO_PROJECT_MODELING_SKILL`: ordinary Codex, no project or third-party Skill.
- `HANDSOMEZR_SANITIZED_INSTRUCTION_ONLY`: the already frozen safe text-only package.
- `YUSHUI_SANITIZED_INSTRUCTION_ONLY_WITH_LICENSE_BLOCKER`: the frozen safe text-only package with
  `UNKNOWN_NO_LICENSE`; performance cannot remove the blocker.

All runs share model, reasoning, prompt, case, input hash, Schema, timeout, sandbox, transport,
network/MCP policy, oracle, scorer and budget. Only the arm instruction layer differs. Tracked
records use anonymous labels; first-round semantic reviewers do not receive identity mappings.

## 10. Independent repeat and primary eligibility

A repeat is a new non-resumed Codex session started from the frozen input. It must complete with a
legal exit, valid Schema, matching cohort/content/policy hashes, no recovery, no hard/safety/input
failure, an executed deterministic oracle and verifiable process evidence. Oracle PASS/FAIL remains
outcome evidence and is never used to select observations into or out of the primary sample.
Exact-session resume, transport
continuation, publication/parser/raw-output recovery, hand-repaired JSON, partial/failed output,
different cohort/profile, manual fill and old cross-model evidence are excluded. A fresh retry can
be primary if it independently passes; its predecessor failure remains immutable.

## 11. Blocked randomized schedule

Each block is `case_id × repeat_id`. A fixed seed generated before scored work randomizes the three
anonymous arms within each block. The frozen schedule records cohort, cases, repeats, order,
attempt IDs, retry queue, hash, generation time and deviation policy. One failure does not trigger
immediate repeated retries: complete the block, then process the frozen retry queue. No arm-first
ordering or post-result queue edits are allowed.

## 12. Runner, attempts and checkpoints

`scripts/run_phase002d_expansion.py` builds a fresh temporary no-remote Git repository per attempt,
copies only compact case inputs, frozen arm instruction and output Schema, scrubs sensitive env
names, uses ChatGPT-managed `codex exec --ephemeral`, disables web/MCP by policy and observable
trace audit, freezes model/reasoning/timeout/profile, stores raw trace/stderr/output only under
ignored cache, and tracks only structured output, summaries and hashes. It checks input mutation,
Schema, oracle, process evidence, robustness and primary eligibility, then atomically appends the
attempt ledger/checkpoint. Existing successful cells are never repeated; failures are never
overwritten; budget/minima/hard stops are enforced before every start.

Each attempt binds cohort/case/anonymous arm/repeat/block/order/freshness/profile/model/config and
all prompt/input/fixture/package/Schema/oracle/scorer/runner hashes; times/exit/status/failure/retry;
observable token fields; files/input mutation; verification results; exclusions; result/raw/stderr
hashes. Tracked data never contains raw trace, hidden reasoning, credentials, exact session IDs,
auth files, private paths or full third-party instructions.

## 13. Evidence and scoring

Maintain separate `STRUCTURED_COVERAGE_SCORE`, `ORACLE_CORRECTNESS`, `PROCESS_EVIDENCE`,
`ROBUSTNESS_EVIDENCE`, and conditional `SEMANTIC_REVIEW`. Coverage is field presence only. Oracle
uses deterministic injected truth/numerics/feasibility/dependency/source/unit/boundary checks.
Process evidence uses actual commands/files/hashes/splits/failures/protocol. Robustness uses
perturbations and repeat stability. Semantic E0/E1 opinions never replace E1/E2 machine evidence.
The historical 70/30 score is not a correctness or acceptance Gate.

## 14. Batches and recovery

Batch 0 is the pilot. Batch 1 is one complete case/repeat block (three arms). Verify profile,
cohort, all hashes, Schema/oracle/process/eligibility, usage, fairness, schedule and budget. Later
batches start at most 3–6 attempts. After every batch atomically write checkpoint/ledger; run status;
recompute success/failure/balanced/repeat/budget/hard-gate/cohort/schedule; run focused tests;
inspect/stage explicit paths; commit and push. On interruption, re-read the startup truth chain and
resume the earliest frozen scheduled cell; never repeat a successful cell. Near execution limits,
record exact checkpoint and resume command, validate, commit and push before handing off.

## 15. Stop conditions

Stop new scored runs when minima pass; any mandatory hard Gate/freeze/input/cohort/reasoning/
profile/scorer/oracle/schedule/Schema invariant fails; contamination, network/MCP or input mutation
occurs; budget/attempt/token/time/quota/auth limits fire; a cell reaches two consecutive
infrastructure failures; global infrastructure failures reach three; or predicted absolute cost is
exceeded. Do not convert failure to zero, relax a threshold, delete an attempt or use recovery to
fill a cell. Minima satisfaction immediately locks comparative execution.

## 16. Sufficiency, audits and decisions

After every batch run the unchanged `PRE_ADJUDICATION_EVIDENCE_GATE`: balanced cases ≥4 and
independent repeats ≥2 in one compatible cohort with equal task/policy/model hashes and passing hard
Gates. Mode A may use exact compatible historical primary records; Mode B uses only Phase 002D new
cohort primary records. Recovery, failed, superseded, partial, NOT_RUN and cross-model records never
fill minima.

Only after `SUFFICIENT` launch four independent native read-only, identity-blind, non-voting first
round roles: correctness, scientific validity, engineering reproducibility, and dissent/cost. They
receive no peer outputs and emit Schema-valid evidence-linked JSON. Every testable BLOCKER becomes
an executed registered test; non-testable assertions remain uncertainty. Then generate:

- `DECISION-EVIDENCE-SUFFICIENCY-002D`
- `DECISION-DIRECT-UPSTREAM-ADOPTION-002D`
- `DECISION-ARCHITECTURE-002D`
- `DECISION-RECOVERY-POLICY-002D`
- `DECISION-COMPONENT-READINESS-002D`

Run the separate native `expanded_decision_auditor` only after frozen decisions/replay inputs. A
technical terminal requires Auditor `PASS`; no majority vote or human technical override exists.
Offline replay must be stable under label swap, order permutation and recovery-presence exclusion.

## 17. Decision boundaries

Whole-package direct adoption retains license, contamination, security, second-state,
second-orchestrator, scope and full-runtime hard Gates; sanitized performance cannot override them.
Architecture may select `NATIVE_SINGLE_SKILL_CLEAN_ROOM`, `RETAIN_SCAFFOLD_ONLY`, reject, abstain or
remain insufficient. Clean-room acceptance additionally needs at least three repeated E1/E2 gaps,
native acceptance tests, no copied/unknown-license content, one state/orchestrator, resolved Dissent,
stable replay and measurable benefit over the simplest scaffold with recorded maintenance cost.

Recovery scope is at most `POLICY_ONLY` for diagnosis/gap/test/recovery engineering and never ranks
or advances. Each of the four components is independently eligible only for `SPECIFICATION_ONLY`
after repeated multi-case/repeat evidence, native tests, clean-room feasibility, measurable benefit,
cost evidence, no Dissent BLOCKER and Auditor PASS. Primary cases do not fabricate new CASE-003/005
evidence; any secondary test needs a separate predeclared freeze after the primary cohort.

## 18. State transitions

At start set Phase 002D/`IN_PROGRESS`/`EVIDENCE_EXPANSION_IN_PROGRESS`, clear phase eligibility and
preserve null architecture/empty components/false base and integration/scaffold capability. Update
cohort/model/reasoning/profile, target/attempt/success/failure/balanced/repeat/budget/batch/infra from
machine records. Pilot infrastructure failure ends as `EVIDENCE_EXPANSION_INFRASTRUCTURE_BLOCKED`;
budget/minima shortfall ends as `EVIDENCE_EXPANSION_INCOMPLETE` with Phase 002D resumable; sufficient
evidence but incomplete audits ends `AUTOMATED_ADJUDICATION_INCOMPLETE`; complete audit/replay routes
only according to decisions. Even if Phase 003 becomes allowed, this task does not execute it and
the Skill stays scaffold-only until a later implementation phase.

## 19. Milestones and acceptance

1. **M1 start — COMPLETE** — preflight/baseline pass; archive completed 002C plan; create this plan; transition
   state; strict risk enum and Phase 002C compatibility replay pass; focused/full checks; atomic
   commit and push.
2. **M2 freeze/cohort — COMPLETE** — Phase 002D input freeze verifies; local model availability and compatibility
   Gate select a mode/model without a scored start; ADR-0024/25/28/29 and target calculator pass;
   atomic commit and push.
3. **M3 pilot/budget — COMPLETE** — fresh pilot succeeds within two starts; one profile and replayable formula
   budget freeze before scored work; ADR-0027; focused checks; atomic commit and push.
4. **M4 schedule/runner — COMPLETE** — fixed schedule, runner, append-only attempts,
   checkpoint/status, mocks and fault injection passed without a real scored start; ADR-0026;
   business commit `fe90c32` is remotely delivered and verified.
5. **M5 Batch 1 — COMPLETE** — one complete block was attempted in frozen order; all three records
   are primary eligible and retained; checkpoint/cost/score-audit/status passed; business commit
   `dcff679` is remotely delivered and verified.
6. **M6 later batches — COMPLETE/REMOTE TERMINAL** — each bounded batch is verified/committed/pushed; the
   final A03 is excluded by HARD-FAIL-003 and cumulative elapsed crosses the frozen limit. Runner
   is STOPPED with `ELAPSED_BUDGET_REACHED`; Batch 7 is remotely delivered.
7. **M7 sufficiency — COMPLETE/REMOTE INSUFFICIENT** — formal machine record reports 18 eligible
   records, three balanced cases, one independent repeat, intact cohort/input/hard Gates and
   `INSUFFICIENT`; it is remotely delivered.
8. **M8 audits/decisions — LOCKED/NOT RUN** — quantitative minima did not pass, so native semantic
   Subagents, derived BLOCKER tests, Phase 002D automated decisions and Decision Auditor are
   prohibited by the frozen ordering.
9. **M9 replay/route — PARTIAL ROUTE ONLY** — decision replay and label/order variants are not
   applicable without M8 decisions; deterministic state route is `EVIDENCE_EXPANSION_INCOMPLETE`
   with only the same Phase 002D allowed next.
10. **M10 acceptance/delivery — REMOTE DELIVERED/INCOMPLETE** — required documents, reports,
    contracts and ledgers are current; 535 tests pass with one expected skip; strict has zero
    errors/warnings. Business commit `fd0523bc5caa0a0e2c50d5f75fd9b475fd57a235` matches the
    remote task branch and its `CI/offline-validation` completed successfully. Draft PR #3 remains
    OPEN/DRAFT. The task delivery is complete while the technical route remains fail-closed as
    `EVIDENCE_EXPANSION_INCOMPLETE`.

## 20. Validation commands

Run the prompt-mandated Phase 002D checks plus: Ruff lint/format, full pytest, instruction/Skill/
contract/upstream/leakage/secret checks, Phase 002 and 002B freezes, 002D freeze/cohort/pilot/budget/
schedule/runner-status/score/sufficiency/adjudication/audit/replay/report checks, status generation and
check, strict repository validation, `bash scripts/ci.sh`, `git diff --check`, and final branch/status.
The tracked command ledger records command, exit, duration, execution type, cohort/model/profile,
attempt, result/blocker, evidence hash and observable token usage; real Codex, native Subagent and
offline/mock execution remain distinct.

## 21. Cost reporting

Report attempts/successes/failures/rate, all observable input/cached/output/reasoning tokens,
durations/retries/infrastructure/operator/queue/CPU/replay/storage/tracked-files/LOC/maintenance
surface; cost per primary success, balanced case and repeat; arm averages; clean-room engineering
versus retain-scaffold cost. Unobservable fields remain `UNKNOWN`; monetary cost remains `UNKNOWN`.
Correctness and hard Gates dominate cost.

## 22. Git, Draft PR and rollback

Before each commit inspect status, whitespace, unstaged/staged stat and full diff; stage explicit
paths only; run focused validation; inspect the commit. Push normally to
`feat/evidence-expansion-002d` after each key batch. TLS failures receive at most five bounded
retries; one command-local no-proxy control is allowed without persistent configuration. Never
force-push/rebase/merge/modify `main`. Create Draft PR #3 after the first deterministic business
commit if absent; keep it OPEN/DRAFT and update its generated body from machine records.

Rollback published work only with scoped `git revert`; never reset/clean/rewrite historical
evidence. Unpublished generated Phase 002D artifacts may be superseded append-only through explicit
new records and hashes. Any change to the frozen design updates this plan with factual rationale,
affected hashes and acceptance changes before further scored work.

## 23. Progress and findings

- `2026-09-01T17:52:49+08:00`: preflight passed. Root/branch/remote were correct; worktree clean;
  HEAD, origin/main, task branch and merge-base were `8dd43cad...`; PR #2 was merged; no task-branch
  PR was open; Codex CLI was `0.147.0` with ChatGPT authentication.
- `2026-09-01T17:53:30+08:00`: baseline `bash scripts/ci.sh` passed with 378 tests, strict zero
  errors/warnings and exactly one formal Skill.
- `2026-09-01T18:07:00+08:00`: M1 delivered commits `07b0247` and `a27e10f` to the task branch;
  remote SHA matched and Draft PR #3 was created OPEN/DRAFT.
- `2026-09-01T18:14:55+08:00`: the local read-only App Server catalog omitted historical
  `gpt-5.4` and exposed `gpt-5.6-sol` with `medium`; zero models were started. The machine Gate
  selected `NEW_MODEL_COHORT`, prohibited old-primary reuse, recomputed the inactive MODE A
  shortfall as 14 and set the active target to 24. Input freeze `4846e25e...` and cohort hash
  `f1ad3696...` passed. Official web documentation was not used as local-account evidence.
- `2026-09-01T18:29:38+08:00`: the compact real pilot used two fresh starts and no resume. Attempt
  1 was rejected before model output because the runner Schema lacked explicit property types; its
  original attempt hash was preserved and an evidence-hash correction recorded. Attempt 2 passed
  Schema, deterministic oracle and input-integrity checks in 21.204297 seconds on
  `PROXY_INHERITED`, observing 41,092 input and 397 output tokens. The final input freeze is
  `fb0c1122...`, cohort `db663586...`, and formula budget `389c24e9...`; expected input is 4,762,659
  tokens and expected elapsed time 4,590 seconds, below absolute hard limits.
- `2026-09-01T18:51:53+08:00`: M4 deterministic implementation passed 49 focused tests and all
  43 Schema positive/33 negative fixtures. Schedule `5d0351aa...` freezes eight blocks, 24 primary
  attempts and 48 retry slots. Input freeze `ddcb409e...` binds the independent runner, ledger,
  eligibility, oracle, coverage scorer and contracts. Runner `--check`, `--status` and dry-run pass
  with zero scored attempts; the first block is CASE-001/R1 in ARM-C, ARM-A, ARM-B order.
- `2026-09-01T18:56:09+08:00`: M4 business commit
  `fe90c320900883b2035afaf8a7cae089b800fd71` was pushed normally and verified byte-for-byte at
  `origin/feat/evidence-expansion-002d`. Draft PR #3 remains OPEN/DRAFT against `main`.
- `2026-09-01T19:13:42+08:00`: M5 Batch 1 completed the frozen CASE-001/R1 block in ARM-C,
  ARM-A, ARM-B order. All three fresh attempts completed Schema-valid with process E2, no hard
  failure, no recovery and primary eligibility PASS. Oracle outcomes were FAIL, PASS, FAIL in
  schedule order and remain separate from eligibility. Total observed input/output tokens were
  532,989/27,845 and elapsed time was 633.072039 seconds. Cost hash is `2afad1f7...`; the append-only
  coverage-binding audit `1c24743d...` preserves one non-authoritative ARM-A coverage false positive
  and excludes coverage hard-failure fields from formal Gates.
- `2026-09-01T19:18:12+08:00`: M5 business commit
  `dcff6790cfc140ebf40a13e0094e08e59fbcba1c` was pushed normally and verified at the task-branch
  remote ref. Draft PR #3 remains OPEN/DRAFT.
- `2026-09-01T19:40:07+08:00`: M6 Batch 2 completed two frozen blocks and six fresh starts.
  Five new records are primary eligible; CASE-001/ARM-A/R2 is excluded for authoritative
  HARD-FAIL-003 after claiming `.harness/*` files that are not publishable attempt outputs. All six
  oracle checks and all process checks passed. Cumulative attempts/eligible are 9/8, balanced cases
  are CASE-001 and CASE-002, cost is `e065e64f...`, and score audit `88ffff41...` passes with two
  isolated coverage-binding limitations. No retry ran and no later block started.
- `2026-09-01T19:42:09+08:00`: Batch 2 business commit
  `81b6b798bc95e7087ef3ccae4931e6bb1c70b47b` was pushed and verified at the task-branch ref.
- `2026-09-01T20:07:47+08:00`: M6 Batch 3 completed CASE-002/R2 and CASE-004/R1 in frozen order.
  All six new records are primary eligible; CASE-002 now has two complete repeats and CASE-004 has
  one. Cumulative attempts/eligible are 15/14, balanced cases are CASE-001/002/004, observed
  input/output are 2,739,660/147,675, and elapsed is 3,192.763951 seconds. Cost `37657847...` and
  authoritative score audit `1be00ad2...` pass; original oracle outcomes include three CASE-004
  failures and remain retained.
- `2026-09-01T20:11:45+08:00`: Batch 3 business commit
  `d3121d6e06fc0b29c9bd19206f21396cb4cba245` was pushed normally and verified byte-for-byte at the
  task-branch remote ref. Draft PR #3 remains OPEN/DRAFT.
- `2026-09-01T20:43:46+08:00`: M6 Batch 4 completed CASE-004/R2 and CASE-006/R1 in frozen order.
  Three of six new records are eligible; three Schema-invalid `POLICY_VIOLATION` records are
  retained as exclusions, including two authoritative HARD-FAIL-003 records. No infrastructure
  failure or retry occurred. Cumulative attempts/eligible are 21/17, oracle PASS/FAIL are 9/8, and
  remaining elapsed budget is 1,347.669194 seconds. Score audit `9126fbb0...` and cost
  `30538e0d...` pass. The non-frozen score auditor now treats missing observations as explicitly
  noncomparable instead of raising; 58 focused tests pass with one expected skip.
- `2026-09-01T20:46:12+08:00`: Batch 4 business commit
  `a6d85b5234d1e2f09587da4145a4cedc23c86867` was pushed normally and verified byte-for-byte at the
  task-branch remote ref. Draft PR #3 remains OPEN/DRAFT.
- `2026-09-01T20:55:27+08:00`: M6 Batch 5 completed the final primary block CASE-006/R2 in A/B/C
  order. All three Schema-invalid `POLICY_VIOLATION` records are retained as exclusions; ARM-A also
  has authoritative HARD-FAIL-003. Cumulative attempts/eligible are 24/17 with six completion
  failures, no infrastructure failures and 891.836500 seconds remaining. The primary queue is
  exhausted; retry A02 for CASE-001/ARM-A/R2 is next. Cost `0f0e0f56...`, score audit
  `18407b4d...`, runner check and 58 focused tests pass with one expected skip.
- `2026-09-01T20:57:01+08:00`: Batch 5 business commit
  `bb5b48a1b016242bc421ee38d4e613dcb35dc55f` was pushed normally and verified byte-for-byte at the
  task-branch remote ref. Draft PR #3 remains OPEN/DRAFT.
- `2026-09-01T21:09:59+08:00`: M6 retry Batch 6 ran three frozen A02 slots. CASE-004/ARM-A/R2 is
  eligible with oracle FAIL; CASE-001/ARM-A/R2 has an HTTPS fallback disconnect and authoritative
  HARD-FAIL-003; CASE-006/ARM-A/R1 is a Schema-invalid policy exclusion. Cumulative attempts/eligible
  are 27/18; elapsed is 5,988.297082 seconds with 208.702918 remaining. Cost `4ac9dfc5...`, score
  audit `86b47288...`, and runner check pass. Minima still miss six eligible records.
- `2026-09-01T21:11:44+08:00`: Retry Batch 6 business commit
  `8efe3f2fa790a27861094d944484ded0f4fc2f24` was pushed normally and verified byte-for-byte at the
  task-branch remote ref. Draft PR #3 remains OPEN/DRAFT.
- `2026-09-01T21:16:58+08:00`: M6 terminal Batch 7 ran the final CASE-001/ARM-A/R2/A03. It
  completed Schema-valid with process PASS but is excluded by authoritative HARD-FAIL-003 because
  no publishable files were written. Cumulative attempts/eligible are 28/18; balanced cases remain
  three and repeat depth zero. Elapsed reached 6,228.480778 seconds, so runner status is STOPPED
  with `ELAPSED_BUDGET_REACHED`. Cost `a9b97f47...` and score audit `5b84b5a2...` pass. No further
  model start or native Subagent audit is allowed.
- `2026-09-01T21:18:32+08:00`: Terminal Batch 7 business commit
  `e935da9fd18c0567c99214c36c1658a8d05e0508` was pushed normally and verified byte-for-byte at the
  task-branch remote ref. Draft PR #3 remains OPEN/DRAFT.
- `2026-09-01T21:24:08+08:00`: M7 deterministic sufficiency record passes the reused Schema and
  hash checks with result `INSUFFICIENT`: 18 eligible primary records, three balanced cases and one
  independent repeat among balanced cells against frozen minima four/two. Task-input hashes,
  cohort, input freeze and eligible hard Gates pass. Semantic Subagents and ranking remain locked;
  record hash is `cf9c9c98...`. M10 audit also identified five required Phase 002D policy documents
  and the `0.2.4-evidence-expansion` version bump as outstanding acceptance work.
- `2026-09-01T21:27:22+08:00`: M7 business commit
  `9762cf547e07675a5c16acc9e223d1c1b448d010` was pushed normally and verified byte-for-byte at the
  task-branch remote ref. Draft PR #3 remains OPEN/DRAFT.
- `2026-09-01T21:37:46+08:00`: M10 local acceptance added the Phase 002D precondition-lock
  contract, deterministic closure/route checks, five required policy documents, version
  `0.2.4-evidence-expansion`, all required final reports and a 30-start command ledger. The generated
  reports explicitly record zero native Subagents and zero Phase 002D decisions. Full CI passes 535
  tests with one expected skip; 45 valid Schemas pass and 35 invalid fixtures are rejected; strict
  reports zero errors/warnings. PR #3 is OPEN/DRAFT and its previous remote head CI was SUCCESS.

## 24. Current next step

Commit and push M10 business content, verify remote CI/SHA, then record the final delivery receipt.
