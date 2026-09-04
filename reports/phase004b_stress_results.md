# Phase 004B — Mechanistic Stress Results

All variants are derived from the same Development problem without answer use. They test semantic
robustness and are not independent historical cases or generalization proof. Each variant ran a
baseline and primary candidate through the complete main chain to `READY_FOR_PAPER_HANDOFF`, then
mutated its configuration only in a copied probe to verify `STALE` propagation.

## Stress A — units and time

Measurement time was converted from seconds to minutes and temperature from Celsius to Kelvin.
Tracked conversion metadata applies `time_s=time_min*60` and `temperature_c=temperature_k-273.15`.
The selected model, Q2 speed and calibration score are invariant within tolerance: Q2 difference is
zero and score difference is `1e-8`. Both Runs exit zero and seal. The transformed workbook and
configuration hashes differ from the original; the mutation probe is `STALE`.

## Stress B — equivalent segmented process

The coordinate-defined process rows were deterministically shuffled and one constant-setpoint zone
was split into two adjacent equivalent segments. The case code sorts by coordinates and reconstructs
the process rather than trusting file order. Selected model, Q2 speed and validation score are
unchanged; both Runs exit zero and seal. The changed configuration invalidates the old bindings and
the probe becomes `STALE`.

## Stress C — degraded observations

Seven preregistered noncritical calibration rows were removed, Gaussian noise with seed `20260907`
and sigma `0.2` °C was added, and values were rounded to `0.1` °C. The Skill does not crash; both
Runs exit zero and seal. Validation RMSE moves from `5.80972512` to `5.82804722` °C, fitted values
are reported as `[52.5, 171.4]` with four significant digits, and degradation details enter
uncertainty. The selected model and feasibility conclusion remain stable, but the altered metrics
and precision are not claimed invariant. The mutation probe becomes `STALE`.

All three handoffs pass and all three stale chains include changed variant metadata, the experiment
plan and both manifests. No Stress failure was hidden or used as Validation evidence.
