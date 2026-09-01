# Upstream Dynamic Evaluation

Status: `PROPOSAL_ONLY`; `GATE_BASE_SELECTION_PENDING` is open.

## Method and integrity

Six deterministic synthetic cases compared one neutral no-project-Skill baseline with two
sanitized instruction-only candidate packages using `gpt-5.4`, `medium`, and
`workspace-write`. All 18 initial 70/30 scores were frozen before identity reveal. No
third-party code or dependency was executed or installed, no MCP or remote was configured,
and no historical answer material was used.

## Cases

| Case | Purpose | Injected risks | Deterministic oracle | Status | Case fixture hash |
|---|---|---|---|---|---|
| CASE-001 | Measure requirement coverage and reality discipline | omission, uncontrollable_variable, unit_conversion, correlation_causation | `oracle.json` | `FROZEN` | `cbce5160d3fd8001b2a07598a8d40f42bc909997f19242a856a94e939c9f0783` |
| CASE-002 | Measure injected data-fault detection and safe cleaning | missing, duplicates, units, temporal_leakage, entity_leakage, target_leakage, class_imbalance | `oracle.json` | `FROZEN` | `0b980cfad46fe95112fc8c9af8d0212dc47f5a5caac71344a34668b5e20441f0` |
| CASE-003 | Measure formulation, executable evidence, baseline, and optimum | invented_constraint, infeasibility, false_optimum, unrun_code | `oracle.json` | `FROZEN` | `8ac0451a7e3c2ca450f4eb5416d1605eceaaacefc160a2972687884bf6e5db0b` |
| CASE-004 | Measure temporal validation, leakage avoidance, and robustness | future_leakage, target_leakage, concept_drift, missing, extreme, causal_overclaim | `oracle.json` | `FROZEN` | `1c69cc66b0ce84ad33c942a2512eafa4c18f23f77415e9dbcfe299a358a44e8c` |
| CASE-005 | Measure dependency invalidation and safe recovery | partial_stale, manual_validity_edit, history_loss, paper_stale_flow | `oracle.json` | `FROZEN` | `ca9b3541acf6939ed5828d20e0094dc11111e524eab7a226eaa4d80be0e03693` |
| CASE-006 | Measure source hierarchy, support, and assumption adaptation | fabricated_source, unsupported_claim, assumption_mismatch, causal_overclaim | `oracle.json` | `FROZEN` | `daa06f65def35260c664e49300f10cfc99db21d77c27620fb8dcca43865ffe66` |

## Revealed arms and frozen scores

Medians are across six cases. Completed/failed count all retained real attempts; two failed
CASE-001 attempts were followed by the only two allowed calibration runs.

| Arm | Revealed candidate | Mode | Planned cells | Completed runs | Failed runs | Not-run | Hard failures | Deterministic median /70 | Reviewer median /30 | Total median /100 | Total range | Confidence |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| ARM-A | YUSHUI | SANITIZED_INSTRUCTION_ONLY_WITH_LICENSE_BLOCKER | 6 | 5 | 2 | 0 | 0 | 34.0 | 26.0 | 60.0 | 32.0–79.0 | 1/6 LOW |
| ARM-B | NO_PROJECT_MODELING_SKILL | NEUTRAL_BASELINE | 6 | 5 | 1 | 0 | 0 | 37.5 | 25.5 | 62.5 | 35.0–82.0 | 1/6 LOW |
| ARM-C | HANDSOMEZR | SANITIZED_INSTRUCTION_ONLY | 6 | 3 | 4 | 0 | 0 | 34.0 | 26.0 | 60.5 | 23.0–83.0 | 3/6 LOW |

## Runtime inventory

- Retained real runs: 20/20 budget (13 completed, 7 failed, 0 not-run).
- Calibration: 2/2 used; no further real run is permitted.
- Total retained duration: 2847.841679 seconds.
- Observable token usage: 3461771 input and 143300 output tokens.
- Current score cells: 18/18; five are recovery-affected and forced to LOW confidence.
- Process outcomes: every retained process exited 0 and every workspace reported no remote.

## Result interpretation

The native baseline has the highest median total (62.5), followed by HANDSOMEZR (60.5)
and YUSHUI (60.0). The small spread, single current observation per cell, and uneven
recovery effects do not justify automatic selection. CASE-004 and CASE-005 expose shared
critical gaps, so the proposal is a native clean-room architecture with the neutral baseline
as fallback—not adoption of a score winner.

## Limitations

- Synthetic cases do not establish real CUMCM performance.
- Sanitized text packages do not establish full upstream runtime behavior.
- YUSHUI remains `UNKNOWN_NO_LICENSE` and contaminated source material was excluded.
- HANDSOMEZR has external/corpus exclusions and its full repository was not executed.
- Five score cells depend on append-only parser recovery while original FAILED manifests remain.
- Dynamic quality, legal reusability, technical integrability, security, and maintenance are separate decisions.
