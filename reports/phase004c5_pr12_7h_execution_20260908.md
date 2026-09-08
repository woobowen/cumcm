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
- The current local recovery commits are `cb0e89f` (historical-root isolation)
  and `65e74b2` (preserve the next Development attempt), followed by
  `bcc3fca` (checker path normalization), `ef69b02` and `92dfebd` (audit
  documentation).
  The current v5
  receipts bind `candidate_implementation_commit` and
  `execution_code_commit` to `65e74b2`; the remote branch still points to
  `f17e99a` because no push has been made in this continuation.
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

The prior canonical v4 evidence remains under
`evals/results/phase004c5-pr12-7h/development-v4/`. After restoring the
historical roots and moving current code to a governed case-owned path, the
latest local v5 evidence is under
`evals/results/phase004c5-pr12-7h/development-v5/`:

| case | attempt | valid runs | terminal | evidence SHA-256 |
| --- | ---: | ---: | --- | --- |
| 2022 C | 11 | 3/3 | `READY_FOR_PAPER_HANDOFF` | `BDB38F18F6A5AEC70779316296A2E6E49E6E584AF133A9CAF86FD861E4B954D5` |
| 2021 C | 5 | 3/3 | `READY_FOR_PAPER_HANDOFF` | `6D0F00EC8EC6850806941CDC79D3650940886A79B5CF590FF8B5520C1276ED72` |

Both receipts bind `84087c71d1a20501771e95851ad42e4662cbbdc9`, report
`PROVISIONAL_ENGINEERING_REGRESSION`, have `claim_gate=PASS` and
`handoff_gate=PASS`, and contain explicit `DEVELOPMENT_NO_FINAL_EVALUATION`
with `authorized=false,count=0`.

The v5 receipts supersede v4 for the local Development audit, without
rewriting v4 or any formal artifact:

| case | attempt | valid runs | elapsed seconds | terminal | evidence SHA-256 |
| --- | ---: | ---: | ---: | --- | --- |
| 2021 C | 13 | 3/3 | 40.848093 | `READY_FOR_PAPER_HANDOFF` | `7998729212608dd05c9535e3703a0e82ee6dd31b1404850b7d4c61fe4f19e2aa` |
| 2022 C | 13 | 3/3 | 51.380819 | `READY_FOR_PAPER_HANDOFF` | `7910619cea68f14fc49d618f92de542bf89dc740ce983f647fdd5b2143d9ee55` |

Attempt 012 is retained as a failed trusted-freeze observation
(`RC_TRUSTED_FREEZE_REGISTRY_MISSING`) and is not counted as a run. Both v5
receipts bind the new code to `65e74b2`, report
`DEVELOPMENT_NO_FINAL_EVALUATION`, `final_evaluator_invoked=false`, and
`test_access.authorized=false,count=0`; they are not Validation or scientific
quality conclusions.

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
- Latest LF-worktree `python -m pytest -q` was allowed to continue past its
  first failure and was stopped after the summary at `362 passed, 1 failed` in
  `1732.55 seconds`. The failure was
  `test_legal_predictive_after_evaluate_final_reaches_handoff`: its Windows
  subprocess invocation of `finalize_fresh_c_validation.py` exceeded the
  test's 30-second timeout. The remaining tests were not run, so this is an
  incomplete Windows observation, not a Linux CI result. The earlier CRLF
  frozen-file mismatch did not recur in the LF worktree.
- A Linux-native WSL clone at the same `e3653c2` tree ran the static checker
  subset with Python 3.12 and PyYAML; claim-scope, batch/first-run/postmortem,
  RC4 candidate/batch/unified, 2019, and 2024 freeze/outcome all returned
  `ok=true`. WSL had no pytest/ruff, and `uv` dependency setup failed after
  three PyPI connection timeouts. Linux full pytest and Ruff are therefore
  unverified rather than failed.

Linux-native formal-boundary replay gives the current M4/M5 stop condition:
`check_phase004c4_fresh_validation.py --check` executed successfully but
reported `status=PASS` only for the checker process while retaining substantive
`verdict=C_TARGET_VALIDATION_FAILED`, `run_count=9`,
`delivery_verified=false`, and `workspace_verified=false`.
`check_phase004c4_regressions.py --check` returned `status=PASS` without
promoting that verdict. `check_phase004c4_rc7_release.py` returned `BLOCK` for
both candidate and live stages: candidate had
`RC7_CANDIDATE_EVIDENCE_DRIFT` for actual_controller,
neutral_actual_controller_e2e, and runtime_core, plus
`RC7_CANDIDATE_LIVE_STATE_PREMATURE_OR_INVALID`; live retained those drifts
and added `RC7_RELEASE_LIVE_VERSION_OR_TREE_INVALID`. No unfamiliar case was
opened because the formal prerequisites remain unsatisfied.
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
- The first platform-independent blocker after the merge-tree replay was
  `scripts/check_claim_scope_repair.py --check`:
  `HISTORICAL_EVIDENCE_DRIFT` for the 2021 C supply-plan code and the 2022 C
  model-pipeline code. Their preflight hashes are unchanged, while the
  current files contain the new cardinality fields and repeated grouped-CV
- diagnostic. This is a legitimate frozen-history guard, not a reason to
  rewrite old hashes or remove the checker. The local repair restored those
  two historical paths and moved the Development code to `development-v5`;
  the Linux-like post-repair checker result is recorded separately below.
- No formal state, historical freeze, or registry was rewritten during this
  audit. The feature branch and PR head remain at `f17e99a`; no new push was
  made. The repair boundary was to move new Development code/evidence into a
  new governed case/freeze while leaving the historical case roots immutable.

## Post-repair checker replay

The local LF worktree at `da73cc4` confirms the original platform-independent
root cause is repaired: `check_claim_scope_repair.py --check` passes with
`held_out_unchanged=true` and `old_validation_unchanged=true`. Ruff,
`validate_repo --strict`, batch freeze, first-run freeze, postmortem, RC4
candidate, RC4 batch-regression, unified-regression, and phase-004C2
consistency checks also pass.

The Windows replay then exposed path-only checker defects. Commit `bcc3fca`
normalizes the 2019 `git show` path and the 2024 registry path comparisons to
POSIX form. The resulting substantive diagnostics are now visible: 2019 has
three historical release/freeze binding or delivery errors; 2024 has seven
pre-run and three terminal freeze/delivery/protocol errors. These are formal
historical-artifact blockers, not evidence that the new Development runs are
scientifically valid, and the old artifacts were not rewritten.

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
- [2022 v5 Development receipt](../evals/results/phase004c5-pr12-7h/development-v5/CUMCM-2022-C-DEVELOPMENT-BATCH-001/development_regression_evidence.json)
- [2021 v5 Development receipt](../evals/results/phase004c5-pr12-7h/development-v5/CUMCM-2021-C-DEVELOPMENT-BATCH-002/development_regression_evidence.json)
