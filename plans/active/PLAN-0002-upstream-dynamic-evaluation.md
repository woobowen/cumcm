# PLAN-0002 — Upstream Dynamic Evaluation

Status: `IN_PROGRESS`
Phase: `PHASE-UPSTREAM-DYNAMIC-EVAL-002`
Owner: main agent
Started: `2026-08-31T16:00:59+08:00`

## 1. Background

Foundation is merged at `d31363438e73b9f227999975a5c068cabbaa0aea`. It established one
`SCAFFOLD_ONLY` project Skill and eight pinned, statically reviewed upstream candidates. Dynamic
behavior remains unverified and the project license remains undecided.

## 2. Current authoritative state

- Repository root: `<REPO_ROOT>`; branch: `feat/upstream-dynamic-eval`.
- Base commit and current `origin/main`: `d31363438e73b9f227999975a5c068cabbaa0aea`.
- Formal state is `state/project_state.json`; generated status is read-only.
- `base_selected=false`, `third_party_integrated=false`, formal Skill `SCAFFOLD_ONLY`.
- Candidate identity/commit/license facts come only from `research/upstream_candidates/manifest.yaml`.

## 3. Goal

Build, execute, and validate an offline, auditable, identity-blind dynamic evaluation comparing the
no-project-modeling-Skill baseline with the two base candidates through sanitized instruction-only
packages, then publish proposals that stop at `GATE_BASE_SELECTION_PENDING`.

## 4. Non-goals

Do not select or integrate a base/component, modify the formal Skill, use historical CUMCM tasks or
answers, write paper content, execute candidate code, install candidate dependencies, create a
project LICENSE, change global configuration, merge a PR, or start Phase 003.

## 5. Candidate scope

- `NO_PROJECT_MODELING_SKILL`: neutral baseline; not “no Skill”.
- `handsomezr-mathmodel-skill@d3941e14d8693fb4a79948e59afff3098734127e`:
  `SANITIZED_INSTRUCTION_ONLY`.
- `yushui-mathmodel-skill@51054497f052197c3afe434e502e38edb85b2870`:
  `SANITIZED_INSTRUCTION_ONLY_WITH_LICENSE_BLOCKER`.
- At most five mechanism cards may be proposed only after observed gaps.

## 6. Safety boundary

Candidate repositories are untrusted data. Only allowlisted plain text under ignored caches may be
read. Never execute candidate scripts, binaries, hooks, Makefiles, installers, MCPs, or services.
Each real run uses an isolated temporary Git repository with no remote, `workspace-write`, no MCP,
no web request, a fixed output Schema, and a scrubbed environment. Raw events and normalized
candidate instructions remain ignored.

## 7. License boundary

Dynamic quality does not grant reuse rights. `UNKNOWN_NO_LICENSE` cannot become direct reuse or a
fork recommendation. Unknown subresource rights remain blockers. Proposals distinguish dynamic
quality, legal reuse, technical integration, security, and maintenance.

## 8. Contamination boundary

All six cases and oracles are project-authored synthetic data. No historical problem, answer,
excellent paper, candidate demo result, or paper-derived phrase enters packages, prompts, fixtures,
graders, or tracked outputs. A failed contamination scan makes the package unsafe.

## 9. Architecture

`case_generation` freezes deterministic fixtures; `package_builder` produces cache-only sanitized
packages; `runner` builds isolated workspaces and records observable events; `scoring` combines a
70-point deterministic layer with a 30-point reviewer layer; `anonymization` freezes then reveals
arm identity; `reporting` rebuilds tracked summaries. Schemas and `dynamic_eval_rules.yaml` are the
machine contracts.

## 10. Benchmark cases

CASE-001 requirement trace; CASE-002 data audit/leakage; CASE-003 formalization/baseline/known
optimum; CASE-004 temporal experiment/robustness; CASE-005 freshness/STALE propagation; CASE-006
source evidence/method adaptation. Seed, fixture hashes, task hashes, and independent oracles freeze
each case.

## 11. Runner design

Invoke the installed `codex exec` only with flags verified by `codex exec --help`: `--ephemeral`,
`--ignore-user-config`, `--sandbox workspace-write`, `--json`, `--output-schema`,
`--output-last-message`, model, config reasoning effort, and isolated `--cd`. Capture exit code,
duration, JSON event counts, usage when present, files/hashes, Schema outcome, and sanitized error.
Mock execution is structurally identical but explicitly labeled `MOCK`.

## 12. Temporary workspaces

Packages, workspaces, raw traces, raw outputs, and logs live only below `.cache/upstream-eval/`.
Each workspace is a fresh Git repo without a remote and contains only a case, public output Schema,
task prompt, and one arm’s sanitized instructions. Tracked results contain no raw trace or candidate
text.

