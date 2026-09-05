# 2019 C fresh one-shot Validation

Decision: `C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT`; reason `VALIDATION_PRIMARY_EMPIRICAL_DATA_MISSING`. Final case state `REJECTED`; next phase `null`.

Official title: 机场的出租车问题. Official problem/archive were obtained after RC5 remote release. No airport/city observations were supplied or separately acquired. All numerical inputs are registered assumptions; Q2 remains unfulfilled. Answers and 2025 remain sealed.

## Fourteen stages

| Stage | Status | Evidence | Gate/capture time (UTC unless offset shown) | Failure / recovery |
|---|---|---|---|---|
| 1. PROBLEM_INTAKE | PASS_NATIVE_SCOPED | `problem/problem_requirements.json` | 2026-09-05T04:16:55Z | None / none |
| 2. REQUIREMENT_DECOMPOSITION | PASS_NATIVE_SCOPED | `problem/problem_requirements.json` | 2026-09-05T04:16:55Z | None / none |
| 3. RESEARCH_AND_SOURCE_PLANNING | PASS_NATIVE_SCOPED | `research/source_ledger.json` | 2026-09-05T04:16:55Z | None / none |
| 4. ASSUMPTION_AND_SYMBOL_DEFINITION | PASS_NATIVE_SCOPED | `models/assumptions_and_symbols.json` | 2026-09-05T04:16:55Z | None / none |
| 5. DATA_AUDIT | COMPLETE_WITH_PRIMARY_EVIDENCE_GAP | `data/data_audit.json` | 2026-09-05T04:16:55Z | VALIDATION_PRIMARY_EMPIRICAL_DATA_MISSING / none |
| 6. MODEL_PORTFOLIO_GENERATION | PASS_NATIVE_SCOPED | `models/model_candidates.json` | 2026-09-05T04:16:55Z | None / none |
| 7. BASELINE_DEFINITION | PASS_NATIVE_SCOPED | `models/model_candidates.json` | 2026-09-05T04:16:55Z | None / none |
| 8. EXPERIMENT_DESIGN | PASS_NATIVE_SCOPED | `experiments/experiment_plan.json` | 2026-09-05T04:16:55Z | None / none |
| 9. IMPLEMENTATION_AND_EXECUTION | PASS_NATIVE_SCOPED | `validation/run_and_gate_checks.json` | 2026-09-05T04:25:35Z–2026-09-05T04:25:39Z | None / none |
| 10. MODEL_COMPARISON | PASS_NATIVE_SCOPED | `results/model_comparison.json` | 2026-09-05T04:26:41Z | None / none |
| 11. ROBUSTNESS_AND_SENSITIVITY | PASS_NATIVE_SCOPED | `results/robustness.json` | 2026-09-05T04:26:41Z | None / none |
| 12. FINAL_RUN | PASS_NATIVE_SCOPED | `results/final_result.json` | 2026-09-05T04:26:41Z | None / none |
| 13. CLAIM_EVIDENCE_VALIDATION | PASS_NATIVE_SCOPED | `evidence/claim_evidence.json` | 2026-09-05T04:26:41Z | None / none |
| 14. MODELING_TO_PAPER_HANDOFF | NATIVE_CONTRACT_PASS_PAPER_DISPATCH_REJECTED | `handoff/modeling_to_paper.json` | Native gate after 2026-09-05T04:26:41Z; terminal adjudication 2026-09-05T12:28:53+08:00 | VALIDATION_PRIMARY_EMPIRICAL_DATA_MISSING / none |

First eight timestamps identify native acceptance checks, not invented authoring durations. The whole episode began at 11:48:24 +08:00, with a 15:48:24 deadline. Exact per-stage human/agent authoring time is unknown.

## Actual Runs

| Candidate | Repeats | Mean Q1 loss (CNY) | Mean Q3 groups/hour | Mean Q4 income Gini | Mean Q4 groups/hour |
|---|---:|---:|---:|---:|---:|
| BASELINE_STATIC_FCFS | 3 | 0.103674903 | 109.812060 | 0.045393736 | 39.875 |
| CONTROL_FLUID_AGING | 3 | 0.103674903 | 237.542465 | 0.045781108 | 39.875 |
| PRIMARY_NHPP_CREDIT | 3 | 0.103674903 | 332.547781 | 0.050296587 | 39.875 |

All 9 subprocesses exited 0; total captured subprocess time 1.510821 s. Outer orchestration took about 4.44 s. No failed, infeasible, nonconverged, superseded or unsealed actual Run was deleted; those observed counts are zero. All 9 captures and manifests are retained under `runs/`. No retries or post-result edits.

Selection used Q1 validation means only. All three tied exactly; frozen lexicographic selection chose BASELINE_STATIC_FCFS, seed 101. This does not select a joint optimum. The main Q3 configuration uses 5 bays/lane and has greater conditional capacity, while the selected baseline uses 1. Main Q4 mean Gini is worse than baseline; no fairness improvement is claimed.

Q1 uses an NHPP integrated-intensity Gamma inversion and conditional opportunity-cost rule, with constant-rate baseline and fluid inverse control. There are 16 fixed states, 256 training draws/state and 128 independent validation draws/state. Q3 uses a finite preregistered bay set and separate simulated phase/geometry checks; Q4 checks exogenous destination, full-cycle income, one-use credit, expiry, ordinary-service quota and aging. Fixed simulations do not establish global convergence or real-site safety. Five Q1 and two each Q3/Q4 quantitative perturbations were executed.

Selected validation Q1 loss is 0.0847180485 CNY; its conditional Monte Carlo interval is [0.0554696752, 0.1139664219]. These values describe simulation noise, not uncertainty in real airport parameters. Independent inverse residual is 5.6843418861e-14.

The selected test payload was decoded once after the immutable selection hash; test Q1 loss is 0.0992449429, Q3 throughput 107.810993 groups/hour and Q4 Gini 0.0479403396. Test metrics were not used for selection; `final_metrics` remain validation-scenario summaries. Base64 is a policy guard, not cryptographic or OS isolation.

## Claim and handoff disposition

All 4 PRIMARY IDs have structurally exact local Claims, distinct aggregate identity and exact coverage.
Auditor 2 found Q4 semantic support incomplete: the selected output runs FCFS with zero priority,
while the local Claim describes priority evaluation. Nonzero priority results exist in other Runs,
but that local Claim does not directly bind them. Therefore 4/4 semantic Claim completeness is not
established; no Claim/output was revised after seeing results. Run/manifest/code/input/config/output/decision bindings pass. Q2 Claim truthfully reports missing empirical evidence. Seven scoped formulas, symbols, result tables, figure-ready data, limitations and reproduction are present in the canonical native handoff. Native state reached READY_FOR_PAPER_HANDOFF; frozen empirical rubric then appended REJECTED. Candidate handoff is conditional diagnostic evidence, never an accepted paper dispatch.

Machine source: `evals/results/phase-004c2/CUMCM-2019-C-VALIDATION-002/validation/` and the terminal freeze. No reference material was unlocked.

Release acceptance is blocked: frozen Skill VERSION remains RC4 despite RC5 declarations.
No Skill drift occurred, but immutable hashes do not prove internal release consistency.
