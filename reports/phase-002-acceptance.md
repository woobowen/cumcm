DYNAMIC_EVAL_COMPLETE_AWAITING_HUMAN_GATE

# Phase 002 Acceptance Report

## Scope and terminal boundary

- Phase: `PHASE-UPSTREAM-DYNAMIC-EVAL-002`.
- Active plan: `plans/active/PLAN-0002-upstream-dynamic-evaluation.md`.
- Recommendation: `RECOMMEND_CLEAN_ROOM_ARCHITECTURE` with the native
  `NO_PROJECT_MODELING_SKILL` baseline as fallback.
- Authority: `PROPOSAL_ONLY — HUMAN GATE REQUIRED`.
- Formal state remains `IN_PROGRESS`; blocker is `GATE_BASE_SELECTION_PENDING`.
- `base_selected=false`; `third_party_integrated=false`; formal Skill remains `SCAFFOLD_ONLY`.
- `PHASE-SKILL-INTEGRATION-003` has not started.

## Evidence inventory

- Six project-authored deterministic synthetic cases, seed `20260831`, 29 frozen generated
  artifacts, and stable content-set hash
  `9aa9f4813e8bcdea383f86d7db88825f341fe3a2cfbcc07ff26fea51ca73ba97`.
- Three text-only packages are `PACKAGE_SAFE`; package hashes are baseline
  `908d89f00e4bbab7260c84d5b698171c87ea8c12f86f08ea437289ec8385b26c`,
  HANDSOMEZR `7a9cb6c6850991f9d708a83c762ffd6f066c024153f39b3c0e7a123f50d68194`,
  and YUSHUI `ab7a9611c67b4f14c50feb338c5c027737e0fc4936d046604f4a6c34fef807d5`.
- 20/20 retained real attempts: 13 completed and seven failed, including two superseded
  CASE-001 run-001 failures. Both allowed calibration runs were used; no run is hidden.
- 18/18 current cells are scored. Five cells use append-only hash-bound recovery and remain
  `affected_by_run_failure=true` with LOW confidence; every original FAILED manifest remains.
- 18 initial 70/30 scores were frozen at `2026-08-31T10:05:21.949273Z`; identities were revealed
  separately at `2026-08-31T10:10:33.283763Z`; score hashes were preserved and no correction exists.
- Reveal: ARM-A=YUSHUI, ARM-B=NO_PROJECT_MODELING_SKILL, ARM-C=HANDSOMEZR.
- Median deterministic/reviewer/total scores: YUSHUI 34.0/26.0/60.0, native baseline
  37.5/25.5/62.5, HANDSOMEZR 34.0/26.0/60.5. Hard failures: zero.
- Total retained runtime: 2847.841679 seconds. Observable usage: 3,461,771 input and 143,300
  output tokens. These counts come from retained trace summaries, not billing claims.

## Retained failures and interpretation

The seven failed Run manifests are not erased or averaged away. Two initial CASE-001 failures were
followed by the only two allowed calibration attempts. Five current failures were publication-parser
false positives recovered offline from hash-bound raw output; their scores are explicitly LOW
confidence. The final main-run command returned exit 1 because it faithfully read back 13 COMPLETED
and five FAILED current manifests. It created zero new runs and is not a delivery blocker.

The 2.5-point median spread, one current observation per cell, synthetic-only benchmark, and uneven
recovery effects do not establish a winning base or real CUMCM performance. Dynamic quality is kept
separate from legal reuse, technical integration, security, contamination, and maintenance.

## Component ruling

Four and only four cards are proposed: `accepted-versus-done-workflow-state`,
`claim-evidence-support-gate`, `hash-bound-reproducibility-manifest`, and
`leakage-safe-model-comparison-gate`. Each is `CLEAN_ROOM_REIMPLEMENT_CANDIDATE`, traces to an
observed CASE gap, states an observable next-phase metric, preserves the single state/Skill truth,
and requires human review. No component is approved, copied, ported, or integrated.

## Safety and legal boundary