## 13. Anonymous evaluation

The arm map is generated once in ignored cache. Run and score records expose `ARM-A/B/C` only.
Initial deterministic/reviewer scores freeze before reveal. Reveal writes a separate record; any
later correction appends and never overwrites the initial score.

## 14. Deterministic grader

Graders check injected truth, contract fields, observable commands/files, known optimum, temporal
split/leakage, dependency propagation, and source support. They never inspect candidate identity.
Missing evidence reduces score; `NOT_RUN` remains missing rather than zero.

## 15. Reviewer boundary

Anonymous qualitative review contributes at most 30 points and must cite fields/events. It cannot
repair original output, override hard failures, prove mathematical correctness by vote, or write
formal state. The main agent records discrepancies.

## 16. Scoring and hard failures

The deterministic layer is 70 and reviewer layer 30. `rules/dynamic_eval_rules.yaml` owns dimension
weights and HARD-FAIL-001…012. A hard failure is retained and cannot be averaged away.

## 17. Budget

Maximum 20 real runs, at most 15 minutes each. Start with one identical smoke case per runnable arm;
then one six-case round (18 theoretical arm/case cells, smoke may reuse CASE-001 only when the full
record is valid). Up to two calibration runs are allowed. Quota/auth failures stop retries and leave
remaining cells `NOT_RUN`.

## 18. Milestones

1. M1 phase start: plan, ADRs, rule/config/state, Foundation regression.
2. M2 deterministic fixtures, Schemas, graders, tests, frozen hashes.
3. M3 sanitized packages, allow/exclude evidence, tests.
4. M4 isolated runner, mock integration, smoke capability, fault injection.
5. M5 equal-arm real smoke.
6. M6 fixed first-round real executions.
7. M7 blind scoring/review, score freeze, reveal.
8. M8 gap matrix and at most five mechanism cards.
9. M9 proposal and human Gate materials.
10. M10 full validation, acceptance, atomic commits, push, remote SHA, Draft PR.

## 19. Acceptance by milestone

- M1: Foundation CI passes; one active plan; state/report agree; four ADRs exist.
- M2: six reproducible cases/oracles; all six new Schemas have positive and negative fixtures;
  generator `--check` passes; deterministic graders have identity-independence tests.
- M3: packages are cache-only, pinned, text-only, non-executable, hashed, license/contamination
  recorded; unsafe inputs fail closed.
- M4: mock end-to-end, timeout/nonzero/auth/quota/secret/trace/path/prompt-fairness tests pass;
  nested capability smoke is truthfully recorded.
- M5/M6: completed/failed/not-run records reflect actual attempts without discarded failures.
- M7: 70/30 results, hard failures, freeze and reveal evidence are rebuildable offline.
- M8/M9: proposals trace only observed gaps and preserve all legal/safety/human gates.
- M10: required validation passes, branch is pushed and SHA-equal, Draft PR remains unmerged.

## 20. Validation commands

Run the exact command set in the Phase 002 task, including Ruff, pytest, all existing validators,
fixture/package/runner/scorer/summary checks, status render/check, strict validation, `scripts/ci.sh`,
Git whitespace/status, and—when nested execution is available—the configured real run plus offline
score and summary. Record command, exit, duration, real/mock classification, and result.

## 21. Decisions

- `2026-08-31`: Keep candidate code non-executable and evaluate sanitized textual mechanisms only.
- `2026-08-31`: Use synthetic cases before historical development/validation/held-out cases.
- `2026-08-31`: All selection artifacts are proposals; `BASELINE_SELECTED` requires a human Gate.
- `2026-08-31`: Foundation’s `preferred_task_branch` was phase-specific and stale; update the sole
  tracked delivery truth to `feat/upstream-dynamic-eval`, preserving the remote/base protections.

## 22. Risks

Nested Codex auth/quota/latency may block sufficient evidence; sandbox mode does not itself provide
OS-level network denial; textual sanitization cannot prove full upstream behavior; small samples
limit confidence; unknown licenses block direct adoption; candidate examples can contaminate
evaluation if allowlists fail; qualitative review can introduce bias.

## 23. Actual progress

- [x] Prompt ingested completely; preconditions and Foundation `23 passed` baseline verified.
- [x] Required sources of truth, policies, candidate reviews, contracts, rules, and directory AGENTS
  read in prescribed order.
- [x] M1 phase start prepared; Foundation regression passed (`23 passed`, strict PASS) before the
  atomic M1 commit.
- [x] M2 generated and froze six cases/oracles/rubrics (29 artifacts), added six Schemas with valid
  and invalid fixtures, and validated the identity-independent deterministic grader.
- [x] M3 built three deterministic cache-only packages at pinned commits; code/executable,
  contamination, license, and normalized-instruction tests passed. No raw candidate text was copied.
