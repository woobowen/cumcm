# PR12 Phase 004C5 evidence and generalization execution report

Generated at `2026-09-08T11:56:51+08:00`. This report is a continuation
record, not a release authorization.

## Decision summary

- Development engineering disposition: `ACCEPTED_FOR_PROVISIONAL_HANDOFF` for
  the registered 2021 C and 2022 C regressions only.
- Formal disposition: `VALIDATION_PRECONDITIONS_BLOCKED`.
- Release disposition: `CANDIDATE_NOT_RELEASED`; PR #12 remains open/draft.
- No Final evaluator was invoked, no test labels were accessed, and no 2016 C
  or 2015 C inputs were accessed.

## M0, identity, and boundaries

- Checkpoint start: `2026-09-08T09:56:26.5351995+08:00` local,
  `2026-09-08T01:56:26.5351995+00:00` UTC.
- This report's observed close point is `2026-09-08T11:56:51+08:00`; wall-clock
  continuation was about two hours at this checkpoint. Codex token/input/output
  telemetry was not observable.
- Start branch and head: `feat/phase004c5-p0-01-finalization-hf22-repro`,
  `c71912e176f8fcec148542ec5f929dda3b1b3c66`.
- Implementation freeze: `84087c71d1a20501771e95851ad42e4662cbbdc9`,
  repository tree `78654b2de71b2953a3c7c23930568829811e0a02`, Skill subtree
  `bfc3be777fb42e01e40067a3cbb419448454164f`.
- Remote branch matched the implementation freeze after the code push. The
  final documentation/receipt commit may advance the branch head without
  changing this frozen implementation identity.
- The user-provided `CUMCM_PR12_7H_EXECUTION_PLAN.md` was preserved and not
  staged. Historical Validation artifacts, formal state, registry, answer
  material, 2025 C, benchmark vault, and unrelated jobs/worktrees were not
  modified.

## M1: evidence-semantic repair

The old Development workspaces contained no
`evidence/final_evaluation_ledger.json` but their comparison records asserted
`test_access.authorized=true,count=1`. The generic contract was repaired to
require the explicit `DEVELOPMENT_NO_FINAL_EVALUATION` shape:
`authorized=false`, integer `count=0`, `used_for_selection=false`,
`evaluator_invoked=false`, and `ledger_status=NOT_ACCESSED`. Legacy implicit
zero-access records remain fail-closed, and a Development count of one is
rejected.

The route now derives stage evidence from observed state history and records
observed UTC timing. Claim semantic adapters are case-owned JSON files rather
than a generic all-`DESCRIPTIVE` map; they are schema/case/requirement/hash
bound and forbid `PREDICTIVE` claims without formal Final evidence.

The neutral evidence test suite is `5 passed`. The related finalization and
Development regression test set is `17 passed` after a Windows path-key repair
in `scripts/freeze_skill_first_run.py` (all four relative-path emissions now
use POSIX separators).

## M2: scientific audit and iteration

2022 C:

- The official workbook yields 56 effective artifact groups after validity
  filtering and median aggregation, with only 12 fixed Development validation
  groups (4/8 class split); unknown/test labels remain unaccessed.
- Fixed-split scores are raw centroid `0.1216581282`, CLR ridge
  `0.0198854699`, and Hellinger KNN `0.0000000000` Brier loss.
- The persisted 4-fold x 5-repeat grouped diagnostic for the selected KNN has
  280 held-out group predictions, accuracy mean/min/max `1/1/1`, and Brier
  mean/median/min/max `0.0000891426/0/0/0.00178285`. This corrects the
  interpretation of the small fixed-split zero; it is not external validity,
  calibration evidence, or Validation.

2021 C:

- Independent workbook parsing reproduces the selected baseline validation
  score `2.137602595628006` versus route output `2.137602596` (absolute
  difference `3.72e-10`). The selected forecast receipt is within the declared
  `0.0282 m3` tolerance, not exact equality.
- The declared 399 supplier count is an upper-bound candidate pool; the weekly
  plan transports from 168 suppliers. No global minimum certificate is
  claimed.
- Two independent rolling windows retain the baseline winner under the
  registered Development metric; this remains conditional future-behavior and
  does not establish global optimality.

## M3: cross-case repair and final Development receipts

The cross-case matrix identifies four generalized risks: false Development
test access, silent all-`DESCRIPTIVE` labels, engineering gates being mistaken
for scientific quality, and case-specific overclaiming. The independent
read-only review recomputed outputs without importing the case feasibility
module and did not write case workspaces or formal state.

Canonical latest evidence is isolated under
`evals/results/phase004c5-pr12-7h/development-v4/`:

| case | attempt | valid runs | terminal | evidence SHA-256 |
| --- | ---: | ---: | --- | --- |
| 2022 C | 11 | 3/3 | `READY_FOR_PAPER_HANDOFF` | `BDB38F18F6A5AEC70779316296A2E6E49E6E584AF133A9CAF86FD861E4B954D5` |
| 2021 C | 5 | 3/3 | `READY_FOR_PAPER_HANDOFF` | `6D0F00EC8EC6850806941CDC79D3650940886A79B5CF590FF8B5520C1276ED72` |

Both receipts bind `84087c71d1a20501771e95851ad42e4662cbbdc9`, report
`PROVISIONAL_ENGINEERING_REGRESSION`, have `claim_gate=PASS` and
`handoff_gate=PASS`, and contain explicit `DEVELOPMENT_NO_FINAL_EVALUATION`
with `authorized=false,count=0`.

## Verification truth

