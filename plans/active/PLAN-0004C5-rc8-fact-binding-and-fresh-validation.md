# PLAN-0004C5 — RC8 fact binding and fresh C Validation

Status: `IN_PROGRESS`
Phase: `PHASE-SKILL-C-TARGET-BATCH-REPAIR-004C5`
Owner: main agent / `modeling_orchestrator`
Branch: `feat/phase004c5-p0-01-finalization-hf22-repro`
Starting commit: `17f109cadc8524c285af6a50776e6c3decb8b3e8`
Started: `2026-09-08T17:46:50Z`; absolute deadline: `2026-09-09T01:46:50Z`.

## Purpose and authorized scope

Execute the user-supplied `CUMCM_PR12_RC8_RELEASE_AND_GENERALIZATION_PLAN.md` M0–M5.
The explicit authorization supersedes previous takeover-only, pause and single-P0 restrictions.
Preserve the 004C4 terminal failure, RC7 release, every old Validation/first-run and Development v5.
Continue the existing PR; no ready/merge, main push, history rewrite, paid API, global changes,
2025 reservation, benchmark vault or current contest input access. One formal Skill and one formal
project-state source remain mandatory. Python distribution 0.2.3 is distinct from competition
Project 0.3.0-competition-rc8 / Skill 0.2.0-competition-rc8 candidate labels.

Environment: inherited Linux/Bash, full Git history, existing `.venv/bin/python`; no reinstall or
parallel runtime. All new numerical work belongs to new case-owned directories. The main agent
alone writes shared implementation, state, registry, decisions and Git. Native reviewers are
read-only. Fresh workers may write only their assigned case-owned artifacts and ignored workspace.
No more than two concurrent units including the main agent. Native agents do not spawn agents.
The main agent grants one Development worker conflict-free ownership of
`evals/results/phase-004c5/development/v6/2021/code/` and its local implementation notes only.
That worker may implement and test the case-owned scientific repair; it may not write shared code,
formal state, decisions, other cases, or Git. Its work is implementation, not independent acceptance.
After the 2021 worker finishes, the same single worker slot may own
`evals/results/phase-004c5/development/v6/2022/code/` and `2022/implementation_notes.md` under
the identical restrictions. This is serial delegation; no third concurrent unit is permitted.

## Milestones and acceptance

| Milestone | Target elapsed | Required evidence |
|---|---|---|
| M0 | 0–0.5 h | Short inheritance check; legal state/plan; candidate identity and preserved history |
| M1 | 0.5–2 h | Neutral expectations frozen before actual CLI/controller fact-binding repair |
| M2 | 2–3 h | New 2021/2022 captured Development comparisons and independent scientific checks |
| M3 | 3–3.5 h | Bound implementation subject; native audit; candidate/activation checks; remote freeze |
| M4 | 3.5–7 h | At least first fresh case actually solved and terminally frozen; attempt second if budget permits |
| M5 | 7–8 h | Terminal audit/report; full CI; atomic delivery; Draft PR and remote SHA evidence |

M1 separates original source class, output-generation method and supported Claim scope. Case
adapters propose requirements; validators consume actual source/data/Run/output/metric and
independent checks. Descriptive, conditional simulation and feasible optimization have legitimate
non-predictive paths. A renamed predictive Claim cannot evade its final-evaluation requirement.
Partial or contradicted evidence cannot produce whole-problem scientific completion. Inherited P0
Final/HF22 behavior is verified and preserved; only reproduced remaining gaps justify changes.

M2 preregisters three candidates and one seed per case, at most six additional captured attempts
per case for bounded repairs or necessary comparisons, each at most 900 seconds. All attempts,
failures and selections remain recorded. Baseline must actually run under matching conditions to
claim improvement. No Final test access for these Development regressions. Independent Python
checks must recompute quantities without importing the model's verification helper. Sources must
change a specific model/experiment decision. Case recipes remain case-owned.

M3 freezes candidate version surfaces before its implementation subject commit. Existing checker
mechanisms gain explicit subject/version handling, preserving old valid and invalid histories.
Candidate acceptance precedes activation. Activation cannot change the accepted implementation,
shared code/rules/contracts or runtime dependencies. Manifests and delivery receipts reference
existing subjects and never require their own commit SHA. Qualification scope is research/Validation
only; team compliance remains `NOT_RUN`, and no contest release or generalization claim is made.

## Fresh-case preregistration before any new input or numeric result

Planned denominator is two: first 2016 C, second 2015 C; 2014 C substitutes only for official input
unavailability/corruption/missing required attachments or pre-result contamination. Difficulty,
external-data requirements and negative results never permit replacement. Inputs remain unopened
until candidate acceptance and remote freeze. Answers stay sealed throughout; model-prior exposure
is unverifiable. Raw official inputs are hash-registered, immutable and ignored.

