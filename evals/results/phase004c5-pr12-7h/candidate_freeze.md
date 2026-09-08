# M3 candidate identity freeze

This is a candidate identity record for the PR12 continuation. It is not a
formal RC8 release and does not authorize a Validation run.

## Git identity

- Repository branch: `feat/phase004c5-p0-01-finalization-hf22-repro`
- Frozen implementation commit: `84087c71d1a20501771e95851ad42e4662cbbdc9`
- Repository tree at implementation freeze: `78654b2de71b2953a3c7c23930568829811e0a02`
- Skill subtree: `bfc3be777fb42e01e40067a3cbb419448454164f`
- Remote branch verification: `git ls-remote` returned the implementation freeze
  SHA before the documentation-only handoff artifacts were added.
- Formal release status: `CANDIDATE_NOT_RELEASED`; the registry's active
  release remains the historical RC7 and the formal project state remains
  `C_TARGET_VALIDATION_FAILED`.

## Bound implementation hashes

| file | SHA-256 |
| --- | --- |
| `.agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py` | `4518112bb49990e19d09c4551c7b95fcc3820640024a94a78b91e070fe431a92` |
| `scripts/run_c_target_rc7_development_regressions.py` | `f0d4e72bfeb627132ba7a78a7b825e2af3f29ed199d83473cc650fb6d39d195f` |
| `scripts/freeze_skill_first_run.py` | `6ba722320d06ee86bce5fefe41d1801a60b72bedc5a99e9da034f00783f4465a` |
| `evals/results/phase-004c-c-batch/CUMCM-2022-C-DEVELOPMENT-BATCH-001/code/model_pipeline.py` | `e4145e77aef95d80238e7fe1aa0e26269fc370be66bf7312d889d7988cb9566c` |
| `evals/results/phase-004c-c-batch/CUMCM-2021-C-DEVELOPMENT-BATCH-002/code/c2021_supply_plan.py` | `cfcb8d9e02a9eafafa4db5c96eb1053b6310a1e59277a83820d600b17a438454` |
| `evals/results/phase-004c-c-batch/CUMCM-2021-C-DEVELOPMENT-BATCH-002/code/c2021_feasibility.py` | `c188edef89d6abff8a74277137de92c2e68fbe9b04aec6bf9c71e64166da1677` |
| `evals/results/phase-004c-c-batch/CUMCM-2021-C-DEVELOPMENT-BATCH-002/scientific_claim_semantics.json` | `803c81a38463b0233f689741be5193ddf30eafbc23412010b3af3819574a9da7` |
| `evals/results/phase-004c-c-batch/CUMCM-2022-C-DEVELOPMENT-BATCH-001/scientific_claim_semantics.json` | `b055496b37c3473bf90f90c30e32d9ee9a252d68c2b57e6684a7b02a9b331a2a` |
| `tests/unit/test_phase004c5_development_evidence.py` | `d96ea071de790f72951d9e4a0fb7c8ace8812df296f0504a73a4c01ef86c83a9` |

## Environment observed in `.venv`

- Python 3.11.14
- NumPy 2.4.6
- SciPy 1.17.1
- scikit-learn 1.9.0
- openpyxl 3.1.5
- pytest 8.4.2

## Checks bound to this candidate

- Neutral Development evidence suite: `5 passed`.
- Ruff checks for the route, neutral tests, and both case-owned model files:
  clean.
- 2022 Development attempt 11: 3 successful candidate runs, claim gate PASS,
  handoff gate PASS, no Final evaluator, evidence SHA-256
  `BDB38F18F6A5AEC70779316296A2E6E49E6E584AF133A9CAF86FD861E4B954D5`.
- 2021 Development attempt 5: 3 successful candidate runs, claim gate PASS,
  handoff gate PASS, no Final evaluator, evidence SHA-256
  `6D0F00EC8EC6850806941CDC79D3650940886A79B5CF590FF8B5520C1276ED72`.
- The first attempt under the new case-owned mapping was intentionally retained
  as an incomplete `RC_TRUSTED_FREEZE_REGISTRY_MISSING` observation because the
  case model formatting change was not yet committed; it was not treated as a
  model or scientific failure.
- The long full-suite pytest runs were not a passing release gate: one emitted
  failures before interruption and the `-x` rerun was interrupted without a
  traceback. With the correct project entry point, collection completed at
  2,091 tests and `-x` stopped at the historical Phase-002 evidence-freeze test
  after `175 passed, 1 failed`; all 120 mismatches were CRLF-only checkout
  differences from the historical LF subject commit. The focused neutral suite
  remains `5 passed`, the related finalization set is `17 passed`, and Ruff/diff
  checks are clean.
- The first-run path-normalization repair is included in this implementation
  freeze and prevents Windows backslash keys from entering evidence hashes.
- A separate read-only numerical review and a separate semantic-registry test
  were completed; neither modified the case workspaces or formal state.

## Formal Validation boundary

M4/M5 are not started. The current candidate has no formal release manifest,
no newly preregistered unfamiliar-case registry entries, no remotely frozen
answer-sealed 2016/2015 first-run workspace, and no clean full release gate.
The exact safe disposition is therefore `VALIDATION_PRECONDITIONS_BLOCKED`,
not a fabricated Validation result. The 2016/2015 official problem inputs are
not accessed in this checkpoint.
