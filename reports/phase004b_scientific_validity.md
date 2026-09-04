# Phase 004B First-Run Scientific Validity

## Model boundary

The portfolio used a spatial air-temperature profile interpolated between ambient and zone-center
setpoint anchors. It compared a single-capacitance lag, a two-capacitance surface/core network and a
single-state heating/cooling-asymmetric control. Conveyor position was mapped by `x=v t`; all speed
calculations converted `cm/min` to `cm/s` once. Effective parameters were fitted by bounded least
squares to the first 80% of ordered measurements.

## Valid and invalid conclusions

The code executed real calibration, forward simulation, process-metric recomputation and bounded
search. Declared and implemented model identities match, units are internally consistent, and raw
inputs remained immutable. However, no Run passed the full requirement set. There is therefore no
selected model, valid Q1–Q4 result, Final Run, Claim or paper handoff in the first run.

The high cooling-window validation errors indicate that the fixed spatial air-profile assumption
and/or calibration split does not transfer adequately into the cooling tail. The one-node baseline
and asymmetric control found no Q2-feasible maximum speed under the implemented profile. The
two-node path also exposed a Q4 feasible-pool implementation defect. Global optimality was never
proved. Any reported intermediate curves or feasible samples remain diagnostic only.

## Audit decision

`BLOCK`. A total score cannot compensate for zero successful Runs, no successful baseline,
unsealable failed outputs, or absent Final/Claim/handoff evidence.
