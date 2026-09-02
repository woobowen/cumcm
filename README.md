# CUMCM Modeling Evidence Lab

Foundation repository for a single Codex Skill that will eventually support the CUMCM modeling chain from problem intake to a validated, reproducible evidence package for a separate paper team.

Current project version: `0.2.6-specification-protocol`. The formal Skill remains
`0.1.0-foundation` and `SCAFFOLD_ONLY`. Phase 002A freezes and reclassifies Phase 002 evidence,
separates coverage/correctness/process evidence, excludes recovery from rank, and implements
non-voting automated adjudication. Phase 002B adds deterministic compact role bundles, exact-session
checkpoints, resumable exec, and an App Server fallback. Its real Correctness initial turn and sole
resume both ended in `RESPONSES_CONNECT_RESET`, after three historical Phase 002A transport
failures. Phase 002C treats those failures as retained historical risk and evaluates the frozen
evidence-sufficiency Gate before any candidate-quality semantic Judge. Phase 002D then ran a frozen
new-model cohort for 28 scored starts and retained 18 eligible records. The elapsed budget stopped
the experiment at three historical primary-eligibility balanced cases and repeat depth one. Phase
002D-R1 then classified all outcomes, resolved 23/24 slots and completed independent failure-aware
audits/decisions/replay. Quality remains `EVIDENCE_INSUFFICIENT` at two oracle-passing balanced
cases and depth one; observed reliability is descriptive-only, four mechanisms are accepted only as
specifications, and only a redesigned Phase 002D continuation is allowed. No architecture/base is
selected, no component is implemented, no third-party code is integrated, and Phase 003 is blocked.
Phase 002D-R2 has frozen four clean-room component specifications, their single-truth interaction
contract, three unselected architecture candidates, a prospective sealed Benchmark, 32 metrics and
thresholds, and a later-phase experiment/ablation protocol. All 29 serious adversarial findings have
passing deterministic evidence; the independent Decision Auditor and five-variant offline replay
pass. Shadow authorization remains `RETEST_REQUIRED` on the R2 route. No prototype, model/API
experiment, component implementation, architecture selection or Phase 003 transition occurred.

Start with `AGENTS.md`, then read `GOALS.md`, `WORKFLOW.md`, the active plan, and `state/project_state.json`. Run `bash scripts/bootstrap_dev_env.sh` and `bash scripts/ci.sh` for local validation.

No project license has been selected. Third-party repositories remain isolated under ignored `.cache/upstream/` and are not part of this repository.
