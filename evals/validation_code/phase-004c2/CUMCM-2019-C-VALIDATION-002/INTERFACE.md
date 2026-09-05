# Fresh 2019 C worker interface

This directory contains independently authored case code. It contains no model results.
The worker has not run any numerical model before pre-run remote delivery.

## Main-agent preparation

1. Initialize the private case with the frozen RC5 `init --kind general`. Only the main agent
   owns `case_state.json` and all accepted artifacts.
2. Copy `pipeline.py` and `independent_checks.py` together into `models/runtime/` in that case.
   Copy the official PDF byte-for-byte to `data/raw/problem.pdf`. Its SHA256 is
   `e6c3bcbfdb92c633d49712fff7a2ef4bfc9dbaf540b1de4036b0e71503d962d0`.
3. Copy `experiments/scenario_assumptions.json` and the non-result probe from the proposal case.
   Map these DRAFT content records into the native artifact paths via `core.artifact(...)`:

| Proposal | Native artifact |
|---|---|
| `problem/proposed_problem_requirements.json` | `problem/problem_requirements.json` |
| `research/proposed_research_plan.json` | `research/research_plan.json` |
| `research/proposed_source_ledger.json` | `research/source_ledger.json` |
| `models/proposed_assumptions_and_symbols.json` | `models/assumptions_and_symbols.json` |
| `experiments/proposed_data_audit.json` | `data/data_audit.json` |
| `models/proposed_model_candidates.json` | `models/model_candidates.json` |
| `experiments/proposed_experiment_plan.json` | `experiments/experiment_plan.json` |

4. Advance native stages serially through `MODELS_PROPOSED`; call
   `preflight-output --path experiments/selected_output_contract_probe.json` there.
   The worker has already passed the exact native validator in a stateless call; the stateful
   CLI call remains the orchestrator's responsibility.
5. Commit the copied code and unchanged RC5 runner first. Set `code_commit` to that actual commit;
   fill `required_code_files` for `models/runtime/pipeline.py`, its sibling checker and the native
   Skill runner, using their actual repository paths and matching Git blob SHA256 values.
   Freeze actual `handoff_generated_at`, set the two preparation booleans, and calculate the nine
   native `trusted_freeze_registry` entries. Commit/push/verify the complete pre-run freeze.
   DRAFT placeholders are not executable freeze bindings.

## Execution after explicit freeze authorization

The runtime entrypoint accepts the exact native argv:

```text
models/runtime/pipeline.py --case-root . --candidate-id CANDIDATE --seed SEED --output runs/RUN-ID/output.json
```

`--mode execute` is the default. `--mode describe` writes interface metadata only;
`--mode contract-probe` writes marked numerical placeholders only. Neither mode is a Run.
Runtime dependencies are Python 3.11 standard library plus the sibling independent checker.
No package was installed.

The frozen matrix is these three candidates in this order, each with seeds `101, 202, 303`:

- `BASELINE_STATIC_FCFS`
- `PRIMARY_NHPP_CREDIT`
- `CONTROL_FLUID_AGING`

For each pair, invoke native `execute` once, using a unique preregistered Run ID and
`--timeout-seconds 900`. Do not invoke the pipeline directly for trial numerical runs.
No fitting, threshold or code changes are allowed after observing a Run. Model failures are
retained; no score is assigned to a non-successful attempt. The 4-hour one-shot outer budget is
additional to the per-Run timeout and must be enforced by the orchestrator.

## Selection, test access, seal and final artifacts

1. Read only `validation_metrics.opportunity_loss_cny` from captured successful outputs for
   selection. Group by candidate, average the frozen three repeats, take the smallest mean,
   then the lexicographically smallest candidate ID on exact ties. Failures and all hard gates
   remain separate from this comparison. Never use Final or test values to select a candidate.
