# RC9 scientific contracts

`experiment_plan.metric_definitions` maps each metric ID to the exact definition also recorded in
its requirement's `metric_contracts`. The definition has these fields:

```json
{"target":"battery_remaining_time","quantity":"REMAINING_TIME","target_unit":"min",
 "unit":"%","prediction_origin":"PER_SAMPLE","formula":"ABSOLUTE_RELATIVE_ERROR",
 "denominator":"TRUE_REMAINING_TIME","sample_unit":"historical_state_origin",
 "aggregation":"MEAN","weights":"UNIFORM","direction":"MIN","zero_denominator_policy":"REJECT"}
```

Time-error samples contain sample_id, target, unit, origin, predicted_end_time, observed_end_time.
The kernel derives remaining times by subtracting the origin from both endpoints. It never infers
remaining time from a metric label. `EXCLUDE_WITH_COUNT` retains excluded IDs and cannot yield an
empty aggregate. Only explicit uniform weighting is currently supported; weighted objectives need
a new reviewed formula contract. `SQUARED_ERROR` with `ROOT_MEAN` produces RMSE in target units.

`temporal_design` contains schema_version=temporal-visibility/v1, task=SAME_ENTITY_FUTURE or
NEW_ENTITY_GENERALIZATION, a hash-bound JSON index_path, and samples. Each sample declares sample_id,
entity_id, origin, target_time, split (VALIDATION or FORECAST), target_observation_id (null for an
unknown forecast), feature_observation_ids, preprocess_fit_observation_ids and model_fit_observation_ids.
The index contains observations with observation_id, entity_id, observed_at, available_at and value.
All consumed observations must be available at the corresponding origin. Historical validation
labels remain outside those consumption lists. This lineage is verified against independently
recomputed outputs; it is not operating-system isolation from arbitrary untrusted model code.

A predictive requirement's prediction_spec freezes kind=CONDITIONAL_ESTIMATE, claim_type=PREDICTIVE,
target_field, future_truth_field, known_input_fields, model_basis, conditions,
historical_validation_required=true and empirical_accuracy_required. The future truth field is not a
minimum computation input. The claim and captured prediction evidence retain actual history metrics,
explicit predictions and uncertainty.kind=MODEL_SENSITIVITY or UNCALIBRATED_POINT_ESTIMATE with
calibrated=false. Empirical accuracy requirements cannot be satisfied by this conditional route.

The neutral implementation examples are first-party fixtures in tests/fixtures/rc9_science_model.py
and rc9_science_checker.py. They illustrate protocols, not battery scientific performance.