- `.venv/Scripts/python.exe scripts/validate_repo.py --strict`: repository
  `PASS`, 0 errors, 0 warnings.
- Ruff full check and format check: pass; `git diff --check`: pass.
- Correct project test entry point:
  `.venv/Scripts/python.exe -m pytest --collect-only -q`: 2,091 tests
  collected.
- Correct-entry `python -m pytest -x -q`: stopped at the first historical
  Phase-002 freeze test after `175 passed, 1 failed` in 17 minutes. All 120
  reported frozen-file mismatches are CRLF-only checkout differences from the
  historical LF subject commit; after CRLF normalization they are identical,
  and the base/subject/HEAD Git blob for `CASE-001.json` is unchanged. This is
  not a clean full release gate.
- Direct `.venv/Scripts/pytest.exe` collection is not used as the project result:
  on Windows it produced 17 `ModuleNotFoundError` collection errors because
  that launcher did not put the repository root on `sys.path`.
- GitHub PR #12 run `34185499763` reached the `offline-validation` job and
  failed with exit code 1 after 6m16s; checkout, uv setup, and environment
  bootstrap were successful. The Node.js 20 message is an annotation warning,
  not the failing result. The public job page does not expose the step log
  without sign-in.

## CI failure self-audit

- The CI entry point runs the full `pytest -q` before the remaining frozen
  checkers. Because `scripts/ci.sh` uses `set -e`, a non-zero test or checker
  result terminates the job; the single GitHub step therefore hides which
  internal command failed.
- The PR workflow checks the GitHub pull-request merge tree, not only the
  feature branch. A read-only fetch of `refs/pull/12/merge` produced merge
  commit `e97dcc39bd0d4e58f93e53776c91d98bc1f37255` from branch head
  `f17e99ac3ccf24d724bf5cd699074e68c37d8d41`. Ruff check and format check
  pass on that tree. The Windows worktree showed only path-separator-only
  registry discrepancies in a few POSIX-sensitive checkers; those are not
  evidence of a Linux CI failure.
- The first platform-independent blocker after the merge-tree replay is
  `scripts/check_claim_scope_repair.py --check`:
  `HISTORICAL_EVIDENCE_DRIFT` for the 2021 C supply-plan code and the 2022 C
  model-pipeline code. Their preflight hashes are unchanged, while the
  current files contain the new cardinality fields and repeated grouped-CV
  diagnostic. This is a legitimate frozen-history guard, not a reason to
  rewrite old hashes or remove the checker.
- No formal state, historical freeze, or registry was rewritten during this
  audit. The feature branch and PR head remain at `f17e99a`; no new push was
  made. The repair boundary is to move new Development code/evidence into a
  new governed case/freeze, or run a separately authorized correction
  protocol, while leaving the historical case roots immutable.

Read-only formal checks independently agree with the blocked boundary:

- `python -X utf8 scripts/check_phase004c4_fresh_validation.py --check`
  returned `BLOCK`, `verdict=C_TARGET_VALIDATION_FAILED`, `run_count=9`,
  `answer_access_status=SEALED`, `workspace_verified=false`, and 17 errors:
  five historical validation-code drift items, fresh integrity/terminal-registry
  invalidity, and tracked-artifact drift in the pre-run freeze, contamination
  check, input registration, official retrieval, decision, controller outcome,
  fourteen-stage episode, and selection/run summary.
- `scripts/check_phase004c4_regressions.py --check` returned `BLOCK` with eight
  frozen-regression file-drift errors. `scripts/check_c_target_batch_freeze.py
  --check` returned `ok=false` with `BATCH_FREEZE_DELIVERY_RECEIPT_INVALID` and
  `BATCH_FREEZE_PROJECT_STATE_DRIFT`.
- RC7 candidate/live checks returned `BLOCK` for candidate evidence/receipt
  drift, premature or invalid live state, and missing/invalid release binding.
  These checks were not repaired by rewriting formal artifacts.

## M4/M5 blocker and recovery

The formal registry and `state/project_state.json` still identify the active
historical release as `0.2.0-competition-rc7`, with state
`IN_PROGRESS / C_TARGET_VALIDATION_FAILED`. There are no new 2016/2015 case
registry entries, no formal RC8 release manifest, no answer-sealed remote
pre-run freeze for unfamiliar cases, and no clean full release gate.

Therefore fresh Validation was not started and no Validation result is claimed.
The recovery entry is to preserve the v1/v2/v3/v4 Development receipts and
audits, then begin a new formal release/freeze protocol only after registry,
answer-sealed workspace, remote receipt, and clean-context worker prerequisites
are independently present.

## Evidence index

- [checkpoint](../evals/results/phase004c5-pr12-7h/checkpoint.md)
- [candidate freeze](../evals/results/phase004c5-pr12-7h/candidate_freeze.md)
- [cross-case gap matrix](../evals/results/phase004c5-pr12-7h/cross_case_gap_matrix.md)
- [independent read-only review](../evals/results/phase004c5-pr12-7h/scientific/independent_readonly_review.md)
- [2021 audit](../evals/results/phase004c5-pr12-7h/scientific/2021_baseline_audit.md)
- [2022 audit](../evals/results/phase004c5-pr12-7h/scientific/2022_zero_loss_audit.md)
- [2022 Development receipt](../evals/results/phase004c5-pr12-7h/development-v4/CUMCM-2022-C-DEVELOPMENT-BATCH-001/development_regression_evidence.json)
- [2021 Development receipt](../evals/results/phase004c5-pr12-7h/development-v4/CUMCM-2021-C-DEVELOPMENT-BATCH-002/development_regression_evidence.json)
