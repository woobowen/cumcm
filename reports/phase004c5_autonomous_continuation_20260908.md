# Phase 004C5 autonomous continuation record

Status: `IMPLEMENTED_NOT_RC8` / `DEVELOPMENT_REGRESSION_NOT_COMPLETED`

Branch: `feat/phase004c5-p0-01-finalization-hf22-repro`  
PR: `#12` Draft, base `main`  
Start ledger: `2026-09-07T23:29:10.4545963+08:00` (Asia/Shanghai)  
Last checkpoint: `2026-09-08T00:59:21.6256141+08:00` (Asia/Shanghai)

This record covers the authorized continuation from the PR head. It does not change the
formal RC7 state, frozen 2017 Validation artifacts, answer status, or the 2025 C reserve.
No independent Validation or new numeric Run was created.

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
5. Checked the authorized historical C route. The required ignored input/workspace cache is
   absent, so no 2021/2022 or fallback 2020/2023 numerical batch was started.

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
- `ruff check .`, `ruff format --check .`, `scripts/validate_repo.py --strict`, and
  `git diff --check`: passed.
- Existing RC4 batch evidence checker without workspace verification: passed for all three
  registered cases.

The 2,086-test full pytest invocation was intentionally stopped after a slow early segment once
it had produced environment-dependent CRLF hash failures. It is not reported as a full-suite
pass. The affected transport and repository-validator groups were then rerun to completion and
passed after the narrowly scoped portability repairs.

## Historical C boundary

The default 2021 C and 2022 C Development route requires the ignored, hash-bound
`.cache/official_inputs` workspaces. The directory is absent on this machine; exact checks also
show that the 2020 C and 2023 C fallback workspaces are absent. Existing tracked RC4 evidence is
read-only historical evidence, not a fresh current-code Run. Its content checker passes, while
workspace verification reports only the missing workspace/prior-workspace records.

Therefore the requested historical numerical Development Regression remains `NOT_RUN:
AUTHORIZED_INPUT_WORKSPACE_MISSING`, not PASS, not Validation, and not evidence of generalized
C-target performance. The next legal continuation is to reacquire the named official inputs
through the documented authorized route, verify their registered hashes, and run the current
entrypoint in isolated `DEVELOPMENT_REGRESSION` workspaces.

## Delivery boundary

No version bump, formal-state mutation, merge, force push, main push, 2017 artifact mutation,
2025 access, benchmark-vault access, credential access, or paid/third-party execution occurred
in this continuation. The branch is ready for the authorized push after final remote checks.
