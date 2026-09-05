#!/usr/bin/env python3
"""Deterministic input verification and schema audit for CUMCM-2017-C.

This module performs no model fitting.  It preserves the official workbooks,
normalizes their tabular representation in memory, and can write derived CSVs
and a machine-readable audit into the case-owned ignored workspace.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

CASE_ID = "CUMCM-2017-C-VALIDATION-003F"
FEATURES = ["R", "G", "B", "H", "S"]
EXPECTED_HASHES = {
    "CUMCM-2017-problem-C.docx": "f447d3ab2c5a9c70e21a52cf9fa7ccfde4b243615cd1dbfc7d154e9415615adf",
    "Data1.xls": "ee7982ae98ee3d3f9a5762d49e2fa6a780db61ad25fcb09519228d86689636ad",
    "Data2.xls": "6766f5317fd256f86ce28c2c46e101a3c7057af84b9419158bbe824c8c36d723",
    "readme.txt": "bb46f621f6a0aa4d504de3493e92521ce63bb3d78a959f3196dc9b83637acbdf",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_raw_inputs(raw_dir: Path) -> dict[str, str]:
    observed: dict[str, str] = {}
    for name, expected in EXPECTED_HASHES.items():
        path = raw_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"missing required raw input: {path}")
        actual = sha256_file(path)
        if actual != expected:
            raise ValueError(f"raw input hash mismatch: {name}")
        observed[name] = actual
    return observed


def _water_to_zero(value: Any) -> Any:
    return 0.0 if isinstance(value, str) and value.strip() == "水" else value


def _require_numeric(frame: pd.DataFrame, columns: list[str], dataset: str) -> None:
    for column in columns:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
        if frame[column].isna().any():
            raise ValueError(f"{dataset}: missing numeric value in {column}")
        values = frame[column].to_numpy(dtype=float)
        if not all(math.isfinite(float(value)) for value in values):
            raise ValueError(f"{dataset}: non-finite value in {column}")


def read_data1(raw_dir: Path) -> pd.DataFrame:
    frame = pd.read_excel(raw_dir / "Data1.xls", sheet_name="Sheet1", header=0, engine="xlrd").iloc[
        :, :7
    ]
    frame.columns = ["substance", "concentration", "B", "G", "R", "H", "S"]
    frame["substance"] = frame["substance"].ffill()
    frame = frame[frame[FEATURES].notna().any(axis=1)].copy()
    frame["concentration"] = frame["concentration"].map(_water_to_zero)
    frame["concentration"] = frame.groupby("substance", sort=False)["concentration"].ffill()
    frame.insert(0, "dataset", "Data1")
    frame["source_row_id"] = [f"D1-R{index + 2:03d}" for index in frame.index]
    frame["substance"] = frame["substance"].astype(str)
    _require_numeric(frame, ["concentration", *FEATURES], "Data1")
    return frame[["dataset", "substance", "concentration", *FEATURES, "source_row_id"]].reset_index(
        drop=True
    )


def read_data2(raw_dir: Path) -> pd.DataFrame:
    frame = pd.read_excel(raw_dir / "Data2.xls", sheet_name="Sheet1", header=0, engine="xlrd").iloc[
        :, :7
    ]
    frame.columns = ["substance", "concentration", "R", "G", "B", "S", "H"]
    frame = frame[frame[FEATURES].notna().any(axis=1)].copy()
    frame["substance"] = "二氧化硫"
    frame["concentration"] = frame["concentration"].map(_water_to_zero).ffill()
    frame.insert(0, "dataset", "Data2")
    frame["source_row_id"] = [f"D2-R{index + 2:03d}" for index in frame.index]
    _require_numeric(frame, ["concentration", *FEATURES], "Data2")
    return frame[["dataset", "substance", "concentration", *FEATURES, "source_row_id"]].reset_index(
        drop=True
    )


def _json_number(value: Any) -> int | float:
    number = float(value)
    return int(number) if number.is_integer() else number


def _replicate_registry(frame: pd.DataFrame) -> dict[str, Any]:
    registry: dict[str, Any] = {}
    for substance, group in frame.groupby("substance", sort=False):
        counts = group.groupby("concentration", sort=True).size()
        registry[str(substance)] = {
            "row_count": int(len(group)),
            "distinct_concentration_count": int(len(counts)),
            "replicates_by_concentration": {
                str(_json_number(level)): int(count) for level, count in counts.items()
            },
        }
    return registry


def _duplicate_registry(frame: pd.DataFrame) -> list[dict[str, Any]]:
    keys = ["substance", "concentration", *FEATURES]
    duplicate_rows = frame[frame.duplicated(keys, keep=False)]
    records: list[dict[str, Any]] = []
    for values, group in duplicate_rows.groupby(keys, sort=True):
        records.append(
            {
                **{
                    key: (_json_number(value) if key != "substance" else str(value))
                    for key, value in zip(keys, values, strict=True)
                },
                "source_row_ids": sorted(group["source_row_id"].tolist()),
            }
        )
    return records


def _scale_gap_flags(frame: pd.DataFrame) -> list[dict[str, Any]]:
    flags: list[dict[str, Any]] = []
    for substance, group in frame.groupby("substance", sort=False):
        levels = sorted(set(float(value) for value in group["concentration"] if value > 0))
        for lower, upper in zip(levels, levels[1:], strict=True):
            if lower > 0 and upper / lower >= 20:
                flags.append(
                    {
                        "dataset": str(group["dataset"].iloc[0]),
                        "substance": str(substance),
                        "lower_level": _json_number(lower),
                        "upper_level": _json_number(upper),
                        "ratio": float(upper / lower),
                        "interpretation": "REVIEW_REQUIRED_NOT_AUTO_CORRECTED",
                    }
                )
    return flags


def _workbook_registry(raw_dir: Path, name: str) -> list[dict[str, Any]]:
    book = pd.ExcelFile(raw_dir / name, engine="xlrd")
    result: list[dict[str, Any]] = []
    for sheet in book.sheet_names:
        raw = pd.read_excel(raw_dir / name, sheet_name=sheet, header=None, engine="xlrd")
        result.append(
            {
                "sheet_name": sheet,
                "raw_shape": [int(raw.shape[0]), int(raw.shape[1])],
                "nonempty": bool(not raw.empty and raw.notna().any(axis=None)),
            }
        )
    return result


def build_audit(raw_dir: Path) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    hashes = verify_raw_inputs(raw_dir)
    data1 = read_data1(raw_dir)
    data2 = read_data2(raw_dir)
    datasets = {"Data1": data1, "Data2": data2}
    audit: dict[str, Any] = {
        "contract_version": "fresh-validation-data-audit/v1",
        "case_id": CASE_ID,
        "audit_scope": "SCHEMA_MISSING_DUPLICATE_RANGE_ONLY_NO_MODEL_RUN",
        "raw_immutable": True,
        "data_hashes": hashes,
        "workbooks": {
            name: _workbook_registry(raw_dir, f"{name}.xls") for name in ("Data1", "Data2")
        },
        "normalized_schema": [
            "dataset",
            "substance",
            "concentration",
            *FEATURES,
            "source_row_id",
        ],
        "datasets": {},
        "review_flags": [],
        "leakage_findings": [
            {
                "finding_id": "LEAK-GROUP-001",
                "risk": "replicates from one concentration level can leak across row-wise splits",
                "required_control": (
                    "all evaluation splits group by substance and concentration level"
                ),
                "status": "CONTROL_PREREGISTERED",
            }
        ],
        "limitations": [
            (
                "Attachment metadata do not describe camera, illumination, paper lot, "
                "or acquisition order."
            ),
            (
                "Concentration labels and color readings are observational; "
                "no causal interpretation is licensed."
            ),
            "No raw record is corrected or removed during preparation.",
        ],
        "model_run_count": 0,
    }
    for name, frame in datasets.items():
        exact_duplicates = _duplicate_registry(frame)
        audit["datasets"][name] = {
            "row_count": int(len(frame)),
            "substances": sorted(frame["substance"].unique().tolist()),
            "missing_counts": {
                column: int(frame[column].isna().sum())
                for column in ["substance", "concentration", *FEATURES]
            },
            "feature_ranges": {
                feature: {
                    "min": _json_number(frame[feature].min()),
                    "max": _json_number(frame[feature].max()),
                }
                for feature in FEATURES
            },
            "concentration_range": {
                "min": _json_number(frame["concentration"].min()),
                "max": _json_number(frame["concentration"].max()),
            },
            "replicate_registry": _replicate_registry(frame),
            "exact_duplicate_patterns": exact_duplicates,
            "exact_duplicate_row_count": int(
                sum(len(item["source_row_ids"]) for item in exact_duplicates)
            ),
        }
        singleton_levels = [
            {
                "dataset": name,
                "substance": substance,
                "concentration": _json_number(level),
                "replicate_count": int(count),
                "interpretation": "LIMITS_WITHIN_LEVEL_VARIANCE_ESTIMATION",
            }
            for substance, group in frame.groupby("substance", sort=False)
            for level, count in group.groupby("concentration").size().items()
            if int(count) == 1
        ]
        audit["review_flags"].extend(singleton_levels)
        audit["review_flags"].extend(_scale_gap_flags(frame))
    if audit["datasets"]["Data2"]["exact_duplicate_patterns"]:
        audit["review_flags"].append(
            {
                "dataset": "Data2",
                "finding": "EXACT_DUPLICATE_OBSERVATION",
                "interpretation": "PRESERVED_AND_GROUP_SAFE_SPLIT_REQUIRED",
            }
        )
    return audit, data1, data2


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", required=True, type=Path)
    parser.add_argument("--audit-output", type=Path)
    parser.add_argument("--normalized-dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    audit, data1, data2 = build_audit(args.raw_dir.resolve())
    if args.audit_output:
        _write_json(args.audit_output.resolve(), audit)
    if args.normalized_dir:
        normalized_dir = args.normalized_dir.resolve()
        normalized_dir.mkdir(parents=True, exist_ok=True)
        data1.to_csv(normalized_dir / "Data1.normalized.csv", index=False, encoding="utf-8")
        data2.to_csv(normalized_dir / "Data2.normalized.csv", index=False, encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
