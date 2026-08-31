# Phase 002 evaluation

`configs/phase-002.yaml` freezes the three-arm budget and runtime policy. `cases/phase-002/`,
`fixtures/phase-002/`, and `rubrics/phase-002/` are generated deterministically by
`scripts/generate_eval_fixtures.py`; edit the generator, regenerate, review hashes, and treat all
older results as `STALE`. `results/phase-002/` contains only normalized observations, run manifests,
scores, and summaries—never raw traces or candidate instructions.

All cases are project-authored synthetic tasks. They are not historical CUMCM problems and do not
replace later development, validation, or held-out evaluation.
