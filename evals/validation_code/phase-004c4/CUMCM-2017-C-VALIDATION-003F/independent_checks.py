#!/usr/bin/env python3
"""Independent recomputation of output metrics, feasibility, and coverage."""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from pipeline import CANDIDATE_IDS, FEATURES, REQUIREMENT_IDS, SAMPLE_FRACTIONS, load_bound_json
from prepare_case import EXPECTED_HASHES, read_data1, read_data2, verify_raw_inputs

TOLERANCE = 1e-9


def close(left: Any, right: Any) -> bool:
    try:
        return math.isclose(float(left), float(right), rel_tol=TOLERANCE, abs_tol=TOLERANCE)
    except (TypeError, ValueError):
        return False


def recompute_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(records, list) or not records:
        raise ValueError("prediction evidence must be a nonempty list")
    errors = np.asarray(
        [float(record["prediction"]) - float(record["target"]) for record in records], dtype=float
    )
    if not np.isfinite(errors).all():
        raise ValueError("non-finite prediction evidence")
    groups = sorted(set(float(record["evaluation_group"]) for record in records))
    group_mae: dict[str, float] = {}
    group_bias: dict[str, float] = {}
    for group in groups:
        selected = np.asarray(
            [
                error
                for error, record in zip(errors, records, strict=True)
                if float(record["evaluation_group"]) == group
            ]
        )
        key = str(int(group)) if group.is_integer() else str(group)
        group_mae[key] = float(np.mean(np.abs(selected)))
        group_bias[key] = float(np.mean(selected))
    return {
        "row_count": len(records),
        "group_count": len(groups),
        "mae": float(np.mean(np.abs(errors))),
        "rmse": float(np.sqrt(np.mean(errors**2))),
        "bias": float(np.mean(errors)),
        "absolute_error_q90": float(np.quantile(np.abs(errors), 0.9)),
        "group_mae": group_mae,
        "group_bias": group_bias,
    }


def check_metric_bundle(
    claimed: dict[str, Any], recomputed: dict[str, Any], prefix: str, failures: list[str]
) -> None:
    for key in ("row_count", "group_count"):
        if claimed.get(key) != recomputed[key]:
            failures.append(f"{prefix}:{key}:mismatch")
    for key in ("mae", "rmse", "bias", "absolute_error_q90"):
        if not close(claimed.get(key), recomputed[key]):
            failures.append(f"{prefix}:{key}:mismatch")
    for key in ("group_mae", "group_bias"):
        if set(claimed.get(key) or {}) != set(recomputed[key]):
            failures.append(f"{prefix}:{key}:coverage_mismatch")
            continue
        for group, value in recomputed[key].items():
            if not close(claimed[key].get(group), value):
                failures.append(f"{prefix}:{key}:{group}:mismatch")