2. Freeze the exact native selection decision payload/hash before test disclosure.
3. `sealed_test_metrics_b64` is a top-level base64 JSON string; verify its decoded bytes against
   top-level `sealed_test_payload_sha256`. Its JSON contains `test_metrics`, candidate ID, seed,
   independent checks and an assumption-only source label. Decode only the chosen candidate's
   first successful Run ordered by `(str(seed), run_id)`, exactly once, and record the actual
   access receipt. Every candidate's test results were computed by frozen code using independent
   evaluation streams and the same training-selected policy. Base64 is an accidental-viewing
   guard only; it is not encryption or operating-system isolation.
4. Seal every capture with the same native selection decision hash. The main agent's controller
   builds `model_comparison` from exact captured metrics and all manifests, records
   `test_access={authorized:true,count:1,used_for_selection:false}` only after the real access,
   and calls `compare-check`/native state advancement.
5. Build `robustness_analysis` and `final_result` by copying the exact selected-output fields and
   selected manifest bindings, then invoke native `finalize`. `final_metrics` in this pipeline
   explicitly summarize validation scenarios. They are not test metrics. The decoded test
   diagnostic is an additional receipt, not an invented replacement for captured Final values.
6. Build local claims from captured `requirement_claims`. Each local evidence list contains
   the current Run's actual case-relative output path, passed dynamically from `--output`, plus
   accepted source, audit, assumptions or model artifact paths. The non-result probe references
   `experiments/selected_output_contract_probe.json`; it never references a fabricated Run.
   The aggregate evidence is exactly comparison,
   robustness, Final and the selected output. Bind all native hashes and call
   `derive_claim_contract` → `claim-check` → native `handoff` through the orchestrator.

The required local claims preserve all four PRIMARY requirements. `REQ-Q2` supports the truthful
finding that real airport/city data are missing. It does not support completed empirical modeling.
Even if the native evidence-package chain validates the conditional statements, the independent
Validation rubric must still enforce `VALIDATION_PRIMARY_EMPIRICAL_DATA_MISSING`. It must also
inspect every other hard failure. No structural Claim/Handoff success overrides that primary gap.

## Evidence interpretation

Q1 uses assumed flight-exit NHPP demand, Gamma cumulative-intensity inversion, and an explicit
outside-earning opportunity model. Its baseline is constant-intensity analytic, main candidate
uses Monte Carlo expected waiting, and control uses deterministic fluid inversion. Intervals
use fixed-state stratified Monte Carlo error; they do not estimate empirical parameter uncertainty.

Q3 compares a frozen finite set of batch geometries under saturated queues. Its chosen main
configuration maximizes the sampled training capacity. Each validation event ledger is checked
independently for geometry, phase ordering, stationary boarding, clearance, release headway and
pedestrian/vehicle exclusivity. Real-world site safety remains unverified.

Q4 compares FCFS, capped income-deficit short-trip priority and a fixed-delay short-trip promotion
control. Full round-trip cashflows and end-of-trip exposure are used; tail counts are reported.
An independent checker reconstructs incomes, return times, credit amounts, the seeded exogenous
destination stream, one-use expiry, ordinary-service quota and aging override. The 60-minute
ordinary wait parameter is an override trigger, not a guaranteed upper bound on realized waits.
Fairness improvement is measured, not assumed. Adverse Gini, throughput or delay results remain.

Quantitative robustness is frozen before execution: five Q1 demand/delay/cost perturbations,
two boarding-duration scales and two distance scales. The outer seeds give three independent
repetitions. No real airport, fare schedule, passenger share, geometry or observed wait is claimed.

## Checks completed before freeze

- Python compilation of all three first-party preparation/runtime files.
- Ruff checks on this directory.
- Native `validate_selected_output_contract(..., allow_probe=True)`: PASS.
- Native sensitive-field/path scan on all DRAFT artifacts and the probe: PASS.
- Native structured formula normalization for all seven formulas: PASS.
- All seven DRAFT artifact content hashes match the native canonical hash.

No numerical model, toy numerical case, test metric or actual Run has been executed by this worker.
