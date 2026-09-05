# Phase 004C3 release integrity

RC5 remains immutable and release-blocked by `RC5_VERSION_FILE_MISMATCH`. The RC6 candidate aligns
root VERSION, Skill VERSION, SKILL metadata, runner and discovery at project
`0.3.0-competition-rc6` / Skill `0.2.0-competition-rc6`. The lightweight
`scripts/check_skill_release_consistency.py --check` uses the same pure snapshot evaluator as the
frozen negative tests.

Release is not yet accepted: the live project state intentionally remains
`0.2.0-competition-rc5-blocked`, and `evals/results/phase-004c3/rc6_release.json` does not exist until
historical regressions and Auditor 1 pass. No fresh Validation input may be read before that remote
freeze. The historical RC5 block record is still present and checked.
