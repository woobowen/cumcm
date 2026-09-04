# Phase 004B RC3 Skill Changes

## Decision

Exactly one formal-Skill revision cycle was accepted. Frozen first-run failure `GAP-004B-001`
showed that a case-local process can write useful diagnostic JSON and then exit nonzero. RC2
captured the output and exit code but could leave `failure=null`, which made the failed capture
unsealable. This is a generic execution-evidence defect, not a thermal-model recipe.

## RC3 change

`cumcm_case.py` now assigns `RC_EXECUTION_NONZERO_EXIT` whenever a nonzero subprocess exit has no
more specific failure. It retains an existing output or creates a minimal failed output if none
exists. `seal-run` can therefore produce a faithful `FAILED` manifest; validation and comparison
still reject that manifest because only current `SUCCESS` Runs are eligible.

The version is `0.2.0-competition-rc3`. The release is frozen at commit
`8a2a813ff34d8c2701c64ff9d959848e7b88c27c`, Skill Git tree
`a4551c8aa0b6b119823f6ce9df3f0f948339bb33`, and runner SHA-256
`1cdeeb04219e91dddf73eeb730782e31bef6a669061d2873137ad181b6a86f06`.

Changed formal-Skill surfaces were limited to the executor behavior, its generic tests, version
metadata, templates/workflow wording and their consistency contracts. The implementation contains
no case title, year, field name, physical constant, zone, parameter, equation coefficient or
answer-derived branch. `GAP-004B-002` changed only the evaluation freeze tool; `GAP-004B-003` and
`GAP-004B-004` remain case-owned and were rejected from the Skill.

## Verification boundary

The focused generic program writes diagnostic JSON and exits `2`; RC3 captures and seals it as
`FAILED`, and comparison rejects it with `RC_MANIFEST_NOT_SUCCESS:FAILED`. The unchanged success
path was exercised by six 2020 A Development-regression Runs, three 2023 C cross-case Runs and six
mechanistic Stress Runs. This is Development evidence, not Validation or a generalization proof.
