# CUMCM Modeling Evidence Lab

Foundation repository for a single Codex Skill that will eventually support the CUMCM modeling chain from problem intake to a validated, reproducible evidence package for a separate paper team.

Current project version: `0.2.3-evidence-sufficiency`. The formal Skill remains
`0.1.0-foundation` and `SCAFFOLD_ONLY`. Phase 002A freezes and reclassifies Phase 002 evidence,
separates coverage/correctness/process evidence, excludes recovery from rank, and implements
non-voting automated adjudication. Phase 002B adds deterministic compact role bundles, exact-session
checkpoints, resumable exec, and an App Server fallback. Its real Correctness initial turn and sole
resume both ended in `RESPONSES_CONNECT_RESET`, after three historical Phase 002A transport
failures. Phase 002C treats those failures as retained historical risk and evaluates the frozen
evidence-sufficiency Gate before any candidate-quality semantic Judge. No architecture or component
is selected, no third-party code is integrated, and Phase 003 remains blocked while 002C is in
progress.

Start with `AGENTS.md`, then read `GOALS.md`, `WORKFLOW.md`, the active plan, and `state/project_state.json`. Run `bash scripts/bootstrap_dev_env.sh` and `bash scripts/ci.sh` for local validation.

No project license has been selected. Third-party repositories remain isolated under ignored `.cache/upstream/` and are not part of this repository.
