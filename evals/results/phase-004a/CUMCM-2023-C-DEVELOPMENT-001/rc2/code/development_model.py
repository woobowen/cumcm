#!/usr/bin/env python3
"""Case-owned Development regression model; not part of the reusable Skill."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

BASELINE = "PIPELINE-SEASONAL-BASELINE"
HIERARCHICAL = "PIPELINE-HIERARCHICAL-STOCHASTIC"
ROBUST = "PIPELINE-NONPARAMETRIC-ROBUST"
CANDIDATES = {BASELINE, HIERARCHICAL, ROBUST}


def safe_float(value: float) -> float:
    number = float(value)
    if not np.isfinite(number):
        raise ValueError("required numeric result is non-finite")
    return round(number, 8)


def safe_optional_float(value: float) -> float | None:
    number = float(value)
    return round(number, 8) if np.isfinite(number) else None


def load_metadata(root: Path) -> dict:
    path = root / "state/variant_metadata.json"
    if not path.is_file():
        return {
            "variant_id": "DEVELOPMENT_REGRESSION",
            "quantity_column": "销量(千克)",
            "quantity_scale_to_kg": 1.0,
            "date_shift_days": 0,
            "loss_source_available": True,
        }
    value = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "variant_id",
        "quantity_column",
        "quantity_scale_to_kg",
        "date_shift_days",
        "loss_source_available",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("variant metadata invalid")
    return value


def load_inputs(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    data_root = root / "raw/case_files"
    metadata = load_metadata(root)
    master = pd.read_excel(data_root / "附件1.xlsx")
    sales = pd.read_excel(data_root / "附件2.xlsx")
    costs = pd.read_excel(data_root / "附件3.xlsx")
    loss_path = data_root / "附件4.xlsx"
    if metadata["loss_source_available"] and loss_path.is_file():
        loss = pd.read_excel(loss_path, sheet_name="Sheet1")
    else:
        loss = master[["单品编码", "单品名称"]].copy()
        loss["损耗率(%)"] = np.nan
    quantity_column = metadata["quantity_column"]
    if not isinstance(quantity_column, str) or quantity_column not in sales:
        raise ValueError("quantity column invalid")
    quantity_scale = float(metadata["quantity_scale_to_kg"])
    if not np.isfinite(quantity_scale) or quantity_scale <= 0:
        raise ValueError("quantity scale invalid")
    sales["销量(千克)"] = pd.to_numeric(sales[quantity_column], errors="coerce") * quantity_scale
    sales["销售日期"] = pd.to_datetime(sales["销售日期"], errors="coerce")
    costs["日期"] = pd.to_datetime(costs["日期"], errors="coerce")
    sales = sales.merge(master, on="单品编码", how="left", validate="many_to_one")
    sales = sales.merge(
        costs,
        left_on=["销售日期", "单品编码"],
        right_on=["日期", "单品编码"],
        how="left",
        validate="many_to_one",
    )
    sales = sales.merge(
        loss[["单品编码", "损耗率(%)"]], on="单品编码", how="left", validate="many_to_one"
    )
    positive = sales[(sales["销售类型"] == "销售") & (sales["销量(千克)"] > 0)].copy()
    return master, positive, costs, loss, metadata


def daily_category(sales: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        sales.groupby(["销售日期", "分类名称"], as_index=False)
        .agg(
            quantity=("销量(千克)", "sum"),
            revenue=("销售单价(元/千克)", lambda x: 0.0),
        )
        .drop(columns="revenue")
    )
    revenue = (
        sales.assign(_revenue=sales["销量(千克)"] * sales["销售单价(元/千克)"])
        .groupby(["销售日期", "分类名称"], as_index=False)["_revenue"]
        .sum()
    )
    grouped = grouped.merge(revenue, on=["销售日期", "分类名称"], validate="one_to_one")
    grouped["weighted_price"] = grouped["_revenue"] / grouped["quantity"]
    grouped["dow"] = grouped["销售日期"].dt.dayofweek
    grouped["ordinal"] = (grouped["销售日期"] - grouped["销售日期"].min()).dt.days
    return grouped


def design_matrix(frame: pd.DataFrame) -> np.ndarray:
    day = frame["ordinal"].to_numpy(dtype=float)
    dow = frame["dow"].to_numpy(dtype=int)
    columns = [np.ones(len(frame)), day / max(1.0, float(day.max(initial=1.0)))]
    columns.extend((dow == index).astype(float) for index in range(1, 7))
    columns.extend(
        [
            np.sin(2 * np.pi * day / 365.25),
            np.cos(2 * np.pi * day / 365.25),
        ]
    )
    return np.column_stack(columns)


def prediction_table(train: pd.DataFrame, target: pd.DataFrame, candidate: str) -> pd.DataFrame:
    records: list[pd.DataFrame] = []
    global_mean = float(train["quantity"].mean())
    for category, target_group in target.groupby("分类名称", sort=True):
        source = train[train["分类名称"] == category].copy()
        target_group = target_group.copy()
        if source.empty:
            target_group["prediction"] = global_mean
        elif candidate == BASELINE:
            by_dow = source.groupby("dow")["quantity"].mean()
            target_group["prediction"] = (
                target_group["dow"].map(by_dow).fillna(source["quantity"].mean())
            )
        elif candidate == ROBUST:
            cutoff = source["销售日期"].max() - pd.Timedelta(days=84)
            recent = source[source["销售日期"] >= cutoff]
            by_dow = recent.groupby("dow")["quantity"].median()
            target_group["prediction"] = (
                target_group["dow"].map(by_dow).fillna(recent["quantity"].median())
            )
        else:
            x_train = design_matrix(source)
            coefficients = np.linalg.lstsq(x_train, source["quantity"].to_numpy(), rcond=None)[0]
            target_group["prediction"] = design_matrix(target_group) @ coefficients
            category_mean = float(source["quantity"].mean())
            target_group["prediction"] = 0.85 * target_group["prediction"] + 0.15 * category_mean
        target_group["prediction"] = target_group["prediction"].clip(lower=0.0)
        records.append(target_group)
    return pd.concat(records, ignore_index=True)


def wape(actual: pd.Series, predicted: pd.Series) -> float:
    denominator = float(actual.abs().sum())
    return float((actual - predicted).abs().sum() / denominator) if denominator else 0.0


def validation_score(
    daily: pd.DataFrame,
    candidate: str,
    *,
    training_window_days: int | None = None,
    validation_quantity_scale: float = 1.0,
    validation_tail_days_removed: int = 0,
) -> tuple[float, float]:
    validation_start = daily["销售日期"].max() - pd.Timedelta(days=180)
    validation_end = daily["销售日期"].max() - pd.Timedelta(days=31)
    train = daily[daily["销售日期"] < validation_start]
    validation = daily[
        (daily["销售日期"] >= validation_start) & (daily["销售日期"] <= validation_end)
    ].copy()
    if training_window_days is not None:
        train = train[
            train["销售日期"] >= validation_start - pd.Timedelta(days=training_window_days)
        ]
    if validation_tail_days_removed:
        validation = validation[
            validation["销售日期"]
            <= validation["销售日期"].max() - pd.Timedelta(days=validation_tail_days_removed)
        ]
    validation["quantity"] = validation["quantity"] * validation_quantity_scale
    baseline_predictions = prediction_table(train, validation, BASELINE)
    candidate_predictions = prediction_table(train, validation, candidate)
    baseline_wape = wape(baseline_predictions["quantity"], baseline_predictions["prediction"])
    candidate_wape = wape(candidate_predictions["quantity"], candidate_predictions["prediction"])
    normalized = candidate_wape / baseline_wape if baseline_wape else 1.0
    return safe_float(normalized), safe_float(candidate_wape)


def future_frame(daily: pd.DataFrame) -> pd.DataFrame:
    categories = sorted(daily["分类名称"].dropna().unique())
    dates = pd.date_range(daily["销售日期"].max() + pd.Timedelta(days=1), periods=7)
    frame = pd.MultiIndex.from_product(
        [dates, categories], names=["销售日期", "分类名称"]
    ).to_frame(index=False)
    frame["dow"] = frame["销售日期"].dt.dayofweek
    frame["ordinal"] = (frame["销售日期"] - daily["销售日期"].min()).dt.days
    return frame


def category_plan(sales: pd.DataFrame, daily: pd.DataFrame, candidate: str) -> list[dict]:
    predicted = prediction_table(daily, future_frame(daily), candidate)
    recent_cutoff = sales["销售日期"].max() - pd.Timedelta(days=90)
    recent = sales[sales["销售日期"] >= recent_cutoff].copy()
    recent["markup"] = (recent["销售单价(元/千克)"] - recent["批发价格(元/千克)"]) / recent[
        "批发价格(元/千克)"
    ].replace(0, np.nan)
    parameters = recent.groupby("分类名称").agg(
        wholesale_cost=("批发价格(元/千克)", "median"),
        markup=("markup", "median"),
        loss_rate=("损耗率(%)", "median"),
    )
    records: list[dict] = []
    for row in predicted.itertuples(index=False):
        values = parameters.loc[row.分类名称]
        observed_cost = float(values.wholesale_cost)
        cost = max(0.01, observed_cost if np.isfinite(observed_cost) else 1.0)
        markup = float(np.clip(values.markup if np.isfinite(values.markup) else 0.25, 0.05, 1.5))
        loss_rate = float(values.loss_rate) / 100 if np.isfinite(values.loss_rate) else 0.10
        demand = max(0.0, float(row.prediction))
        replenishment = demand / max(0.5, 1.0 - loss_rate)
        price = cost * (1.0 + markup)
        records.append(
            {
                "date": row.销售日期.strftime("%Y-%m-%d"),
                "category": str(row.分类名称),
                "forecast_sales_kg": safe_float(demand),
                "replenishment_kg": safe_float(replenishment),
                "price_yuan_per_kg": safe_float(price),
                "wholesale_cost_yuan_per_kg": safe_float(cost),
                "loss_rate": safe_float(loss_rate),
                "expected_profit_proxy_yuan": safe_float(demand * price - replenishment * cost),
            }
        )
    return records


def item_plan(sales: pd.DataFrame) -> list[dict]:
    final_date = sales["销售日期"].max()
    recent = sales[sales["销售日期"] >= final_date - pd.Timedelta(days=6)].copy()
    recent["markup"] = (recent["销售单价(元/千克)"] - recent["批发价格(元/千克)"]) / recent[
        "批发价格(元/千克)"
    ].replace(0, np.nan)
    summary = recent.groupby(["单品编码", "单品名称", "分类名称"], as_index=False).agg(
        demand_kg=("销量(千克)", lambda values: values.sum() / 7.0),
        wholesale_cost=("批发价格(元/千克)", "median"),
        markup=("markup", "median"),
        loss_rate_percent=("损耗率(%)", "median"),
    )
    fallback_cost = float(recent["批发价格(元/千克)"].median())
    summary["wholesale_cost"] = summary["wholesale_cost"].fillna(
        fallback_cost if np.isfinite(fallback_cost) else 1.0
    )
    summary["markup"] = summary["markup"].clip(lower=0.05, upper=1.5).fillna(0.25)
    summary["loss_rate_percent"] = summary["loss_rate_percent"].fillna(10.0)
    summary["score"] = summary["demand_kg"] * summary["wholesale_cost"] * summary["markup"]
    selected_indices: list[int] = []
    for _, group in summary.groupby("分类名称", sort=True):
        selected_indices.append(int(group.sort_values("score", ascending=False).index[0]))
    for index in summary.sort_values("score", ascending=False).index:
        if int(index) not in selected_indices:
            selected_indices.append(int(index))
        if len(selected_indices) == 27:
            break
    selected = summary.loc[selected_indices].sort_values(
        ["分类名称", "score"], ascending=[True, False]
    )
    records: list[dict] = []
    for row in selected.itertuples(index=False):
        loss_rate = float(row.loss_rate_percent) / 100
        quantity = max(2.5, float(row.demand_kg) / max(0.5, 1.0 - loss_rate))
        price = float(row.wholesale_cost) * (1.0 + float(row.markup))
        records.append(
            {
                "item_code": str(row.单品编码),
                "item_name": str(row.单品名称),
                "category": str(row.分类名称),
                "replenishment_kg": safe_float(quantity),
                "price_yuan_per_kg": safe_float(price),
                "loss_rate": safe_float(loss_rate),
            }
        )
    return records


def descriptive_results(sales: pd.DataFrame, daily: pd.DataFrame) -> dict:
    category = daily.groupby("分类名称")["quantity"].describe(percentiles=[0.25, 0.5, 0.75, 0.95])
    item = (
        sales.groupby(["单品编码", "单品名称"])["销量(千克)"]
        .sum()
        .describe(percentiles=[0.25, 0.5, 0.75, 0.95])
    )
    pivot = daily.pivot(index="销售日期", columns="分类名称", values="quantity")
    correlations = pivot.corr(method="spearman", min_periods=30)
    price_demand: list[dict] = []
    for category_name, frame in daily.groupby("分类名称", sort=True):
        price_demand.append(
            {
                "category": str(category_name),
                "spearman_price_quantity": safe_optional_float(
                    frame[["weighted_price", "quantity"]].corr(method="spearman").iloc[0, 1]
                ),
                "n_days": int(len(frame)),
                "interpretation": "association_not_causation",
            }
        )
    return {
        "category_daily_distribution": {
            str(category_name): {key: safe_float(value) for key, value in row.items()}
            for category_name, row in category.to_dict(orient="index").items()
        },
        "item_total_distribution": {
            str(key): safe_float(value) for key, value in item.to_dict().items()
        },
        "category_spearman_correlations": {
            str(left): {str(right): safe_float(value) for right, value in row.items()}
            for left, row in correlations.to_dict(orient="index").items()
        },
        "price_demand_associations": price_demand,
    }


def requirement_claims(output_relative: str) -> dict:
    descriptions = {
        "REQ-1A": (
            "Empirical category/day and item-total distributions were computed from bound "
            "positive sales."
        ),
        "REQ-1B": "Category rank correlations were computed with pairwise observed-day support.",
        "REQ-2A": "Category price-demand associations are reported as non-causal diagnostics.",
        "REQ-2B": (
            "A seven-day category replenishment and pricing plan was generated with loss "
            "adjustment."
        ),
        "REQ-3": (
            "A feasible 27-item plan was generated with category coverage and 2.5 kg minimum "
            "display."
        ),
        "REQ-4": (
            "Additional stockout, inventory, weather, promotion, and shelf-capacity data are "
            "prioritized."
        ),
    }
    return {
        requirement_id: {
            "claim_id": f"CLAIM-RC2-{index}",
            "claim_text": description,
            "evidence_artifact_ids": [output_relative],
        }
        for index, (requirement_id, description) in enumerate(descriptions.items(), start=1)
    }


def run(case_root: Path, candidate: str, seed: int, output: Path) -> None:
    if candidate not in CANDIDATES:
        raise ValueError("candidate not preregistered")
    np.random.seed(seed)
    master, sales, costs, loss, metadata = load_inputs(case_root)
    daily = daily_category(sales)
    normalized_loss, raw_wape = validation_score(daily, candidate)
    shorter_window_loss, _ = validation_score(daily, candidate, training_window_days=730)
    demand_shift_loss, _ = validation_score(daily, candidate, validation_quantity_scale=1.05)
    truncated_validation_loss, _ = validation_score(
        daily, candidate, validation_tail_days_removed=14
    )
    category_decisions = category_plan(sales, daily, candidate)
    item_decisions = item_plan(sales)
    expected_profit = sum(row["expected_profit_proxy_yuan"] for row in category_decisions)
    data_quality = {
        "master_rows": int(len(master)),
        "positive_sales_rows": int(len(sales)),
        "wholesale_rows": int(len(costs)),
        "loss_rows": int(len(loss)),
        "unmatched_category_rows": int(sales["分类名称"].isna().sum()),
        "missing_wholesale_rows": int(sales["批发价格(元/千克)"].isna().sum()),
        "missing_loss_rows": int(sales["损耗率(%)"].isna().sum()),
        "quantity_scale_to_kg": safe_float(metadata["quantity_scale_to_kg"]),
        "date_shift_days": int(metadata["date_shift_days"]),
        "loss_source_available": bool(metadata["loss_source_available"]),
    }
    output_relative = output.as_posix()
    claims = requirement_claims(output_relative)
    primary_scope = claims["REQ-1A"]["claim_text"]
    value = {
        "status": "SUCCESS",
        "candidate_id": candidate,
        "seed": seed,
        "variant_id": metadata["variant_id"],
        "validation_metrics": {
            "baseline_normalized_decision_loss": normalized_loss,
            "validation_wape": raw_wape,
        },
        "final_metrics": {
            "validation_wape": raw_wape,
            "forecast_total_kg": safe_float(
                sum(row["forecast_sales_kg"] for row in category_decisions)
            ),
            "expected_profit_proxy_yuan": safe_float(expected_profit),
            "selected_item_count": len(item_decisions),
        },
        "claim_scope": primary_scope,
        "requirement_claims": claims,
        "robustness_evidence": {
            "metric": "baseline_normalized_decision_loss",
            "metric_direction": "MIN",
            "perturbations": [
                {
                    "perturbation_id": "RECENT_WINDOW_SHORTER",
                    "metric": "baseline_normalized_decision_loss",
                    "result": shorter_window_loss,
                    "evidence": "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS",
                },
                {
                    "perturbation_id": "VALIDATION_DEMAND_SCALE_UP",
                    "metric": "baseline_normalized_decision_loss",
                    "result": demand_shift_loss,
                    "evidence": "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS",
                },
                {
                    "perturbation_id": "VALIDATION_TAIL_REMOVED",
                    "metric": "baseline_normalized_decision_loss",
                    "result": truncated_validation_loss,
                    "evidence": "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS",
                },
            ],
            "failure_cases": [
                "No stockout indicator; observed sales can understate latent demand.",
                "Price-demand association is endogenous and is not a causal elasticity estimate.",
                "Profit is a planning proxy without shelf-capacity or inventory carryover data.",
            ],
        },
        "data_quality": data_quality,
        "descriptive_results": descriptive_results(sales, daily),
        "category_plan": category_decisions,
        "item_plan": item_decisions,
        "additional_data_priorities": [
            "hourly inventory and stockout flags",
            "promotion exposure and display position",
            "weather and local event covariates",
            "supplier availability and order lead time",
            "shelf capacity and disposal quantity",
        ],
        "figure_ready_data": [
            {
                "figure_id": "SEVEN_DAY_CATEGORY_FORECAST",
                "series": [
                    {
                        "date": row["date"],
                        "category": row["category"],
                        "forecast_sales_kg": row["forecast_sales_kg"],
                        "replenishment_kg": row["replenishment_kg"],
                    }
                    for row in category_decisions
                ],
            }
        ],
        "uncertainty": {
            "scope": "time-ordered validation and three deterministic perturbations",
            "quantified": True,
            "missing_loss_rows": data_quality["missing_loss_rows"],
            "future_outcomes_available": False,
        },
        "limitations": [
            "Development regression after reference unlock; not blind, Validation, or Held-out.",
            "Single historical problem cannot establish generalization.",
            "The item assortment is a feasible heuristic, not a global optimality certificate.",
            "Future realized outcomes are unavailable, so plans are not ex-post profit claims.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.case_root, args.candidate_id, args.seed, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
