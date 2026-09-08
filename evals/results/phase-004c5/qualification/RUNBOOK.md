# RC8 reproduction and bounded recovery

Use the inherited `.venv/bin/python`; current versions are recorded in `environment.json`.
Core/CLI dependencies are declared in `pyproject.toml`. Development numerical cases additionally
use NumPy, SciPy, pandas and openpyxl at the observed versions; no package was installed this task.
The environment observation is not a tested fresh-install or cross-platform reproduction claim.

Run targeted checks before full CI:

```text
.venv/bin/python -m pytest -q tests/integration/test_rc8_scientific_fact_binding.py tests/integration/test_rc8_nonpredictive_and_final_lifecycle.py tests/unit/test_phase004c5_release_subjects.py
bash scripts/ci.sh
.venv/bin/python scripts/validate_repo.py --strict
.venv/bin/python scripts/render_status.py --check
git diff --check
```

Historical RC7 release checks resolve their original Git subjects; never alter their hashes to
match RC8:

```text
.venv/bin/python scripts/check_phase004c4_rc7_release.py --stage candidate --check
.venv/bin/python scripts/check_phase004c4_rc7_release.py --stage live --check
.venv/bin/python scripts/check_phase004c4_rc7_release.py --release rc8 --stage candidate --check
.venv/bin/python scripts/check_phase004c4_rc7_release.py --release rc8 --stage live --check
```

RC8 candidate must pass while active remains RC7. The candidate snapshot binds a prior implementation
subject and complete shared/test file mapping. Receipts and activation are later commits and may
not change that mapping. A snapshot or Git SHA string without passing bound evidence is insufficient.
Do not open fresh inputs before accepted release and normal push/remote SHA verification.

Development results under `development/v6/results-*` preserve actual execution subjects. Only
recorded current-candidate Run code files that are byte-identical at the qualification subject may
be transferred as scientific regression evidence; never claim those processes ran a later commit.
Original raw inputs remain ignored and required hashes are in each capture. Replaying a model
consumes the registered per-year capture budget (2021 8/9, 2022 7/9 at this checkpoint), so numerical
reproduction is not an instruction to exceed the task budget. Use existing captures and independent
recorded checks first. FAILED captures remain evidence, excluded from ranking.

Fresh episodes follow `FRESH_VALIDATION_PROTOCOL.md`, the frozen Skill and their own case pre-run
freeze. For API details use `.venv/bin/python .agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py --help`.
The actual completion entrypoint is `scripts/finalize_fresh_c_validation.py --case-root CASE`.
No Final retry after result exposure; no terminal restart. If interrupted, inspect current
checkpoint, actual captures and ledgers before taking any action. Unknown completion is not success.

Ignored native audit directories retain exact original command/input files. Published tool receipts
replace only the absolute repository prefix by `.` and retain original hashes. Synthetic probe
scripts are reviewer-owned test evidence; Python recomputation and native audit are distinct.
