# Phase 004C5 autonomous continuation record

Status: `IMPLEMENTED_DEVELOPMENT_REGRESSION_COMPLETED_NOT_RC8`

Branch: `feat/phase004c5-p0-01-finalization-hf22-repro`  
PR: `#12` Draft, base `main`  
Start ledger: `2026-09-07T23:29:10.4545963+08:00` (Asia/Shanghai)  
Last checkpoint: `2026-09-08T01:43:02.3486631+08:00` (Asia/Shanghai)

This record covers the authorized continuation from the PR head. It does not change the
formal RC7 state, frozen 2017 Validation artifacts, answer status, or the 2025 C reserve.
No independent Validation run or formal-state numeric run was created; the two current numeric
runs are Development regressions documented below.

## Checkpoints

1. Re-queried PR #12 and fetched its actual head branch. Local branch is the exact PR head
   branch and started clean.
2. Reproduced the P0 failures on Windows. The first stable causes were Git path separators,
   CRLF versus LF source binding, and serialized Windows relative paths.
3. Implemented and committed the narrow portability repairs. The raw `file_hash` contract for
   inputs, outputs, captures, and sidecars remains unchanged; only source-to-Git binding and
   tracked text verification use LF-normalized text where the contract is text-based.
4. Ran the controller and repository checks listed below. The current formal state remains the
   RC7 terminal Validation failure with the existing blockers.
5. Reacquired the registered 2021 and 2022 archives from the official mcm.edu.cn attachments.
   URL hashes, archive hashes, and all bound C-problem/data hashes match the registration.
   Only problem/data inputs were copied into ignored local workspaces; reference/answer
   material was not included in the execution data hashes.
6. Added a current RC7 Development-only route and repaired two Windows execution boundaries:
   the subprocess receives only the loader-required SYSTEMROOT in addition to the recorded
   deterministic environment, and all state/claim evidence paths use portable POSIX keys.
7. Completed both authorized historical C Development batches. Their evidence is separate from
   the old RC4 artifacts and remains explicitly `DEVELOPMENT_REGRESSION`, not Validation.

## Changes

Local commits ahead of the PR head:

- `3a0022a` — normalize repository paths before `git show` on Windows.
- `84dd8f7` — bind source files with an LF-normalized companion hash while retaining exact
  worktree hashes.
- `a710814` — emit portable POSIX relative paths in captures, manifests, ledgers, and handoff
  evidence.
- `f1d0a77` — preserve legacy raw code-freeze declarations while enforcing Git binding.
- `b54bd97` — normalize tracked text when validating the repository verification manifest.
- `3c361ab` — satisfy the repository lint rule for the text-hash helper.

Additional commits in this continuation:

- `1f2bc63` add the current RC7 C Development-regression route.
- `c291aa1` normalize the RC7 output-contract probe path check.
- `4aee146` preserve the Windows runtime loader environment for controlled subprocesses.
- `96296c3` canonicalize Windows evidence paths at transition and claim boundaries.
- `d156af8` complete the current route's final/claim/handoff transition sequence.

## Verification

Passed on the current branch with CPython 3.11.14:

- P0-01/P0-02/P0-03 integration suite: `17 passed`.
- Fresh controller plus actual-controller black-box, neutral, and adversarial suite: `39 passed`.
- Fault-injection suite: `48 passed`.
- Adjudication, package-builder, and recovery integration subset: `26 passed`.
- Evaluation-runner integration suite: `23 passed`.
- Transport-recovery integration suite: `14 passed`.
- Repository-fault integration suite: `10 passed`.
- Frozen actual/adversarial probe hash checks: `2 passed`.
- Current P0/controller/black-box/neutral/adversarial combined regression after the final
  portability repairs: `48 passed in 263.67s`.
- `ruff check .`, `ruff format --check .`, `scripts/validate_repo.py --strict`, and
  `git diff --check`: passed.
- Existing RC4 batch evidence checker without workspace verification: passed for all three
  registered cases.

The 2,086-test full pytest invocation was intentionally stopped after a slow early segment once
it had produced environment-dependent CRLF hash failures. It is not reported as a full-suite
pass. The affected transport and repository-validator groups were then rerun to completion and
passed after the narrowly scoped portability repairs.

## Historical C boundary

Both default historical C Development batches completed under RC7 with no Final/Validation
evaluator access:

- 2022 C: `CUMCM-2022-C-DEVELOPMENT-RC7-REGRESSION`, attempt 6, 3/3 valid runs,
  selected `HELLINGER_KNN_COMPLETE`, terminal `READY_FOR_PAPER_HANDOFF`.
- 2021 C: `CUMCM-2021-C-DEVELOPMENT-RC7-REGRESSION`, attempt 1, 3/3 valid runs,
  selected `BASELINE_MEAN_GREEDY`, terminal `READY_FOR_PAPER_HANDOFF`.

Evidence files:

- `evals/results/phase004c5-c-batch/CUMCM-2022-C-DEVELOPMENT-BATCH-001/development_regression_evidence.json`
- `evals/results/phase004c5-c-batch/CUMCM-2021-C-DEVELOPMENT-BATCH-002/development_regression_evidence.json`

The 2022 route preserves five earlier harness/environment/path attempts in its ignored
workspace metadata; those failures are not silently discarded. The successful runs are current
RC7 Development evidence only. They do not establish an independent Validation result,
generalized C-target performance, a version release, or permission to access the frozen 2017/
2025 routes.

## Delivery boundary

No version bump, formal-state mutation, merge, force push, main push, 2017 artifact mutation,
2025 access, benchmark-vault access, credential access, or paid/third-party execution occurred
in this continuation. The branch is ready for the authorized push after final remote checks.
