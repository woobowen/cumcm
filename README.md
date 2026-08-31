# CUMCM Modeling Evidence Lab

Foundation repository for a single Codex Skill that will eventually support the CUMCM modeling chain from problem intake to a validated, reproducible evidence package for a separate paper team.

Current project version: `0.2.1-automated-adjudication`. The formal Skill remains
`0.1.0-foundation` and `SCAFFOLD_ONLY`. Phase 002A freezes and reclassifies Phase 002 evidence,
separates coverage/correctness/process evidence, excludes recovery from rank, and implements
non-voting automated adjudication. The current real Blind Judge run is
`AUTOMATED_ADJUDICATION_INCOMPLETE` after three transport failures; no architecture or component is
selected, no third-party code is integrated, and Phase 003 is not allowed.

Start with `AGENTS.md`, then read `GOALS.md`, `WORKFLOW.md`, the active plan, and `state/project_state.json`. Run `bash scripts/bootstrap_dev_env.sh` and `bash scripts/ci.sh` for local validation.

No project license has been selected. Third-party repositories remain isolated under ignored `.cache/upstream/` and are not part of this repository.