- Third-party code executed: no.
- Candidate dependencies installed: no.
- Candidate scripts, hooks, binaries, Makefiles, installers, MCPs, or services invoked: no.
- Historical CUMCM problems, answers, excellent papers, demo results, or benchmark vault read: no.
- Candidate full text, raw traces, raw outputs, hidden reasoning, credentials, or private paths tracked: no.
- Workspace Git remotes: none; dangerous bypass sandbox: not used; global configuration: unchanged.
- YUSHUI remains `UNKNOWN_NO_LICENSE`; direct reuse and fork remain blocked regardless of score.
- HANDSOMEZR and selected component sources retain external, corpus, per-Skill, or subresource gaps.
- Historical/demo/corpus content remains excluded from all packages, prompts, fixtures, and graders.

## Test and contract result

- Pytest: 93 collected, 93 passed, 0 failed, 0 skipped, 0 warnings.
- Dedicated fault-injection plus Runner policy/process collection: 29 test nodes, all passed.
- Contracts: 21 Schemas, 21 positive fixtures accepted, 11 negative fixtures rejected.
- Strict repository validation: PASS, zero errors, zero warnings.
- Ruff check and format check: PASS for 165 files.
- GitHub Actions: pull_request, push-to-main, and workflow_dispatch triggers; read-only contents;
  Python 3.11 via uv; only bootstrap plus `bash scripts/ci.sh`; no real Codex evaluation.

## Final validation command ledger

`real/mock` describes what the command actually did. `REAL-READBACK` means it read retained real-run
manifests but launched no new Codex process.

| Command | Exit | Seconds | real/mock | Result, failure reason, blocker |
|---|---:|---:|---|---|
| `.venv/bin/python -m ruff check .` | 0 | 0.084 | deterministic local | PASS; no failure; not blocker |
| `.venv/bin/python -m ruff format --check .` | 0 | 0.029 | deterministic local | PASS, 165 files formatted; not blocker |
| `.venv/bin/python -m pytest -q` | 0 | 7.098 | offline mock/unit/integration | PASS, 93 passed; no real network or Codex; not blocker |
| `.venv/bin/python scripts/check_instruction_budget.py` | 0 | 0.241 | deterministic local | PASS, total project AGENTS 5,675 bytes; not blocker |
| `.venv/bin/python scripts/check_skill_discovery.py --expected-name cumcm-modeling-evidence --expected-count 1` | 0 | 0.048 | deterministic local | PASS, exactly one formal Skill; not blocker |
| `.venv/bin/python scripts/check_contracts.py` | 0 | 0.177 | deterministic local | PASS, 21/21 valid and 11 invalid rejected; not blocker |
| `.venv/bin/python scripts/check_upstream_manifest.py` | 0 | 0.105 | deterministic local | PASS, eight pinned candidates and ignored cache; not blocker |
| `.venv/bin/python scripts/check_answer_leakage.py` | 0 | 0.023 | deterministic local | PASS, zero findings; not blocker |
| `.venv/bin/python scripts/check_secrets.py` | 0 | 0.268 | deterministic local | PASS, zero secret/private-path findings; not blocker |
| `.venv/bin/python scripts/generate_eval_fixtures.py --check` | 0 | 0.079 | deterministic local | PASS, zero mismatches; not blocker |
| `.venv/bin/python scripts/build_eval_packages.py --check` | 0 | 0.176 | deterministic cache read | PASS, three PACKAGE_SAFE hashes current; no third-party execution; not blocker |
| `.venv/bin/python scripts/run_upstream_dynamic_eval.py --smoke` | 0 | 10.518 | REAL Codex capability run | AVAILABLE; gpt-5.4/medium/workspace-write, no tool command/remote. Known model-cache/state-db warnings only; not blocker |
| `.venv/bin/python scripts/score_upstream_dynamic_eval.py --check` | 0 | 0.150 | deterministic offline | PASS, 18 frozen scores; not blocker |
| `.venv/bin/python scripts/summarize_upstream_dynamic_eval.py --check` | 0 | 0.085 | deterministic offline | PASS, seven outputs current; not blocker |
| `.venv/bin/python scripts/render_status.py` | 0 | 0.064 | deterministic local write | PASS, generated only from project_state; not blocker |
| `.venv/bin/python scripts/render_status.py --check` | 0 | 0.020 | deterministic local | PASS, current; not blocker |
| `.venv/bin/python scripts/validate_repo.py --strict` | 0 | 0.935 | deterministic local | PASS, zero errors/warnings; not blocker |
| `bash scripts/ci.sh` | 0 | 8.086 | offline aggregate | PASS after all code changes, 93 tests and strict validation; not blocker |
| `git diff --check` | 0 | 0.003 | deterministic local | PASS; not blocker |
| `git status --short --branch` | 0 | 0.010 | deterministic local | PASS; feature branch clean before delivery; not blocker |
| `.venv/bin/python scripts/run_upstream_dynamic_eval.py --config evals/configs/phase-002.yaml` | 1 | 0.100 | REAL-READBACK, no new Codex run | 18 current cells: 13 COMPLETED, five retained FAILED; Run count stayed 20→20. Expected evidence status; not blocker |
| `.venv/bin/python scripts/score_upstream_dynamic_eval.py --config evals/configs/phase-002.yaml` | 0 | 0.222 | deterministic offline | PASS, read-only verification of 18-score freeze; no overwrite; not blocker |
| `.venv/bin/python scripts/summarize_upstream_dynamic_eval.py --config evals/configs/phase-002.yaml` | 0 | 0.100 | deterministic offline | PASS, seven outputs rebuilt; not blocker |
| `git push -u origin HEAD` | 0 | 4.010 | real remote delivery | PASS, local/remote `09a760cb9b22f467163253953134b31d0d99e909`; not blocker |
| `gh pr create --draft --base main --head feat/upstream-dynamic-eval ...` | 0 | 4.9 | real GitHub mutation | PASS, Draft PR #2 created; no approval/merge; not blocker |