def check_prediction_records(
    records: list[dict[str, Any]],
    raw_index: dict[str, dict[str, Any]],
    allowed_evaluation_groups: dict[str, set[float]],
    prefix: str,
    failures: list[str],
) -> None:
    seen: set[str] = set()
    observed_groups: dict[str, set[float]] = {key: set() for key in allowed_evaluation_groups}
    for record in records:
        if not isinstance(record, dict):
            failures.append(f"{prefix}:non_object_record")
            continue
        record_id = record.get("record_id")
        if not isinstance(record_id, str) or not record_id or record_id in seen:
            failures.append(f"{prefix}:duplicate_or_invalid_record_id")
        else:
            seen.add(record_id)
        row = raw_index.get(str(record.get("source_row_id")))
        substance = str(record.get("substance"))
        try:
            target = float(record.get("target"))
            prediction = float(record.get("prediction"))
            evaluation_group = float(record.get("evaluation_group"))
            error = float(record.get("error"))
            absolute_error = float(record.get("absolute_error"))
            squared_error = float(record.get("squared_error"))
            train_groups = {float(value) for value in record.get("train_groups", [])}
        except (TypeError, ValueError):
            failures.append(f"{prefix}:invalid_numeric_record")
            continue
        if not all(
            math.isfinite(value)
            for value in (target, prediction, error, absolute_error, squared_error)
        ):
            failures.append(f"{prefix}:nonfinite_record")
        if (
            row is None
            or str(row["substance"]) != substance
            or not close(row["concentration"], target)
        ):
            failures.append(f"{prefix}:raw_row_binding_mismatch")
        if not close(target, evaluation_group):
            failures.append(f"{prefix}:evaluation_group_target_mismatch")
        if evaluation_group in train_groups:
            failures.append(f"{prefix}:concentration_group_leakage")
        if not close(error, prediction - target) or not close(absolute_error, abs(error)):
            failures.append(f"{prefix}:error_recomputation_mismatch")
        if not close(squared_error, error * error):
            failures.append(f"{prefix}:squared_error_recomputation_mismatch")
        if (
            prediction < -TOLERANCE
            or not train_groups
            or prediction > max(train_groups) + TOLERANCE
        ):
            failures.append(f"{prefix}:prediction_feasibility_failure")
        if (
            substance not in allowed_evaluation_groups
            or evaluation_group not in allowed_evaluation_groups[substance]
        ):
            failures.append(f"{prefix}:evaluation_group_outside_frozen_boundary")
        else:
            observed_groups[substance].add(evaluation_group)
    for substance, expected in allowed_evaluation_groups.items():
        if observed_groups.get(substance, set()) != expected:
            failures.append(f"{prefix}:{substance}:evaluation_group_coverage_mismatch")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--raw-dir", required=True, type=Path)
    parser.add_argument("--split-payload", required=True, type=Path)
    parser.add_argument("--split-payload-sha256", required=True)
    parser.add_argument("--candidate-id", required=True, choices=CANDIDATE_IDS)
    parser.add_argument("--seed", required=True, type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    failures: list[str] = []
    raw_dir = args.raw_dir.resolve()
    observed_hashes = verify_raw_inputs(raw_dir)
    output = json.loads(args.output.resolve().read_text(encoding="utf-8"))
    split, split_hash = load_bound_json(args.split_payload.resolve(), args.split_payload_sha256)
    data1 = read_data1(raw_dir)
    data2 = read_data2(raw_dir)
    raw_index = {str(row["source_row_id"]): row.to_dict() for _, row in data1.iterrows()}
    raw_index.update({str(row["source_row_id"]): row.to_dict() for _, row in data2.iterrows()})

    if output.get("candidate_id") != args.candidate_id or output.get("random_seed") != args.seed:
        failures.append("candidate_or_seed_binding_mismatch")
    if output.get("status") != "SUCCESS":
        failures.append("output_status_not_success")
    if output.get("input_hashes") != observed_hashes or observed_hashes != EXPECTED_HASHES:
        failures.append("raw_input_hash_registry_mismatch")
    if output.get("split_payload_sha256") != split_hash:
        failures.append("split_payload_binding_mismatch")
    requirements = output.get("requirements")
    if not isinstance(requirements, dict) or set(requirements) != set(REQUIREMENT_IDS):
        failures.append("primary_requirement_coverage_mismatch")
        requirements = {}
    claims = output.get("requirement_claims")
    if not isinstance(claims, dict) or set(claims) != set(REQUIREMENT_IDS):
        failures.append("requirement_claim_coverage_mismatch")
    elif len({item.get("claim_id") for item in claims.values() if isinstance(item, dict)}) != 3:
        failures.append("requirement_claim_id_not_unique")
    for requirement_id in REQUIREMENT_IDS:
        record = requirements.get(requirement_id, {})
        if record.get("evidence_class") != "PROVIDED_EMPIRICAL":
            failures.append(f"{requirement_id}:evidence_class_invalid")
        if not record.get("limitations"):
            failures.append(f"{requirement_id}:limitations_missing")

    if split.get("mode") == "SELECTION":
        d1_eval = {
            substance: {float(value) for value in values}
            for substance, values in split["data1_development_groups"].items()
        }
        d2_eval = {"二氧化硫": {float(value) for value in split["data2_development_groups"]}}
        if (
            output.get("phase") != "SELECTION"
            or output.get("test_access", {}).get("access_count") != 0
        ):
            failures.append("selection_test_access_policy_failure")
    elif split.get("mode") == "FINAL_TEST":
        d1_eval = {
            substance: {float(value) for value in values}
            for substance, values in split["data1_test_groups"].items()
        }
        d2_eval = {"二氧化硫": {float(value) for value in split["data2_test_groups"]}}
        if output.get("phase") != "FINAL" or output.get("test_access", {}).get("access_count") != 1:
            failures.append("final_test_access_policy_failure")
    else:
        raise ValueError("unknown split payload mode")

    req1 = requirements.get(REQUIREMENT_IDS[0], {})
    req1_records = req1.get("prediction_records", [])
    check_prediction_records(req1_records, raw_index, d1_eval, "req1", failures)
    per_substance = req1.get("metrics", {}).get("per_substance", {})
    recomputed_nmae: list[float] = []
    for substance, allowed_groups in d1_eval.items():
        local = [item for item in req1_records if item.get("substance") == substance]
        recomputed = recompute_metrics(local)
        claimed = per_substance.get(substance, {})
        check_metric_bundle(claimed, recomputed, f"req1:{substance}", failures)
        if split.get("mode") == "SELECTION":
            scoped = data1[
                (data1["substance"] == substance) & data1["concentration"].isin(allowed_groups)
            ]
        else:
            scoped = data1[data1["substance"] == substance]
        scale = float(scoped["concentration"].max() - scoped["concentration"].min())
        expected_nmae = recomputed["mae"] / scale if scale > 0 else 0.0
        if not close(claimed.get("nmae"), expected_nmae):
            failures.append(f"req1:{substance}:nmae_mismatch")
        recomputed_nmae.append(expected_nmae)
    macro_nmae = float(np.mean(recomputed_nmae))
    if not close(req1.get("metrics", {}).get("REQ1_MACRO_GROUPED_NMAE"), macro_nmae):
        failures.append("req1:macro_nmae_mismatch")
    if not close(output.get("final_metrics", {}).get("REQ1_MACRO_GROUPED_NMAE"), macro_nmae):
        failures.append("final_metrics:req1_mismatch")

    req2 = requirements.get(REQUIREMENT_IDS[1], {})
    req2_records = req2.get("prediction_records", [])
    check_prediction_records(req2_records, raw_index, d2_eval, "req2", failures)
    req2_recomputed = recompute_metrics(req2_records)
    check_metric_bundle(req2.get("metrics", {}), req2_recomputed, "req2", failures)
    if not close(
        output.get("final_metrics", {}).get("REQ2_GROUPED_MAE_PPM"), req2_recomputed["mae"]
    ):
        failures.append("final_metrics:req2_mismatch")
    if not close(
        output.get("validation_metrics", {}).get("REQ2_GROUPED_MAE_PPM"),
        req2_recomputed["mae"],
    ):
        failures.append("validation_metrics:req2_mismatch")

    req3 = requirements.get(REQUIREMENT_IDS[2], {})
    ablations = req3.get("ablations", {})
    sample_items = ablations.get("sample_size", [])
    if [item.get("sample_fraction") for item in sample_items] != SAMPLE_FRACTIONS:
        failures.append("req3:sample_fraction_schedule_mismatch")
    sample_mae: dict[float, float] = {}
    development_eval = {"二氧化硫": {float(value) for value in split["data2_development_groups"]}}
    for item in sample_items:
        fraction = float(item.get("sample_fraction"))
        records = item.get("prediction_records", [])
        check_prediction_records(
            records, raw_index, development_eval, f"req3:sample:{fraction}", failures
        )
        recomputed = recompute_metrics(records)
        check_metric_bundle(
            item.get("metrics", {}), recomputed, f"req3:sample:{fraction}", failures
        )
        sample_mae[fraction] = recomputed["mae"]

    dimensions = ablations.get("feature_dimension", [])
    if [item.get("dimension") for item in dimensions] != list(range(1, len(FEATURES) + 1)):
        failures.append("req3:feature_dimension_schedule_mismatch")
    dimension_medians: dict[int, float] = {}
    for item in dimensions:
        dimension = int(item.get("dimension"))
        subsets = item.get("subsets", [])
        expected_sets = {tuple(values) for values in itertools.combinations(FEATURES, dimension)}
        observed_sets = {
            tuple(subset.get("feature_set", [])) for subset in subsets if isinstance(subset, dict)
        }
        if observed_sets != expected_sets or item.get("subset_count") != len(expected_sets):
            failures.append(f"req3:dimension:{dimension}:subset_coverage_mismatch")
        maes: list[float] = []
        for subset in subsets:
            feature_set = subset.get("feature_set", [])
            records = subset.get("prediction_records", [])
            check_prediction_records(
                records,
                raw_index,
                development_eval,
                f"req3:dimension:{dimension}:{','.join(feature_set)}",
                failures,
            )
            recomputed = recompute_metrics(records)
            check_metric_bundle(
                subset.get("metrics", {}),
                recomputed,
                f"req3:dimension:{dimension}:{','.join(feature_set)}",
                failures,
            )
            if any(record.get("feature_set") != feature_set for record in records):
                failures.append(f"req3:dimension:{dimension}:feature_binding_mismatch")
            maes.append(recomputed["mae"])
        if maes:
            median = float(np.median(maes))
            dimension_medians[dimension] = median
            for key, expected in (
                ("median_mae", median),
                ("minimum_mae", min(maes)),
                ("maximum_mae", max(maes)),
            ):
                if not close(item.get(key), expected):
                    failures.append(f"req3:dimension:{dimension}:{key}:mismatch")

    if not close(
        output.get("final_metrics", {}).get("REQ3_HALF_SAMPLE_GROUPED_MAE_PPM"),
        sample_mae.get(0.5),
    ):
        failures.append("final_metrics:req3_half_sample_mismatch")
    if not close(
        output.get("final_metrics", {}).get("REQ3_ONE_DIMENSION_MEDIAN_GROUPED_MAE_PPM"),
        dimension_medians.get(1),
    ):
        failures.append("final_metrics:req3_one_dimension_mismatch")

    robustness = output.get("robustness_evidence", {})
    perturbations = {
        item.get("perturbation_id"): item for item in robustness.get("perturbations", [])
    }
    if not close(
        perturbations.get("PERTURB-SAMPLE-FRACTION-050", {}).get("result"), sample_mae.get(0.5)
    ):
        failures.append("robustness:sample_perturbation_mismatch")
    if not close(
        perturbations.get("PERTURB-FEATURE-DIMENSION-ONE-ALL-SUBSETS", {}).get("result"),
        dimension_medians.get(1),
    ):
        failures.append("robustness:dimension_perturbation_mismatch")

    feasibility = output.get("feasibility", {})
    if (
        feasibility.get("finite_predictions") is not True
        or feasibility.get("nonnegative_predictions") is not True
        or feasibility.get("predictions_within_training_maximum") is not True
        or feasibility.get("global_optimality_claimed") is not False
        or feasibility.get("causal_claimed") is not False
    ):
        failures.append("feasibility:summary_invalid")

    required_contract_fields = {
        "candidate_id",
        "status",
        "final_metrics",
        "validation_metrics",
        "claim_scope",
        "requirement_claims",
        "figure_ready_data",
        "uncertainty",
        "limitations",
        "robustness_evidence",
    }
    if not required_contract_fields <= set(output):
        failures.append("selected_output_contract_fields_missing")
    if (
        not output.get("figure_ready_data")
        or not output.get("uncertainty")
        or not output.get("limitations")
    ):
        failures.append("selected_output_downstream_material_missing")

    result = {
        "check_contract_version": "independent-checks/v1",
        "case_id": output.get("case_id"),
        "candidate_id": args.candidate_id,
        "seed": args.seed,
        "status": "PASS" if not failures else "FAIL",
        "checks": {
            "raw_hashes": "PASS" if output.get("input_hashes") == EXPECTED_HASHES else "FAIL",
            "requirement_coverage": "PASS" if set(requirements) == set(REQUIREMENT_IDS) else "FAIL",
            "metrics_recomputed": "PASS"
            if not any("mismatch" in item for item in failures)
            else "FAIL",
            "group_leakage": "PASS" if not any("leakage" in item for item in failures) else "FAIL",
            "feasibility": "PASS"
            if not any(item.startswith("feasibility") for item in failures)
            else "FAIL",
        },
        "failures": sorted(set(failures)),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
