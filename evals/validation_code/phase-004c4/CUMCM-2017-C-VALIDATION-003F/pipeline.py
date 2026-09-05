#!/usr/bin/env python3
"""One-candidate, one-seed executable pipeline for CUMCM-2017-C.

The pipeline is deliberately result-agnostic at preparation time.  A formal
invocation reads the immutable official workbooks, accepts exactly one frozen
candidate ID and seed, applies concentration-group-safe evaluation, and emits
the RC7 selected-output fields plus recomputable prediction evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from prepare_case import (
    CASE_ID,
    EXPECTED_HASHES,
    FEATURES,
    read_data1,
    read_data2,
    verify_raw_inputs,
)
from sklearn.kernel_ridge import KernelRidge
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

REQUIREMENT_IDS = [
    "REQ-1-DATA1-RELATION-QUALITY",
    "REQ-2-DATA2-CONCENTRATION-MODEL",
    "REQ-3-SAMPLE-SIZE-FEATURE-DIMENSION",
]
CANDIDATE_IDS = ["BASELINE_MEDIAN", "RIDGE_LINEAR", "KERNEL_RBF_RIDGE"]
SAMPLE_FRACTIONS = [0.5, 0.75, 1.0]
HEX64 = re.compile(r"[0-9a-f]{64}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_bound_json(path: Path, expected_sha256: str | None) -> tuple[dict[str, Any], str]:
    actual = sha256_file(path)
    if expected_sha256 is not None and actual != expected_sha256:
        raise ValueError(f"payload hash mismatch: {path.name}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"payload must be an object: {path.name}")
    return payload, actual


def _number(value: Any) -> int | float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("non-finite numeric result")
    return int(number) if number.is_integer() else number


def _finite_dict(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {str(key): _finite_dict(value) for key, value in payload.items()}
    if isinstance(payload, (list, tuple)):
        return [_finite_dict(value) for value in payload]
    if isinstance(payload, (np.integer, np.floating)):
        return _number(payload)
    if isinstance(payload, float):
        return _number(payload)
    return payload


class MedianRegressor:
    def __init__(self) -> None:
        self.value_: float | None = None

    def fit(self, features: np.ndarray, target: np.ndarray) -> MedianRegressor:
        del features
        self.value_ = float(np.median(target))
        return self

    def predict(self, features: np.ndarray) -> np.ndarray:
        if self.value_ is None:
            raise RuntimeError("MedianRegressor is not fitted")
        return np.full(shape=(features.shape[0],), fill_value=self.value_, dtype=float)


def make_estimator(candidate_id: str, feature_count: int) -> Any:
    if candidate_id == "BASELINE_MEDIAN":
        return MedianRegressor()
    if candidate_id == "RIDGE_LINEAR":
        return Pipeline(
            [("scale", StandardScaler()), ("model", Ridge(alpha=1.0, fit_intercept=True))]
        )
    if candidate_id == "KERNEL_RBF_RIDGE":
        return Pipeline(
            [
                ("scale", StandardScaler()),
                (
                    "model",
                    KernelRidge(
                        alpha=1.0,
                        kernel="rbf",
                        gamma=1.0 / max(int(feature_count), 1),
                    ),
                ),
            ]
        )
    raise ValueError(f"unknown candidate_id: {candidate_id}")


def fit_predict(
    candidate_id: str,
    train: pd.DataFrame,
    evaluation: pd.DataFrame,
    feature_set: list[str],
) -> np.ndarray:
    if train.empty or evaluation.empty:
        raise ValueError("train and evaluation partitions must be nonempty")
    target = train["concentration"].to_numpy(dtype=float)
    model = make_estimator(candidate_id, len(feature_set))
    model.fit(train[feature_set].to_numpy(dtype=float), target)
    raw_prediction = np.asarray(
        model.predict(evaluation[feature_set].to_numpy(dtype=float)), dtype=float
    ).reshape(-1)
    if not np.isfinite(raw_prediction).all():
        raise ValueError("candidate emitted non-finite prediction")
    # Frozen physical-domain projection.  It certifies feasibility, not optimality.
    return np.clip(raw_prediction, 0.0, float(np.max(target)))


def _group_values(frame: pd.DataFrame) -> list[int | float]:
    return [_number(value) for value in sorted(frame["concentration"].unique())]


def validate_selection_payload(
    payload: dict[str, Any], data1: pd.DataFrame, data2: pd.DataFrame
) -> tuple[dict[str, list[int | float]], list[int | float]]:
    if (
        payload.get("contract_version") != "sealed-split/v1"
        or payload.get("case_id") != CASE_ID
        or payload.get("mode") != "SELECTION"
        or not isinstance(payload.get("payload_id"), str)
        or not HEX64.fullmatch(str(payload.get("sealed_test_payload_sha256", "")))
        or payload.get("raw_input_hashes") != EXPECTED_HASHES
    ):
        raise ValueError("invalid selection split payload")
    d1_map = payload.get("data1_development_groups")
    d2_groups = payload.get("data2_development_groups")
    if not isinstance(d1_map, dict) or not isinstance(d2_groups, list):
        raise ValueError("invalid development group registry")
    substances = set(data1["substance"].unique())
    if set(d1_map) != substances:
        raise ValueError("Data1 development substance registry mismatch")
    normalized_d1: dict[str, list[int | float]] = {}
    for substance, values in d1_map.items():
        if not isinstance(values, list) or len(set(map(float, values))) < 3:
            raise ValueError(f"insufficient Data1 development groups: {substance}")
        available = set(map(float, _group_values(data1[data1["substance"] == substance])))
        requested = set(map(float, values))
        if not requested < available:
            raise ValueError(f"Data1 development groups must be a strict subset: {substance}")
        normalized_d1[substance] = [_number(value) for value in sorted(requested)]
    available_d2 = set(map(float, _group_values(data2)))
    requested_d2 = set(map(float, d2_groups))
    if len(requested_d2) < 3 or not requested_d2 < available_d2:
        raise ValueError(
            "Data2 development groups must be a strict subset with at least three levels"
        )
    return normalized_d1, [_number(value) for value in sorted(requested_d2)]


def validate_final_payload(
    payload: dict[str, Any],
    authorization: dict[str, Any],
    payload_sha256: str,
    candidate_id: str,
    seed: int,
    data1: pd.DataFrame,
    data2: pd.DataFrame,
) -> tuple[
    dict[str, list[int | float]],
    dict[str, list[int | float]],
    list[int | float],
    list[int | float],
]:
    if (
        payload.get("contract_version") != "sealed-split/v1"
        or payload.get("case_id") != CASE_ID
        or payload.get("mode") != "FINAL_TEST"
        or payload.get("raw_input_hashes") != EXPECTED_HASHES
    ):
        raise ValueError("invalid final split payload")
    if (
        authorization.get("contract_version") != "one-shot-test-authorization/v1"
        or authorization.get("case_id") != CASE_ID
        or authorization.get("one_shot_authorized") is not True
        or authorization.get("candidate_id") != candidate_id
        or authorization.get("seed") != seed
        or authorization.get("sealed_test_payload_sha256") != payload_sha256
        or not isinstance(authorization.get("authorization_id"), str)
        or not authorization.get("authorization_id")
        or not HEX64.fullmatch(str(authorization.get("selection_decision_hash", "")))
    ):
        raise ValueError("invalid or mismatched one-shot test authorization")
    d1_dev = payload.get("data1_development_groups")
    d1_test = payload.get("data1_test_groups")
    d2_dev = payload.get("data2_development_groups")
    d2_test = payload.get("data2_test_groups")
    if not isinstance(d1_dev, dict) or not isinstance(d1_test, dict):
        raise ValueError("invalid Data1 final group registry")
    substances = set(data1["substance"].unique())
    if set(d1_dev) != substances or set(d1_test) != substances:
        raise ValueError("Data1 final substance registry mismatch")
    normalized_dev: dict[str, list[int | float]] = {}
    normalized_test: dict[str, list[int | float]] = {}
    for substance in sorted(substances):
        available = set(map(float, _group_values(data1[data1["substance"] == substance])))
        dev = set(map(float, d1_dev[substance]))
        test = set(map(float, d1_test[substance]))
        if not dev or not test or dev & test or dev | test != available:
            raise ValueError(f"invalid Data1 train/test partition: {substance}")
        normalized_dev[substance] = [_number(value) for value in sorted(dev)]
        normalized_test[substance] = [_number(value) for value in sorted(test)]
    available_d2 = set(map(float, _group_values(data2)))
    dev2 = set(map(float, d2_dev or []))
    test2 = set(map(float, d2_test or []))
    if not dev2 or not test2 or dev2 & test2 or dev2 | test2 != available_d2:
        raise ValueError("invalid Data2 train/test partition")
    return (
        normalized_dev,
        normalized_test,
        [_number(value) for value in sorted(dev2)],
        [_number(value) for value in sorted(test2)],
    )


def _subsample_by_group(frame: pd.DataFrame, fraction: float, seed: int) -> pd.DataFrame:
    if fraction >= 1.0:
        return frame.copy()
    selected: list[int] = []
    for group_index, (_, group) in enumerate(
        frame.groupby(["substance", "concentration"], sort=True)
    ):
        count = max(1, int(math.ceil(len(group) * fraction)))
        key = f"{seed}|{group_index}|{fraction:.6f}".encode()
        local_seed = int.from_bytes(hashlib.sha256(key).digest()[:8], "big")
        rng = np.random.default_rng(local_seed)
        chosen = rng.choice(group.index.to_numpy(), size=count, replace=False)
        selected.extend(int(value) for value in chosen)
    return frame.loc[sorted(selected)].copy()


def _prediction_records(
    candidate_id: str,
    train: pd.DataFrame,
    evaluation: pd.DataFrame,
    feature_set: list[str],
    seed: int,
    fold_id: str,
    sample_fraction: float,
) -> list[dict[str, Any]]:
    predictions = fit_predict(candidate_id, train, evaluation, feature_set)
    train_groups = _group_values(train)
    records: list[dict[str, Any]] = []
    for (_, row), prediction in zip(evaluation.iterrows(), predictions, strict=True):
        target = float(row["concentration"])
        error = float(prediction - target)
        records.append(
            {
                "record_id": f"PRED-{fold_id}-{row['source_row_id']}",
                "dataset": str(row["dataset"]),
                "substance": str(row["substance"]),
                "source_row_id": str(row["source_row_id"]),
                "evaluation_group": _number(target),
                "train_groups": train_groups,
                "target": _number(target),
                "prediction": _number(prediction),
                "error": _number(error),
                "absolute_error": _number(abs(error)),
                "squared_error": _number(error * error),
                "feature_set": list(feature_set),
                "sample_fraction": float(sample_fraction),
                "seed": int(seed),
            }
        )
    return records


def _metrics(records: list[dict[str, Any]], scale: float) -> dict[str, Any]:
    if not records:
        raise ValueError("cannot score empty prediction records")
    errors = np.asarray([float(item["error"]) for item in records], dtype=float)
    absolute = np.abs(errors)
    if not np.isfinite(errors).all():
        raise ValueError("non-finite prediction evidence")
    group_mae: dict[str, float] = {}
    group_bias: dict[str, float] = {}
    groups = sorted(set(float(item["evaluation_group"]) for item in records))
    for group in groups:
        selected = np.asarray(
            [float(item["error"]) for item in records if float(item["evaluation_group"]) == group]
        )
        group_mae[str(_number(group))] = float(np.mean(np.abs(selected)))
        group_bias[str(_number(group))] = float(np.mean(selected))
    return _finite_dict(
        {
            "row_count": len(records),
            "group_count": len(groups),
            "mae": float(np.mean(absolute)),
            "rmse": float(np.sqrt(np.mean(errors**2))),
            "nmae": float(np.mean(absolute) / scale) if scale > 0 else 0.0,
            "bias": float(np.mean(errors)),
            "absolute_error_q90": float(np.quantile(absolute, 0.9)),
            "group_mae": group_mae,
            "group_bias": group_bias,
        }
    )


def evaluate_development(
    frame: pd.DataFrame,
    development_groups: dict[str, list[int | float]],
    candidate_id: str,
    feature_set: list[str],
    seed: int,
    sample_fraction: float = 1.0,
    fold_prefix: str = "DEV",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    per_substance: dict[str, Any] = {}
    for substance, groups in development_groups.items():
        subset = frame[
            (frame["substance"] == substance)
            & (frame["concentration"].isin([float(value) for value in groups]))
        ].copy()
        substance_records: list[dict[str, Any]] = []
        for fold_index, held_out in enumerate(sorted(map(float, groups))):
            train = subset[subset["concentration"] != held_out].copy()
            evaluation = subset[subset["concentration"] == held_out].copy()
            train = _subsample_by_group(train, sample_fraction, seed + fold_index)
            fold_id = f"{fold_prefix}-{substance}-{fold_index:02d}"
            substance_records.extend(
                _prediction_records(
                    candidate_id,
                    train,
                    evaluation,
                    feature_set,
                    seed,
                    fold_id,
                    sample_fraction,
                )
            )
        scale = float(subset["concentration"].max() - subset["concentration"].min())
        per_substance[substance] = _metrics(substance_records, scale)
        records.extend(substance_records)
    total_scale = float(frame["concentration"].max() - frame["concentration"].min())
    return records, {"aggregate": _metrics(records, total_scale), "per_substance": per_substance}


def evaluate_final(
    frame: pd.DataFrame,
    development_groups: dict[str, list[int | float]],
    test_groups: dict[str, list[int | float]],
    candidate_id: str,
    feature_set: list[str],
    seed: int,
    fold_prefix: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    per_substance: dict[str, Any] = {}
    for substance in development_groups:
        dev = set(map(float, development_groups[substance]))
        test = set(map(float, test_groups[substance]))
        train = frame[(frame["substance"] == substance) & frame["concentration"].isin(dev)].copy()
        evaluation = frame[
            (frame["substance"] == substance) & frame["concentration"].isin(test)
        ].copy()
        local = _prediction_records(
            candidate_id,
            train,
            evaluation,
            feature_set,
            seed,
            f"{fold_prefix}-{substance}",
            1.0,
        )
        full = frame[frame["substance"] == substance]
        scale = float(full["concentration"].max() - full["concentration"].min())
        per_substance[substance] = _metrics(local, scale)
        records.extend(local)
    total_scale = float(frame["concentration"].max() - frame["concentration"].min())
    return records, {"aggregate": _metrics(records, total_scale), "per_substance": per_substance}


def _as_single_substance_map(groups: list[int | float]) -> dict[str, list[int | float]]:
    return {"二氧化硫": groups}


def data1_quality_scorecards(
    data1: pd.DataFrame, per_substance_metrics: dict[str, Any]
) -> list[dict[str, Any]]:
    scorecards: list[dict[str, Any]] = []
    for substance, frame in data1.groupby("substance", sort=False):
        centroids = frame.groupby("concentration", sort=True)[FEATURES].mean()
        level_values = centroids.index.to_numpy(dtype=float)
        correlations = {
            feature: float(
                pd.Series(centroids[feature].to_numpy()).corr(
                    pd.Series(level_values), method="spearman"
                )
            )
            for feature in FEATURES
        }
        correlations = {
            key: (value if math.isfinite(value) else 0.0) for key, value in correlations.items()
        }
        within = frame.groupby("concentration")[FEATURES].std(ddof=0).fillna(0.0)
        distances = [
            float(
                np.linalg.norm(
                    centroids.iloc[index + 1].to_numpy() - centroids.iloc[index].to_numpy()
                )
            )
            for index in range(max(len(centroids) - 1, 0))
        ]
        metrics = per_substance_metrics[substance]
        supported = metrics["group_count"] >= 3 and metrics["nmae"] <= 0.25
        scorecards.append(
            _finite_dict(
                {
                    "substance": substance,
                    "row_count": len(frame),
                    "distinct_concentration_count": len(centroids),
                    "minimum_replicates_per_level": int(
                        frame.groupby("concentration").size().min()
                    ),
                    "mean_within_level_feature_sd": float(within.to_numpy().mean()),
                    "minimum_adjacent_centroid_distance": min(distances) if distances else 0.0,
                    "maximum_absolute_spearman": max(abs(value) for value in correlations.values()),
                    "spearman_by_feature": correlations,
                    "grouped_oos_nmae": metrics["nmae"],
                    "identifiability_status": (
                        "SUPPORTED_BY_THIS_CANDIDATE"
                        if supported
                        else "NOT_ESTABLISHED_BY_THIS_CANDIDATE"
                    ),
                    "decision_rule": "group_count>=3 AND grouped_oos_nmae<=0.25",
                }
            )
        )
    return scorecards


def run_ablations(
    data2: pd.DataFrame,
    development_groups: list[int | float],
    candidate_id: str,
    seed: int,
) -> dict[str, Any]:
    group_map = _as_single_substance_map(development_groups)
    sample_size: list[dict[str, Any]] = []
    for fraction in SAMPLE_FRACTIONS:
        records, metrics = evaluate_development(
            data2,
            group_map,
            candidate_id,
            FEATURES,
            seed,
            sample_fraction=fraction,
            fold_prefix=f"SAMPLE-{int(fraction * 100):03d}",
        )
        sample_size.append(
            {
                "sample_fraction": fraction,
                "metrics": metrics["aggregate"],
                "prediction_records": records,
            }
        )
    feature_dimension: list[dict[str, Any]] = []
    for dimension in range(1, len(FEATURES) + 1):
        subset_records: list[dict[str, Any]] = []
        for subset_index, feature_tuple in enumerate(itertools.combinations(FEATURES, dimension)):
            feature_set = list(feature_tuple)
            records, metrics = evaluate_development(
                data2,
                group_map,
                candidate_id,
                feature_set,
                seed,
                sample_fraction=1.0,
                fold_prefix=f"DIM-{dimension}-{subset_index:02d}",
            )
            subset_records.append(
                {
                    "feature_set": feature_set,
                    "metrics": metrics["aggregate"],
                    "prediction_records": records,
                }
            )
        feature_dimension.append(
            _finite_dict(
                {
                    "dimension": dimension,
                    "subset_count": len(subset_records),
                    "median_mae": float(
                        np.median([item["metrics"]["mae"] for item in subset_records])
                    ),
                    "minimum_mae": float(min(item["metrics"]["mae"] for item in subset_records)),
                    "maximum_mae": float(max(item["metrics"]["mae"] for item in subset_records)),
                    "subsets": subset_records,
                }
            )
        )
    return {"sample_size": sample_size, "feature_dimension": feature_dimension}


def worst_group_failure(records: list[dict[str, Any]]) -> str:
    grouped: dict[float, list[float]] = {}
    for record in records:
        grouped.setdefault(float(record["evaluation_group"]), []).append(
            float(record["absolute_error"])
        )
    group, errors = max(grouped.items(), key=lambda item: (float(np.mean(item[1])), item[0]))
    return (
        f"worst observed held-out concentration group={_number(group)}; "
        f"mae={float(np.mean(errors)):.12g}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-root", type=Path, default=Path("."))
    parser.add_argument("--candidate-id", required=True, choices=CANDIDATE_IDS)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--raw-dir", type=Path)
    parser.add_argument("--phase", default="selection", choices=["selection", "final"])
    parser.add_argument("--split-payload", type=Path)
    parser.add_argument("--split-payload-sha256")
    parser.add_argument("--authorization-payload", type=Path)
    parser.add_argument("--authorization-payload-sha256")
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.seed < 0 or isinstance(args.seed, bool):
        raise ValueError("seed must be a non-negative strict integer")
    case_root = args.case_root.resolve()
    raw_dir = (args.raw_dir or case_root / "data/raw").resolve()
    input_hashes = verify_raw_inputs(raw_dir)
    data1 = read_data1(raw_dir)
    data2 = read_data2(raw_dir)
    split_path = args.split_payload or case_root / "splits/development_payload.json"
    expected_split_hash = args.split_payload_sha256 or sha256_file(split_path.resolve())
    split, split_hash = load_bound_json(split_path.resolve(), expected_split_hash)
    authorization: dict[str, Any] | None = None
    authorization_hash: str | None = None
    if args.phase == "selection":
        if args.authorization_payload or args.authorization_payload_sha256:
            raise ValueError("selection phase must not receive test authorization")
        d1_dev, d2_dev = validate_selection_payload(split, data1, data2)
        d1_records, d1_metrics = evaluate_development(
            data1, d1_dev, args.candidate_id, FEATURES, args.seed, fold_prefix="D1-DEV"
        )
        d2_records, d2_metrics = evaluate_development(
            data2,
            _as_single_substance_map(d2_dev),
            args.candidate_id,
            FEATURES,
            args.seed,
            fold_prefix="D2-DEV",
        )
        evaluation_boundary = "DEVELOPMENT_GROUPED_OOS"
        test_access = {
            "status": "NOT_AUTHORIZED",
            "access_count": 0,
            "sealed_test_payload_sha256": split["sealed_test_payload_sha256"],
        }
    else:
        if not args.authorization_payload or not args.authorization_payload_sha256:
            raise ValueError("final phase requires a hash-bound authorization payload")
        authorization, authorization_hash = load_bound_json(
            args.authorization_payload.resolve(), args.authorization_payload_sha256
        )
        d1_dev, d1_test, d2_dev, d2_test = validate_final_payload(
            split,
            authorization,
            split_hash,
            args.candidate_id,
            args.seed,
            data1,
            data2,
        )
        d1_records, d1_metrics = evaluate_final(
            data1,
            d1_dev,
            d1_test,
            args.candidate_id,
            FEATURES,
            args.seed,
            "D1-FINAL",
        )
        d2_records, d2_metrics = evaluate_final(
            data2,
            _as_single_substance_map(d2_dev),
            _as_single_substance_map(d2_test),
            args.candidate_id,
            FEATURES,
            args.seed,
            "D2-FINAL",
        )
        evaluation_boundary = "ONE_SHOT_HELD_OUT_CONCENTRATION_GROUPS"
        test_access = {
            "status": "AUTHORIZED_ONCE",
            "access_count": 1,
            "sealed_test_payload_sha256": split_hash,
            "authorization_payload_sha256": authorization_hash,
            "authorization_id": authorization["authorization_id"],
            "selection_decision_hash": authorization["selection_decision_hash"],
        }

    ablations = run_ablations(data2, d2_dev, args.candidate_id, args.seed)
    quality_scorecards = data1_quality_scorecards(data1, d1_metrics["per_substance"])
    req1_macro_nmae = float(np.mean([item["grouped_oos_nmae"] for item in quality_scorecards]))
    sample_half = next(item for item in ablations["sample_size"] if item["sample_fraction"] == 0.5)
    dimension_one = next(item for item in ablations["feature_dimension"] if item["dimension"] == 1)
    final_metrics = _finite_dict(
        {
            "REQ1_MACRO_GROUPED_NMAE": req1_macro_nmae,
            "REQ2_GROUPED_MAE_PPM": d2_metrics["aggregate"]["mae"],
            "REQ3_HALF_SAMPLE_GROUPED_MAE_PPM": sample_half["metrics"]["mae"],
            "REQ3_ONE_DIMENSION_MEDIAN_GROUPED_MAE_PPM": dimension_one["median_mae"],
        }
    )
    req1_claim = (
        f"On the provided Data1 observations, {args.candidate_id} produced a five-substance "
        f"macro grouped-out-of-concentration NMAE of {req1_macro_nmae:.12g}; per-substance "
        "identifiability and data-quality diagnostics are reported without causal interpretation."
    )
    req2_claim = (
        f"On the frozen {evaluation_boundary} boundary for the provided Data2 observations, "
        f"{args.candidate_id} produced grouped MAE {d2_metrics['aggregate']['mae']:.12g} ppm; "
        "the claim is predictive only within the observed attachment scope."
    )
    req3_claim = (
        "For the provided Data2 observations and frozen candidate/split, preregistered "
        f"half-sample grouped MAE was {sample_half['metrics']['mae']:.12g} ppm and median "
        f"one-dimensional grouped MAE was {dimension_one['median_mae']:.12g} ppm; these are "
        "conditional sensitivity results, not causal effects."
    )
    limitations = [
        "The attachments do not identify camera, illumination, paper lot, or acquisition order.",
        "The small number of distinct concentration groups limits external-validity claims.",
        (
            "Repeated readings from one concentration are never split across train and "
            "evaluation, reducing nominal sample size."
        ),
        (
            "Prediction clipping certifies the frozen numeric domain only; "
            "it is not an optimality certificate."
        ),
        (
            "No causal conclusion or extrapolation beyond the observed substances and "
            "concentration range is supported."
        ),
    ]
    failure_cases = [
        worst_group_failure(d2_records),
        (
            "extrapolation outside the observed concentration range was not evaluated "
            "and is unsupported"
        ),
    ]
    output = _finite_dict(
        {
            "contract_version": "cumcm-2017-c-selected-output/v1",
            "case_id": CASE_ID,
            "candidate_id": args.candidate_id,
            "random_seed": args.seed,
            "status": "SUCCESS",
            "phase": args.phase.upper(),
            "ranking_eligible": args.phase == "selection",
            "input_hashes": input_hashes,
            "split_payload_sha256": split_hash,
            "test_access": test_access,
            "evaluation_boundary": evaluation_boundary,
            "validation_metrics": {"REQ2_GROUPED_MAE_PPM": final_metrics["REQ2_GROUPED_MAE_PPM"]},
            "final_metrics": final_metrics,
            "claim_scope": (
                "Provided-empirical association and data-quality assessment for all five "
                "Data1 substances; group-safe predictive concentration modeling for "
                "Data2; and conditional sample-size and "
                "feature-dimension sensitivity, with no causal or global-optimality claim."
            ),
            "requirement_claims": {
                REQUIREMENT_IDS[0]: {
                    "claim_id": "CLAIM-REQ1-DATA1-RELATION-QUALITY",
                    "claim_text": req1_claim,
                    "evidence_artifact_ids": [
                        "EVIDENCE-REQ1-GROUPED-PREDICTIONS",
                        "EVIDENCE-REQ1-QUALITY-SCORECARDS",
                    ],
                },
                REQUIREMENT_IDS[1]: {
                    "claim_id": "CLAIM-REQ2-DATA2-PREDICTION",
                    "claim_text": req2_claim,
                    "evidence_artifact_ids": [
                        "EVIDENCE-REQ2-GROUPED-PREDICTIONS",
                        "EVIDENCE-REQ2-ERROR-ANALYSIS",
                    ],
                },
                REQUIREMENT_IDS[2]: {
                    "claim_id": "CLAIM-REQ3-ABLATIONS",
                    "claim_text": req3_claim,
                    "evidence_artifact_ids": [
                        "EVIDENCE-REQ3-SAMPLE-SIZE",
                        "EVIDENCE-REQ3-FEATURE-DIMENSION",
                    ],
                },
            },
            "requirements": {
                REQUIREMENT_IDS[0]: {
                    "evidence_class": "PROVIDED_EMPIRICAL",
                    "data_sufficiency": "SUFFICIENT_WITH_LIMITATIONS",
                    "selected_output_id": "OUTPUT-REQ1-DATA1-RELATION-QUALITY",
                    "selected_output_types": [
                        "RELATIONSHIP_IDENTIFIABILITY_TABLE",
                        "DATA_QUALITY_SCORECARD",
                        "GROUPED_OOS_PREDICTIONS",
                    ],
                    "metrics": {
                        "REQ1_MACRO_GROUPED_NMAE": req1_macro_nmae,
                        "per_substance": d1_metrics["per_substance"],
                    },
                    "prediction_records": d1_records,
                    "quality_scorecards": quality_scorecards,
                    "support_predicates": {
                        "provided_empirical_source_bound": True,
                        "all_five_substances_covered": len(quality_scorecards) == 5,
                        "grouped_out_of_concentration_evaluation": True,
                        "same_concentration_replicate_leakage_absent": True,
                        "causal_identification_design": False,
                    },
                    "limitations": limitations,
                },
                REQUIREMENT_IDS[1]: {
                    "evidence_class": "PROVIDED_EMPIRICAL",
                    "data_sufficiency": "SUFFICIENT_WITH_LIMITATIONS",
                    "selected_output_id": "OUTPUT-REQ2-DATA2-CONCENTRATION",
                    "selected_output_types": [
                        "CONCENTRATION_PREDICTIONS",
                        "GROUPED_OOS_ERROR_ANALYSIS",
                        "FEASIBILITY_CHECKS",
                    ],
                    "metrics": d2_metrics["aggregate"],
                    "prediction_records": d2_records,
                    "error_analysis": {
                        "group_mae": d2_metrics["aggregate"]["group_mae"],
                        "group_bias": d2_metrics["aggregate"]["group_bias"],
                        "worst_group_case": failure_cases[0],
                    },
                    "support_predicates": {
                        "provided_empirical_source_bound": True,
                        "validation_boundary_frozen": True,
                        "held_out_test_valid": args.phase == "final",
                        "grouped_out_of_concentration_evaluation": True,
                        "same_concentration_replicate_leakage_absent": True,
                        "finite_predictions": True,
                        "prediction_domain_projection_applied": True,
                    },
                    "limitations": limitations,
                },
                REQUIREMENT_IDS[2]: {
                    "evidence_class": "PROVIDED_EMPIRICAL",
                    "data_sufficiency": "SUFFICIENT_WITH_LIMITATIONS",
                    "selected_output_id": "OUTPUT-REQ3-SAMPLE-FEATURE-ABLATIONS",
                    "selected_output_types": [
                        "SAMPLE_SIZE_ABLATION_CURVE",
                        "FEATURE_DIMENSION_ABLATION_TABLE",
                        "PERTURBATION_SENSITIVITY",
                    ],
                    "selection_dependency": "INHERIT_REQ2_SELECTED_RUN",
                    "metrics": {
                        "REQ3_HALF_SAMPLE_GROUPED_MAE_PPM": sample_half["metrics"]["mae"],
                        "REQ3_ONE_DIMENSION_MEDIAN_GROUPED_MAE_PPM": dimension_one["median_mae"],
                    },
                    "ablations": ablations,
                    "support_predicates": {
                        "provided_empirical_source_bound": True,
                        "sample_size_schedule_preregistered": True,
                        "all_feature_subsets_by_dimension_evaluated": True,
                        "evaluation_groups_held_fixed": True,
                        "test_set_not_used_for_ablation": True,
                        "causal_identification_design": False,
                    },
                    "limitations": limitations,
                },
            },
            "figure_ready_data": [
                {
                    "figure_id": "FIG-REQ1-QUALITY",
                    "kind": "TABLE",
                    "data": quality_scorecards,
                },
                {
                    "figure_id": "FIG-REQ2-ERROR-BY-GROUP",
                    "kind": "LINE_OR_TABLE",
                    "data": d2_metrics["aggregate"]["group_mae"],
                },
                {
                    "figure_id": "FIG-REQ3-SAMPLE-SIZE",
                    "kind": "CURVE",
                    "data": [
                        {
                            "sample_fraction": item["sample_fraction"],
                            "mae": item["metrics"]["mae"],
                        }
                        for item in ablations["sample_size"]
                    ],
                },
                {
                    "figure_id": "FIG-REQ3-FEATURE-DIMENSION",
                    "kind": "BAND",
                    "data": [
                        {
                            key: item[key]
                            for key in ("dimension", "median_mae", "minimum_mae", "maximum_mae")
                        }
                        for item in ablations["feature_dimension"]
                    ],
                },
            ],
            "uncertainty": {
                "method": "EMPIRICAL_GROUPED_OOS_ERROR_DISTRIBUTION",
                "req1_per_substance_absolute_error_q90": {
                    key: value["absolute_error_q90"]
                    for key, value in d1_metrics["per_substance"].items()
                },
                "req2_absolute_error_q90_ppm": d2_metrics["aggregate"]["absolute_error_q90"],
                "scope": evaluation_boundary,
            },
            "limitations": limitations,
            "robustness_evidence": {
                "metric": "GROUPED_MAE_PPM",
                "metric_direction": "MIN",
                "perturbations": [
                    {
                        "perturbation_id": "PERTURB-SAMPLE-FRACTION-050",
                        "metric": "GROUPED_MAE_PPM",
                        "result": sample_half["metrics"]["mae"],
                        "evidence": "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS",
                    },
                    {
                        "perturbation_id": "PERTURB-FEATURE-DIMENSION-ONE-ALL-SUBSETS",
                        "metric": "GROUPED_MAE_PPM",
                        "result": dimension_one["median_mae"],
                        "evidence": "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS",
                    },
                ],
                "failure_cases": failure_cases,
            },
            "feasibility": {
                "finite_predictions": True,
                "nonnegative_predictions": all(
                    float(item["prediction"]) >= 0 for item in [*d1_records, *d2_records]
                ),
                "predictions_within_training_maximum": all(
                    float(item["prediction"]) <= max(map(float, item["train_groups"]))
                    for item in [*d1_records, *d2_records]
                ),
                "global_optimality_claimed": False,
                "causal_claimed": False,
            },
        }
    )
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    args.output.resolve().write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "case_id": CASE_ID,
                "candidate_id": args.candidate_id,
                "seed": args.seed,
                "phase": args.phase,
                "output_sha256": sha256_file(args.output.resolve()),
                "output_contract_hash": canonical_hash(output),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