All later freeze/reveal/report checks also passed after the idempotent score CLI change. The
acceptance-closing commit must be pushed normally and verified by exact remote SHA; that post-commit
proof is reported in the final handoff without rewriting this report.

## Acceptance criteria A–J

| Group | Status | Evidence |
|---|---|---|
| A. Preconditions | PASS | Correct non-main feature branch; PR #1 merged; Foundation base `d313634…`; one Skill; no tracked candidate cache |
| B. Plan and governance | PASS | PLAN-0002 active, PLAN-0001 archived, ADR-0006…0009, Runbook, rules, and human Gate present |
| C. Benchmark | PASS | Six synthetic cases, no historical material, fixed seed/oracles/hashes, identity-independent grader, STALE test |
| D. Safe packages | PASS | Ignored cache only; text-only allowlist; no executable/code/dependency; hashes and include/exclude evidence; no candidate text tracked |
| E. Runner | PASS | Real capability, temporary Git, no remote/web/MCP, same model/prompt/Schema/timeout, retained failures, ignored raw traces |
| F. Dynamic runs | PASS | All three arms attempted; 20 real records; NOT_RUN is nullable not zero; two bounded calibrations; failures retained; rules unchanged |
| G. Scoring | PASS | 70 deterministic + 30 blind Reviewer; hard failures preserved; freeze before reveal; evidence/dimensions; no automatic selection |
| H. Components | PASS | Four observed-gap cards with pinned commits, license/contamination, measurable benefits, clean-room tests, no second state/Skill |
| I. Engineering | PASS | Schemas/positive/negative fixtures, unit/integration/fault tests, Foundation regression, strict/CI, offline GitHub Actions |
| J. Terminal state | PASS | Accurate reports; IN_PROGRESS; Gate pending; false integration/selection flags; SCAFFOLD_ONLY; branch delivered; Draft PR; no Phase 003 |

## Git delivery and recovery

- Designated remote: `origin`; branch: `feat/upstream-dynamic-eval`; protected base: `main`.
- Pre-acceptance remote equality was verified at
  `09a760cb9b22f467163253953134b31d0d99e909`.
- Draft PR: `https://github.com/woobowen/cumcm/pull/2`; state OPEN/DRAFT; base `main`.
- Remote CI at report creation: `offline-validation` IN_PROGRESS; local CI is authoritative for this
  acceptance condition, and the final handoff reports the later remote conclusion.
- Rollback uses non-destructive `git revert <milestone-commit>`; never erase retained failures, reset
  published history, delete the branch, force-push, or modify `main`.

## Human Gate

Humans must approve or reject the clean-room architecture direction, neutral fallback, each of the
four mechanism cards, project/per-resource license requirements, frozen Phase 003 validation design,
the permitted use of recovery-affected evidence, and preservation of one Skill/one state/no-answer
access/high-risk human gates. Until a decision is recorded, the only permissible next step is review
of `reports/human_gate_base_selection.md`; implementation and Phase 003 remain blocked.