- [x] M4 added the isolated nested-Git Codex runner, ignored arm map/raw traces, structured run and
  observation records, fail-closed publication checks, mock integration, and fault injection.
  A real capability smoke passed with the fixed model/settings and no workspace remote.
- [ ] M5 equal-arm smoke executed once for all three anonymous arms: one completed and two were
  retained as failures caused by an over-strict harness interpretation of descriptive/no-artifact
  strings. Repair and at most one append-only retry per affected cell remain within the two-run
  calibration allowance; no record will be overwritten.
- [ ] M6–M10.

### Validation evidence

- `2026-08-31` M1: `scripts/render_status.py` exit 0; `--check` exit 0; `git diff --check`
  exit 0; `bash scripts/ci.sh` exit 0 in 4.11 s with Ruff clean, 23 pytest tests passed,
  repository strict validation PASS, zero warnings.
- `2026-08-31` M2: fixture generation exit 0 and `--check` current with 0 mismatches;
  contract check reports 17 Schemas, 17 valid fixtures, and 7 invalid fixtures rejected; focused
  pytest exit 0 with 11 passed; Ruff and `git diff --check` exit 0. The first focused run failed
  because the positive test did not contain oracle evidence and Ruff found long literals; both root
  causes were corrected without weakening the grader, then the full focused rerun passed.
- `2026-08-31` M3: focused package/safety pytest exit 0 with 8 passed; package builder and
  `--check` exit 0 with three `PACKAGE_SAFE` manifests and zero mismatches; tracked cache check is
  empty. The first focused run found an incomplete `requests` text pattern and two Ruff line-length
  errors; scanner coverage and formatting were corrected before acceptance.
- `2026-08-31` M4: real Codex capability smoke exit 0 in 9.730414 s with `gpt-5.4`, `medium`,
  `workspace-write`, Structured Output, no tool command, and no Git remote. Focused Runner tests
  passed 24/24, including timeout, nonzero, auth, quota, environment scrub, secret/path/Schema/file
  reference, input mutation, network/MCP trace, prompt fairness, no overwrite, and ignored raw
  traces. Full CI passed with Ruff clean, 65 pytest tests, strict repository PASS, zero warnings.
  The first smoke exposed a transient model-cache parse warning; the decisive diagnostic exposed a
  missing JSON Schema `type` in the smoke fixture. The Schema was corrected without changing model
  or execution policy. The first full CI correctly rejected key-like and private-path fault literals;
  fixtures were changed to runtime construction without weakening the repository scanners.
- `2026-08-31` M5 first attempt: three real CASE-001 records used one common task hash; durations
  were 116.062575/185.829731/48.930851 s, every process exited 0, one record completed, and two
  failed publication. Anonymous review of only the affected fields showed false positives: a real
  `.harness/workflow_state.json` reference included descriptive suffix text, while Chinese `无。`
  values were treated as paths/actions. Original run-001 records are retained. No identity map was
  read and no score was assigned. The repair must accept explicit none markers and validate the
  leading path token without weakening nonexistent-file, secret, input mutation, network, or MCP
  controls; the two affected cells may use the predeclared one-retry/two-calibration budget.

## 24. Interruption recovery

Read root `AGENTS.md`, this plan, `state/project_state.json`, the runbook, phase config, and the latest
task/review ledgers. Run `git status --short --branch` and `bash scripts/ci.sh`. Resume at the first
unchecked milestone; never delete or regenerate a valid run merely because it failed.

## 25. Rollback

Use non-destructive `git revert <milestone-commit>` after publication. Before publication remove
only explicitly identified new files after inspection. Never reset, clean, force-push, or erase run
evidence. Ignored cache cleanup requires explicit target verification and user authorization.

## 26. Human Gate

`GATE_BASE_SELECTION_PENDING` remains open. Humans must approve/reject the proposed base strategy,
clean-room mechanisms, license treatment, residual contamination risk, and permission to start
Phase 003. No agent writes approval.

## 27. Completion condition

`DYNAMIC_EVAL_COMPLETE_AWAITING_HUMAN_GATE` requires frozen benchmarks/graders, verified runner,
sufficient real dynamic evidence, blind scoring, component/proposal materials, passing deterministic
validation, remote SHA equality, and a Draft PR. Otherwise publish accurate partial work as
`DYNAMIC_EVAL_INCOMPLETE`.

## 28. Next-phase recommendation

After explicit human approval only, create a separate Phase 003 plan to clean-room integrate the
approved architecture/components. This plan must never transition the project to Phase 003.

## Update rule

After every milestone, validation failure, blocker, correction, reveal, or design change, append
facts and exact validation evidence. Preserve historical decisions and failure records.