Execution is serial: one fresh worker plus the main orchestrator, satisfying the two-unit ceiling.
Each full episode has at most 7,200 seconds including preparation, preregistration, execution,
completion and review. Start the second only if at least 8,100 seconds remain before the task
deadline; otherwise record `NOT_RUN_BUDGET` against the unchanged denominator. Earlier genuine
completion may release unused time; no artificial waiting or truncated budget to inflate results.
The fresh worker uses `fork_turns=none` and receives only the frozen Skill, generic instructions and
its own official inputs. This is tool-level context isolation and policy-based filesystem isolation,
not an OS sandbox. It cannot read developer postmortems, peer outputs or historical answers.

Three freezes are distinct: shared Skill/environment/rubric before input; case pre-run protocol
before major numeric results (committed and remotely verified); final model/config/selected Run
before final evaluation. All 14 stages are attempted with appropriate metrics and evidence. Within
the predeclared case budget normal debugging and model comparison are permitted, with every
attempt preserved. No Skill mutation, result-driven final retry, answer unlock, or post-terminal Run.
Final checks match the task: holdout prediction, independent objective/constraint recomputation,
residuals, repeated stochastic experiments or empirical verification as appropriate.
Independent read-only review consumes a fixed terminal candidate package before final decision.
Negative and partial terminal results remain valid attempts but never count as scientific PASS.

## Validation and evidence ownership

Use targeted `.venv/bin/python -m pytest` first, preserving real CLI positive/negative scenarios.
At candidate freeze and final delivery run `bash scripts/ci.sh`, strict repository validation,
`scripts/render_status.py --check` and `git diff --check`. Do not duplicate full pytest immediately
after full CI. Capture command, time, exit, subject/tree, output and coverage; distinguish historical
citations, local execution, remote feature head and PR merge tree. New evidence lives under
`evals/results/phase-004c5/`; raw logs/workspaces under ignored `.cache/pr12-rc8/`.
Native reviewer input/hash/tool output, independent numerical recomputation, main-agent checks and
human review are recorded separately. Serious scientific objections restrict acceptance even when
not expressible as a unit test. No majority vote can pass a Gate.

## Risks, stop and recovery

Maximum three implementation milestones and three audit-triggered repair loops. Stop repeating the
same root cause after three failed attempts without new evidence. At 2.5 h drop only noncritical
refactors/extra reports; preserve the scientific main questions and fresh-case window. At 3.5 h an
unresolved release blocker permits one last root-cause-directed repair, then the task's fallback
queue: development scientific gaps, old/new subject resolution tests, cross-structure regressions,
dependency declaration and runbook. Fallback never substitutes for unrun Validation.

Checkpoint every 30–45 minutes and after a failed gate. Report actual time and visible goal tokens;
unavailable monetary/cache/queue information is UNKNOWN. Preserve checkpoint on interruption.
Rollback means a new scoped corrective commit, never rewriting published history or old raw inputs.
Ordinary plan progress updates are already authorized; record changed decisions and their evidence.

## Decision/progress record

- Startup verified exact anchor/local/remote/PR head and Draft status; only supplied task text and
  its Zone.Identifier were untracked. The Zone.Identifier remains local and is not published.
- Registered RC8 as a pending candidate distinct from historical RC7 and inherited unpublished PR
  code. Archived the terminal 004C4 plan byte-for-byte to `plans/completed/`; historical paths resolve
  at their original Git subjects. Current state follows the previously authorized 004C5 route.
- First native read-only fact-binding reviewer started using a fresh context. No new official
  Validation input, numerical experiment or dependency installation has occurred at registration.
- Next: freeze neutral fact-binding cases, run inherited P0 checks and implement the smallest
  actual-controller repair supported by the new observations.

- 20:14Z progress: M1 core/source/scientific replay and no-Final design implemented; M2 has15 actual
  new Development captures (2021 8/9,2022 7/9) with negative/partial scientific conclusions preserved.
  Versioned candidate subject1b508aa has98 focused tests passing; fullCI rerun pending. Native audit
  found and reverified closure of forged checker and nonfinite qualification-counter attacks.
  Candidate acceptance, activation and remote freeze remain pending; no fresh inputs opened.
  Shared before-input rubric and observed environment now recorded under qualification/. M4/M5
  remain in scope; no noncritical refactor is planned beyond this point.

- 20:35Z: candidate subject29cf1d7 passed2153 full pytest tests (1 skipped), all CI post-checks,
 100 focused tests, strict and native increment review. Actual candidate checker PASS with activeRC7.
 Independent POST_DECISION Auditor PASS on29 bound evidence files/772 frozen implementation paths.
 Accepted research/Validation eligibility only, then locally activated RC8 with implementation
 unchanged. Live/version/training/state/strict checks PASS; remote delivery pending before fresh input.

- 20:47Z: release8ef732b remotely verified before official2016 input retrieval; receipt3aac696
 also remotely verified. OfficialC-only DOCX/XLSX input hashes registered, fresh-context worker
 dispatched. Planned2/started1/completed0/passed0; episode deadline22:37:30Z including preparation
 and review. Case pre-run remote freeze and numerical captures are still pending.

- 21:13Z:2016 code subjectbee0a94 and bound pre-run freezeb71d00f remotely verified before
 the first numerical capture. Same-case preparation revision1 preserved STALE; revision2 uses
 actual PARTIAL data sufficiency, two planned candidates/four maximum total captures, Final0.
 Audited worksheet labels and missing future truth prevent an untouched prediction-test claim.
 Main reviewed protocol consistency; worker chose all case models and no developer model recipe
 was supplied. The frozen shared772 paths remain unchanged. Current delivery CI has a preserved
 historical eight-case-count assertion failure; the separate new-registry-field error was repaired
 and its focused test passes. This does not replace or relabel the passing candidate-subject CI.

- 2026-09-08T21:51:49.240104+00:00:2016 C terminal decision frozen after native read-only audit PASS of the negative proposal.
 Planned2/started1/executed1/completed1/scientificPASS0;2 actual models,2 original checkers,
 2 audit checker replays,Final0. Three questions have conditional numerical outputs; stages11–14
 remain unaccepted. Main accepts audit corrections to overstrong future-truth/group-overlap
 interpretation and records actual remaining-time errors, without rewriting frozen inputs/results.
 Second2015 C remains unopened and is next if the preregistered complete window remains available.

- 2026-09-08T21:56:33.948200+00:00: first terminala03597b remote verified. Second2015 C started at21:53:34Z with
 13995s global remaining and a full7200s episode through23:53:34Z; candidate target23:33:34Z.
 Official C-only DOCX registered; no separate C attachment exists, so no substitution. Fresh worker
 receives only frozen generic materials and its own input. Planned2/started2/executed1/completed1/
 scientificPASS0. Shared implementation, rules and observed environment remain identical.

- 2026-09-08T22:21:23.158386+00:00:2015 C code subject675b37c remotely verified; actualCLI experiment plan accepted
 and bound to all4 required code blobs/22 inputs. Main corrected static count/time tolerance
 mismatch before any numeric model result. Case protocol freezes2 initial/8 maximum cumulative
 model captures,3 repair revisions,Final nonpredictive verification1. Shared772 files unchanged.
 Formalpre-run commit/remote confirmation still required before numeric execution.

-2026-09-08T22:45:53Z:2015 fixed numerical candidate9e58c46 remotely delivered; native
 terminal audit is inspecting a demonstrated formal Final/Gate ordering conflict, with2 models,
 2 original checkers,3 actual later replays,Final1/test0. No frozen files changed. Planned2/
 started2/executed2/completed1/scientificPASS0 pending independent adjudication.
 Main preregisters one case-owned2021 Q4 dual-certificate construction consuming the remaining
 ninth Development attempt, separate exact arithmetic verifier and original Run bindings.
 This is a supplemental conditional proof, not a new fresh case, new Skill or formal Gate pass.

- 2026-09-08T23:13:18.995181+00:00:2015 C formally frozenFAILED for Final prerequisite ordering after original
 nativeauditFAIL and separate Decision AuditorPASS of the negative revision. Both audits and
 actual stdin/output evidence retained. Planned2/started2/executed2/completed2/scientificPASS0.
 2015 has2 model captures,2 original checkers,3 later checker subprocesses,Final1/test0;
 99 nominal windows,2562 daily rows,503 perturbation windows independently checked.
 No post-terminal Run, shared mutation, answer unlock or next-phase advance. M4attempts complete.
 Supplementary2021 Q4 rational certificate PASS atbf34549: exact interval
 [40246.40307264615,40246.40311289259]m3.2021 budget9/9 consumed; whole-problem false.
 M5current fullCI, consolidated report and remote terminal/final delivery remain pending.

- 2026-09-08T23:36:40.979821+00:00: M5 local6be924e fullCI2151passed/2failed/1skip and actual remotePR merge
 22c0972 same counts. Fifteen required supplemental checks PASS; complete CI remains FAIL.
 Both terminals remotely delivered. Q4 native audit PASS within fixed LP scope; its rounded
 display warning is handled by a separate outward interval addendum, original files unchanged.
 Earlier progress-line decimal Q4 endpoints are approximate; strict display uses
 [40246.40307264614,40246.40311289260]. Composite report/recovery documents now drafted.
 One final native read-only delivery-consistency review may inspect a fixed report bundle; it
 cannot modify shared files, state, Git, terminal decisions, or run models/Final. Main remains
 sole public writer. Engineering closure remains INCOMPLETE until current CI blockers are repaired
 under a new coherent maintenance/candidate subject; no hash exception or rerun is granted.

- 2026-09-08T23:56:18.105571+00:00: final report first native consistency audit FAIL identified five wording errors.
 All five corrected; a separate short native re-review PASS is limited to those corrections.
 Original report/audit FAIL and actual tool receipts preserved. Public Q4 script transcripts use
 lossless JSON source encoding; original decoded bytes/hashes and syntax verified, no lint or
 whitespace rule changed. M5 content ready for final content commit/CI/push. Existing engineering
 and scientific BLOCKERs remain, no shared repair/new candidate or terminal rerun is authorized
 by this report review. Prospective10 neutral repair cases are recorded as NOT_EXECUTED.
