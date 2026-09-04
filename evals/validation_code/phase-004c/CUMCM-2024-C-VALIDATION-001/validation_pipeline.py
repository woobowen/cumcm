#!/usr/bin/env python3
"""First-party, standard-library-only validation pipeline for the frozen case.

The runner invokes this file once for every frozen candidate and seed.  It reads
only registered case inputs, constructs four plans (Q1 waste, Q1 discount, Q2
independent uncertainty, Q3 correlated uncertainty), independently recomputes
feasibility, writes structurally preserved result workbooks, and emits the RC4
selected-output contract.  No result is embedded in this source file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import ZipFile

XML_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
XML_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"m": XML_MAIN, "r": XML_REL}
YEARS = tuple(range(2024, 2031))
MIN_AREA_MU = 0.3
MAX_PLOTS_PER_CROP_SEASON = 8
RISK_LAMBDA = 0.25
VALIDATION_SCENARIOS = 16
METRIC = "validation_total_risk_adjusted_profit_yuan"
CANDIDATES = {"BASELINE_RULE_ROTATION", "PRIMARY_RISK_GREEDY"}
REQUIREMENTS = (
    "REQ-2024C-Q1-WASTE",
    "REQ-2024C-Q1-DISCOUNT",
    "REQ-2024C-Q2-UNCERTAINTY",
    "REQ-2024C-Q3-DEPENDENCE",
    "REQ-2024C-CONSTRAINTS",
    "REQ-2024C-MANAGEMENT",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def column_index(reference: str) -> int:
    letters = "".join(character for character in reference if character.isalpha())
    value = 0
    for character in letters:
        value = value * 26 + ord(character.upper()) - ord("A") + 1
    return value


def column_name(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result


def xlsx_sheets(path: Path) -> list[tuple[str, str, list[dict[int, Any]]]]:
    """Read cell values without executing formulas or importing third-party code."""

    with ZipFile(path) as archive:
        try:
            shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = [
                "".join(node.text or "" for node in item.findall(".//m:t", NS))
                for item in shared_root.findall("m:si", NS)
            ]
        except KeyError:
            shared = []
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {item.attrib["Id"]: item.attrib["Target"] for item in relationships}
        result: list[tuple[str, str, list[dict[int, Any]]]] = []
        for sheet in workbook.findall("m:sheets/m:sheet", NS):
            target = targets[sheet.attrib[f"{{{XML_REL}}}id"]]
            member = target if target.startswith("xl/") else "xl/" + target.lstrip("/")
            root = ET.fromstring(archive.read(member))
            rows: list[dict[int, Any]] = []
            for row in root.findall("m:sheetData/m:row", NS):
                values: dict[int, Any] = {}
                for cell in row.findall("m:c", NS):
                    value_node = cell.find("m:v", NS)
                    cell_type = cell.attrib.get("t")
                    if cell_type == "s" and value_node is not None:
                        value: Any = shared[int(value_node.text or "0")]
                    elif cell_type == "inlineStr":
                        value = "".join(node.text or "" for node in cell.findall(".//m:t", NS))
                    elif value_node is not None:
                        value = value_node.text
                    else:
                        value = None
                    values[column_index(cell.attrib["r"])] = value
                rows.append(values)
            result.append((sheet.attrib["name"], member, rows))
        return result


def as_int(value: Any) -> int:
    return int(float(clean(value)))


def as_float(value: Any) -> float:
    return float(clean(value))


def price_midpoint(value: Any) -> float:
    parts = [float(part) for part in clean(value).split("-")]
    return sum(parts) / len(parts)


def load_case_data(case_root: Path) -> dict[str, Any]:
    attachment1 = xlsx_sheets(case_root / "raw/case_files/附件1.xlsx")
    attachment2 = xlsx_sheets(case_root / "raw/case_files/附件2.xlsx")

    plots: list[dict[str, Any]] = []
    for row in attachment1[0][2][1:]:
        if clean(row.get(1)):
            plots.append(
                {
                    "plot": clean(row.get(1)),
                    "land_type": clean(row.get(2)),
                    "area": as_float(row.get(3)),
                }
            )

    crops: dict[int, dict[str, str]] = {}
    for row in attachment1[1][2][1:]:
        if clean(row.get(1)).isdigit():
            crop_id = as_int(row.get(1))
            crops[crop_id] = {
                "name": clean(row.get(2)),
                "kind": clean(row.get(3)),
            }

    plantings_2023: list[dict[str, Any]] = []
    current_plot = ""
    for row in attachment2[0][2][1:]:
        if clean(row.get(1)):
            current_plot = clean(row.get(1))
        if current_plot and clean(row.get(2)).isdigit():
            plantings_2023.append(
                {
                    "plot": current_plot,
                    "crop_id": as_int(row.get(2)),
                    "area": as_float(row.get(5)),
                    "season": clean(row.get(6)),
                }
            )

    statistics_rows: dict[tuple[str, str, int], dict[str, float]] = {}
    for row in attachment2[1][2][1:]:
        if not clean(row.get(2)).isdigit():
            continue
        crop_id = as_int(row.get(2))
        land_type = clean(row.get(4))
        season = clean(row.get(5))
        statistics_rows[(land_type, season, crop_id)] = {
            "yield": as_float(row.get(6)),
            "cost": as_float(row.get(7)),
            "price": price_midpoint(row.get(8)),
        }

    plot_map = {item["plot"]: item for item in plots}
    crops_by_plot_season_2023: dict[tuple[str, str], set[int]] = defaultdict(set)
    legume_2023: dict[str, bool] = {item["plot"]: False for item in plots}
    base_demand = defaultdict(float)
    for record in plantings_2023:
        plot = plot_map[record["plot"]]
        crop_id = record["crop_id"]
        stat = get_stat(statistics_rows, plot["land_type"], record["season"], crop_id)
        base_demand[crop_id] += record["area"] * stat["yield"]
        crops_by_plot_season_2023[(record["plot"], record["season"])].add(crop_id)
        legume_2023[record["plot"]] |= "豆类" in crops[crop_id]["kind"]

    last_crops_2023: dict[str, set[int]] = {}
    for plot in plots:
        plot_id = plot["plot"]
        second = crops_by_plot_season_2023.get((plot_id, "第二季"), set())
        first = crops_by_plot_season_2023.get((plot_id, "第一季"), set())
        single = crops_by_plot_season_2023.get((plot_id, "单季"), set())
        last_crops_2023[plot_id] = set(second or first or single)

    prices_by_crop: dict[int, list[float]] = defaultdict(list)
    for (_, _, crop_id), record in statistics_rows.items():
        prices_by_crop[crop_id].append(record["price"])
    base_price = {crop_id: statistics.median(prices_by_crop[crop_id]) for crop_id in crops}

    return {
        "plots": plots,
        "plot_map": plot_map,
        "crops": crops,
        "plantings_2023": plantings_2023,
        "stats": statistics_rows,
        "base_demand": dict(base_demand),
        "last_crops_2023": last_crops_2023,
        "legume_2023": legume_2023,
        "base_price": base_price,
    }


def get_stat(
    statistics_rows: dict[tuple[str, str, int], dict[str, float]],
    land_type: str,
    season: str,
    crop_id: int,
) -> dict[str, float]:
    normalized_season = (
        "单季"
        if season == "第一季"
        and (land_type in {"平旱地", "梯田", "山坡地"} or (land_type == "水浇地" and crop_id == 16))
        else season
    )
    key = (land_type, normalized_season, crop_id)
    if key in statistics_rows:
        return statistics_rows[key]
    if land_type == "智慧大棚" and season == "第一季":
        return statistics_rows[("普通大棚", "第一季", crop_id)]
    raise KeyError(f"missing registered statistic: {land_type}/{season}/{crop_id}")


def allowed_options(land_type: str) -> list[tuple[int, ...]]:
    if land_type in {"平旱地", "梯田", "山坡地"}:
        return [(crop_id,) for crop_id in range(1, 16)]
    if land_type == "水浇地":
        return [(16,)] + [(first, second) for first in range(17, 35) for second in range(35, 38)]
    if land_type == "普通大棚":
        return [(first, second) for first in range(17, 35) for second in range(38, 42)]
    if land_type == "智慧大棚":
        return [
            (first, second)
            for first in range(17, 35)
            for second in range(17, 35)
            if first != second
        ]
    raise ValueError(f"unknown land type: {land_type}")


def season_label(land_type: str, option_length: int, slot: int) -> str:
    if land_type in {"平旱地", "梯田", "山坡地"} or option_length == 1:
        return "第一季"
    return "第一季" if slot == 0 else "第二季"


def is_legume(data: dict[str, Any], crop_id: int) -> bool:
    return "豆类" in data["crops"][crop_id]["kind"]


def clamp(low: float, high: float, value: float) -> float:
    return min(high, max(low, value))


def make_scenarios(data: dict[str, Any], seed: int, mode: str, count: int) -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []
    if mode == "stable":
        factors = {
            (year, crop_id): {"demand": 1.0, "yield": 1.0, "cost": 1.0, "price": 1.0}
            for year in YEARS
            for crop_id in data["crops"]
        }
        return [{"scenario_id": "STABLE", "factors": factors}]

    substitute_groups = (
        (6, 7, 8, 9),
        (17, 18, 19),
        (21, 22, 29),
        (23, 27, 28, 30),
        (35, 36, 37),
        (38, 39, 40, 41),
    )
    complement_pairs = ((1, 6), (2, 7), (17, 20), (21, 29), (35, 38))
    substitute_index = {
        crop_id: (group_index, member_index)
        for group_index, group in enumerate(substitute_groups)
        for member_index, crop_id in enumerate(group)
    }
    complement_index = {
        crop_id: pair_index for pair_index, pair in enumerate(complement_pairs) for crop_id in pair
    }
    for scenario_index in range(count):
        rng = random.Random(
            seed * 1009 + scenario_index * 9176 + (0 if mode == "independent" else 7919)
        )
        factors: dict[tuple[int, int], dict[str, float]] = {}
        wheat_corn_growth = {6: 1.0, 7: 1.0}
        for year in YEARS:
            common_market = rng.gauss(0.0, 1.0)
            common_climate = rng.gauss(0.0, 1.0)
            common_inflation = rng.gauss(0.0, 1.0)
            group_latent = [rng.gauss(0.0, 1.0) for _ in substitute_groups]
            pair_latent = [rng.gauss(0.0, 1.0) for _ in complement_pairs]
            for crop_id, crop in data["crops"].items():
                kind = crop["kind"]
                if crop_id in (6, 7):
                    if mode == "independent":
                        growth = rng.uniform(0.05, 0.10)
                    else:
                        growth = clamp(
                            0.05, 0.10, 0.075 + 0.012 * common_market + 0.008 * rng.gauss(0, 1)
                        )
                    wheat_corn_growth[crop_id] *= 1.0 + growth
                    demand_factor = wheat_corn_growth[crop_id]
                else:
                    if mode == "independent":
                        demand_change = rng.uniform(-0.05, 0.05)
                    else:
                        substitute = 0.0
                        if crop_id in substitute_index:
                            group_index, member_index = substitute_index[crop_id]
                            substitute = (1.0 if member_index % 2 == 0 else -1.0) * group_latent[
                                group_index
                            ]
                        complement = (
                            pair_latent[complement_index[crop_id]]
                            if crop_id in complement_index
                            else 0.0
                        )
                        demand_change = clamp(
                            -0.05,
                            0.05,
                            0.018 * common_market
                            + 0.020 * substitute
                            + 0.016 * complement
                            + 0.020 * rng.gauss(0, 1),
                        )
                    demand_factor = 1.0 + demand_change

                if mode == "independent":
                    yield_change = rng.uniform(-0.10, 0.10)
                    cost_noise = rng.uniform(-0.01, 0.01)
                else:
                    yield_change = clamp(
                        -0.10, 0.10, 0.055 * common_climate + 0.045 * rng.gauss(0, 1)
                    )
                    cost_noise = clamp(
                        -0.02, 0.02, 0.012 * common_inflation + 0.008 * rng.gauss(0, 1)
                    )
                cost_factor = (1.05 ** (year - 2023)) * (1.0 + cost_noise)
                if "粮食" in kind:
                    price_trend = 1.0
                elif "蔬菜" in kind:
                    price_trend = 1.05 ** (year - 2023)
                elif crop_id == 41:
                    price_trend = 0.95 ** (year - 2023)
                else:
                    decline = rng.uniform(0.01, 0.05)
                    price_trend = (1.0 - decline) ** (year - 2023)
                if mode == "correlated":
                    price_noise = clamp(
                        -0.035,
                        0.035,
                        0.018 * common_market + 0.012 * common_inflation + 0.010 * rng.gauss(0, 1),
                    )
                    price_factor = price_trend * (1.0 + price_noise)
                    relative_price = price_factor / price_trend - 1.0
                    demand_factor *= 1.0 - 0.15 * relative_price
                else:
                    price_factor = price_trend
                factors[(year, crop_id)] = {
                    "demand": demand_factor,
                    "yield": 1.0 + yield_change,
                    "cost": cost_factor,
                    "price": price_factor,
                }
        scenarios.append(
            {"scenario_id": f"{mode.upper()}-{scenario_index:02d}", "factors": factors}
        )
    return scenarios


def option_allocations(
    plot: dict[str, Any], year: int, option: tuple[int, ...]
) -> list[dict[str, Any]]:
    return [
        {
            "year": year,
            "plot": plot["plot"],
            "land_type": plot["land_type"],
            "season": season_label(plot["land_type"], len(option), slot),
            "crop_id": crop_id,
            "area_mu": plot["area"],
        }
        for slot, crop_id in enumerate(option)
    ]


def revenue(quantity: float, demand: float, price: float, surplus_discount: float) -> float:
    normal = min(quantity, demand)
    surplus = max(0.0, quantity - demand)
    return normal * price + surplus * price * surplus_discount


def incremental_profit(
    data: dict[str, Any],
    plot: dict[str, Any],
    year: int,
    option: tuple[int, ...],
    scenarios: list[dict[str, Any]],
    production: list[dict[tuple[int, int], float]],
    surplus_discount: float,
) -> list[float]:
    deltas: list[float] = []
    allocations = option_allocations(plot, year, option)
    for scenario_index, scenario in enumerate(scenarios):
        temporary = dict(production[scenario_index])
        delta = 0.0
        for allocation in allocations:
            crop_id = allocation["crop_id"]
            key = (year, crop_id)
            stat = get_stat(data["stats"], plot["land_type"], allocation["season"], crop_id)
            factors = scenario["factors"][key]
            added = allocation["area_mu"] * stat["yield"] * factors["yield"]
            previous = temporary.get(key, 0.0)
            demand = data["base_demand"][crop_id] * factors["demand"]
            price = data["base_price"][crop_id] * factors["price"]
            delta += revenue(previous + added, demand, price, surplus_discount)
            delta -= revenue(previous, demand, price, surplus_discount)
            delta -= allocation["area_mu"] * stat["cost"] * factors["cost"]
            temporary[key] = previous + added
        deltas.append(delta)
    return deltas


def risk_score(values: list[float], risk_lambda: float) -> float:
    mean = statistics.fmean(values)
    downside = math.sqrt(statistics.fmean([max(0.0, mean - value) ** 2 for value in values]))
    return mean - risk_lambda * downside


def build_plan(
    data: dict[str, Any],
    candidate_id: str,
    scenarios: list[dict[str, Any]],
    surplus_discount: float,
    risk_lambda: float,
) -> list[dict[str, Any]]:
    production: list[dict[tuple[int, int], float]] = [defaultdict(float) for _ in scenarios]
    last_crops = {plot_id: set(crop_ids) for plot_id, crop_ids in data["last_crops_2023"].items()}
    last_legume_year = {
        plot["plot"]: (2023 if data["legume_2023"][plot["plot"]] else 2022)
        for plot in data["plots"]
    }
    schedule: list[dict[str, Any]] = []
    dispersion: Counter[tuple[int, str, int]] = Counter()
    for year in YEARS:
        ordered_plots = list(data["plots"])
        if candidate_id == "PRIMARY_RISK_GREEDY":
            ordered_plots.sort(key=lambda item: (-item["area"], item["plot"]))
            shift = year % len(ordered_plots)
            ordered_plots = ordered_plots[shift:] + ordered_plots[:shift]
        for plot_index, plot in enumerate(ordered_plots):
            due_legume = year - last_legume_year[plot["plot"]] >= 3
            feasible: list[tuple[int, ...]] = []
            for option in allowed_options(plot["land_type"]):
                if option[0] in last_crops[plot["plot"]]:
                    continue
                if len(option) == 2 and option[0] == option[1]:
                    continue
                if due_legume and not any(is_legume(data, crop_id) for crop_id in option):
                    continue
                counts_valid = True
                for slot, crop_id in enumerate(option):
                    season = season_label(plot["land_type"], len(option), slot)
                    if dispersion[(year, season, crop_id)] >= MAX_PLOTS_PER_CROP_SEASON:
                        counts_valid = False
                        break
                if counts_valid:
                    feasible.append(option)
            if not feasible:
                raise RuntimeError(f"no feasible frozen option for {plot['plot']} in {year}")

            if candidate_id == "BASELINE_RULE_ROTATION":
                feasible.sort()
                chosen = feasible[(plot_index + year - YEARS[0]) % len(feasible)]
            else:
                scored: list[tuple[float, tuple[int, ...]]] = []
                for option in feasible:
                    deltas = incremental_profit(
                        data,
                        plot,
                        year,
                        option,
                        scenarios,
                        production,
                        surplus_discount,
                    )
                    scored.append((risk_score(deltas, risk_lambda), option))
                best_score = max(value for value, _ in scored)
                chosen = min(option for value, option in scored if value == best_score)

            allocations = option_allocations(plot, year, chosen)
            for allocation in allocations:
                crop_id = allocation["crop_id"]
                allocation["crop_name"] = data["crops"][crop_id]["name"]
                schedule.append(allocation)
                dispersion[(year, allocation["season"], crop_id)] += 1
            for scenario_index, scenario in enumerate(scenarios):
                for allocation in allocations:
                    crop_id = allocation["crop_id"]
                    stat = get_stat(data["stats"], plot["land_type"], allocation["season"], crop_id)
                    production[scenario_index][(year, crop_id)] += (
                        allocation["area_mu"]
                        * stat["yield"]
                        * scenario["factors"][(year, crop_id)]["yield"]
                    )
            last_crops[plot["plot"]] = {chosen[-1]}
            if any(is_legume(data, crop_id) for crop_id in chosen):
                last_legume_year[plot["plot"]] = year
    return sorted(
        schedule, key=lambda item: (item["year"], item["plot"], item["season"], item["crop_id"])
    )


def evaluate_schedule(
    data: dict[str, Any],
    schedule: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
    surplus_discount: float,
) -> dict[str, Any]:
    scenario_profits: list[float] = []
    for scenario in scenarios:
        production = defaultdict(float)
        cost_total = 0.0
        for allocation in schedule:
            year = allocation["year"]
            crop_id = allocation["crop_id"]
            key = (year, crop_id)
            stat = get_stat(data["stats"], allocation["land_type"], allocation["season"], crop_id)
            factors = scenario["factors"][key]
            production[key] += allocation["area_mu"] * stat["yield"] * factors["yield"]
            cost_total += allocation["area_mu"] * stat["cost"] * factors["cost"]
        revenue_total = 0.0
        for (year, crop_id), quantity in production.items():
            factors = scenario["factors"][(year, crop_id)]
            demand = data["base_demand"][crop_id] * factors["demand"]
            price = data["base_price"][crop_id] * factors["price"]
            revenue_total += revenue(quantity, demand, price, surplus_discount)
        scenario_profits.append(revenue_total - cost_total)
    ordered = sorted(scenario_profits)
    mean = statistics.fmean(scenario_profits)
    downside = math.sqrt(
        statistics.fmean([max(0.0, mean - value) ** 2 for value in scenario_profits])
    )
    return {
        "scenario_count": len(scenario_profits),
        "mean_profit_yuan": round(mean, 6),
        "minimum_profit_yuan": round(min(scenario_profits), 6),
        "maximum_profit_yuan": round(max(scenario_profits), 6),
        "p10_profit_yuan": round(ordered[max(0, math.ceil(0.10 * len(ordered)) - 1)], 6),
        "downside_semideviation_yuan": round(downside, 6),
        "risk_adjusted_profit_yuan": round(mean - RISK_LAMBDA * downside, 6),
    }


def compatibility_valid(land_type: str, season: str, crop_id: int) -> bool:
    if land_type in {"平旱地", "梯田", "山坡地"}:
        return season == "第一季" and 1 <= crop_id <= 15
    if land_type == "水浇地":
        return (season == "第一季" and (crop_id == 16 or 17 <= crop_id <= 34)) or (
            season == "第二季" and 35 <= crop_id <= 37
        )
    if land_type == "普通大棚":
        return (season == "第一季" and 17 <= crop_id <= 34) or (
            season == "第二季" and 38 <= crop_id <= 41
        )
    if land_type == "智慧大棚":
        return season in {"第一季", "第二季"} and 17 <= crop_id <= 34
    return False


def recompute_feasibility(data: dict[str, Any], schedule: list[dict[str, Any]]) -> dict[str, Any]:
    violations: list[str] = []
    plot_map = data["plot_map"]
    allocation_map: dict[tuple[int, str, str], list[dict[str, Any]]] = defaultdict(list)
    dispersion: Counter[tuple[int, str, int]] = Counter()
    for allocation in schedule:
        year = allocation.get("year")
        plot_id = allocation.get("plot")
        season = allocation.get("season")
        crop_id = allocation.get("crop_id")
        area = allocation.get("area_mu")
        if year not in YEARS or plot_id not in plot_map or season not in {"第一季", "第二季"}:
            violations.append("ALLOCATION_IDENTITY_INVALID")
            continue
        if not isinstance(crop_id, int) or crop_id not in data["crops"]:
            violations.append(f"CROP_INVALID:{plot_id}:{year}:{season}")
            continue
        if (
            not isinstance(area, (int, float))
            or isinstance(area, bool)
            or not math.isfinite(area)
            or area < 0
        ):
            violations.append(f"AREA_NONFINITE_OR_NEGATIVE:{plot_id}:{year}:{season}")
            continue
        if area + 1e-9 < MIN_AREA_MU:
            violations.append(f"MINIMUM_AREA:{plot_id}:{year}:{season}")
        if not compatibility_valid(plot_map[plot_id]["land_type"], season, crop_id):
            violations.append(f"COMPATIBILITY:{plot_id}:{year}:{season}:{crop_id}")
        allocation_map[(year, plot_id, season)].append(allocation)
        dispersion[(year, season, crop_id)] += 1

    for year in YEARS:
        for plot in data["plots"]:
            first = allocation_map[(year, plot["plot"], "第一季")]
            second = allocation_map[(year, plot["plot"], "第二季")]
            first_area = sum(item["area_mu"] for item in first)
            second_area = sum(item["area_mu"] for item in second)
            if len(first) != 1 or abs(first_area - plot["area"]) > 1e-8:
                violations.append(f"FIRST_SEASON_CAPACITY:{plot['plot']}:{year}")
            if plot["land_type"] in {"平旱地", "梯田", "山坡地"}:
                if second:
                    violations.append(f"OPEN_LAND_SECOND_SEASON:{plot['plot']}:{year}")
            elif plot["land_type"] == "水浇地":
                rice_mode = len(first) == 1 and first[0]["crop_id"] == 16
                if rice_mode and second:
                    violations.append(f"RICE_WITH_SECOND_SEASON:{plot['plot']}:{year}")
                if not rice_mode and (len(second) != 1 or abs(second_area - plot["area"]) > 1e-8):
                    violations.append(f"IRRIGATED_SECOND_CAPACITY:{plot['plot']}:{year}")
            elif len(second) != 1 or abs(second_area - plot["area"]) > 1e-8:
                violations.append(f"GREENHOUSE_SECOND_CAPACITY:{plot['plot']}:{year}")

    for (year, season, crop_id), count in dispersion.items():
        if count > MAX_PLOTS_PER_CROP_SEASON:
            violations.append(f"DISPERSION:{year}:{season}:{crop_id}:{count}")

    by_plot_year_season: dict[tuple[str, int, str], set[int]] = defaultdict(set)
    for record in data["plantings_2023"]:
        season = "第一季" if record["season"] == "单季" else record["season"]
        by_plot_year_season[(record["plot"], 2023, season)].add(record["crop_id"])
    for allocation in schedule:
        by_plot_year_season[(allocation["plot"], allocation["year"], allocation["season"])].add(
            allocation["crop_id"]
        )
    for plot in data["plots"]:
        chronological: list[tuple[int, str, set[int]]] = []
        for year in range(2023, 2031):
            for season in ("第一季", "第二季"):
                crop_ids = by_plot_year_season[(plot["plot"], year, season)]
                if crop_ids:
                    chronological.append((year, season, crop_ids))
        for left, right in zip(chronological, chronological[1:], strict=False):
            repeated = left[2] & right[2]
            if repeated:
                violations.append(
                    f"CONSECUTIVE_CROP:{plot['plot']}:{left[0]}-{left[1]}:{right[0]}-{right[1]}:{min(repeated)}"
                )
        for start in range(2023, 2029):
            crops = [
                crop_id
                for year in range(start, start + 3)
                for season in ("第一季", "第二季")
                for crop_id in by_plot_year_season[(plot["plot"], year, season)]
            ]
            if not any(is_legume(data, crop_id) for crop_id in crops):
                violations.append(f"LEGUME_WINDOW:{plot['plot']}:{start}-{start + 2}")

    unique_violations = sorted(set(violations))
    return {
        "feasible": not unique_violations,
        "violation_count": len(unique_violations),
        "violations": unique_violations,
        "checks": {
            "allocation_nonnegativity": "RECOMPUTED",
            "land_type_and_season_compatibility": "RECOMPUTED",
            "plot_season_capacity": "RECOMPUTED",
            "no_consecutive_same_crop": "RECOMPUTED_WITH_2023_HISTORY",
            "rolling_three_year_legume_coverage": "RECOMPUTED_2023_TO_2030",
            "minimum_area_mu": MIN_AREA_MU,
            "maximum_plots_per_crop_season": MAX_PLOTS_PER_CROP_SEASON,
            "template_years": list(YEARS),
        },
    }


def workbook_structure(path: Path) -> dict[str, Any]:
    with ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {item.attrib["Id"]: item.attrib["Target"] for item in relationships}
        sheets = []
        for sheet in workbook.findall("m:sheets/m:sheet", NS):
            target = targets[sheet.attrib[f"{{{XML_REL}}}id"]]
            member = target if target.startswith("xl/") else "xl/" + target.lstrip("/")
            root = ET.fromstring(archive.read(member))
            dimension = root.find("m:dimension", NS)
            merges = sorted(
                item.attrib["ref"] for item in root.findall("m:mergeCells/m:mergeCell", NS)
            )
            sheets.append(
                {
                    "name": sheet.attrib["name"],
                    "member": member,
                    "dimension": dimension.attrib.get("ref") if dimension is not None else "",
                    "merges": merges,
                }
            )
        return {"members": sorted(archive.namelist()), "sheets": sheets}


def write_result_workbook(
    template: Path,
    target: Path,
    schedule: list[dict[str, Any]],
    data: dict[str, Any],
) -> dict[str, Any]:
    plot_order = [item["plot"] for item in data["plots"]]
    second_order = [
        item["plot"]
        for item in data["plots"]
        if item["land_type"] in {"水浇地", "普通大棚", "智慧大棚"}
    ]
    values: dict[tuple[int, str], float] = {}
    for allocation in schedule:
        if allocation["season"] == "第一季":
            row = 2 + plot_order.index(allocation["plot"])
        else:
            row = 56 + second_order.index(allocation["plot"])
        cell = f"{column_name(allocation['crop_id'] + 2)}{row}"
        values[(allocation["year"], cell)] = allocation["area_mu"]

    structure_before = workbook_structure(template)
    with ZipFile(template) as source, ZipFile(target, "w") as destination:
        workbook = ET.fromstring(source.read("xl/workbook.xml"))
        relationships = ET.fromstring(source.read("xl/_rels/workbook.xml.rels"))
        targets = {item.attrib["Id"]: item.attrib["Target"] for item in relationships}
        sheet_members = {}
        for sheet in workbook.findall("m:sheets/m:sheet", NS):
            member = targets[sheet.attrib[f"{{{XML_REL}}}id"]]
            member = member if member.startswith("xl/") else "xl/" + member.lstrip("/")
            sheet_members[member] = int(sheet.attrib["name"])
        for info in source.infolist():
            payload = source.read(info.filename)
            if info.filename in sheet_members:
                year = sheet_members[info.filename]
                text = payload.decode("utf-8")
                replaced: set[str] = set()

                def populate(
                    match: re.Match[str],
                    current_year: int = year,
                    replaced_cells: set[str] = replaced,
                ) -> str:
                    column = column_index(match.group(1))
                    row = int(match.group(2))
                    if not (3 <= column <= 43 and 2 <= row <= 83):
                        return match.group(0)
                    cell = f"{match.group(1)}{row}"
                    value = values.get((current_year, cell), 0.0)
                    formatted = format(float(value), ".12g")
                    replaced_cells.add(cell)
                    return f'<c r="{cell}"{match.group(3)}><v>{formatted}</v></c>'

                text = re.sub(r'<c r="([A-Z]+)([0-9]+)"([^>]*)/>', populate, text)
                if len(replaced) != 82 * 41:
                    raise RuntimeError(
                        f"template target cell set incomplete: {year}/{len(replaced)}"
                    )
                payload = text.encode("utf-8")
            destination.writestr(info, payload)
    structure_after = workbook_structure(target)
    if structure_after != structure_before:
        raise RuntimeError("output template structure changed")
    return {
        "path": str(target),
        "sha256": sha256_file(target),
        "structure_preserved": True,
        "sheet_names": [str(year) for year in YEARS],
    }


def claim_registry(output_relative: str) -> dict[str, Any]:
    texts = {
        "REQ-2024C-Q1-WASTE": (
            "Q1 waste plan is feasible and its objective is recomputed from registered inputs."
        ),
        "REQ-2024C-Q1-DISCOUNT": (
            "Q1 half-price-surplus plan is feasible and its objective is recomputed "
            "from registered inputs."
        ),
        "REQ-2024C-Q2-UNCERTAINTY": (
            "Q2 plan is feasible under the registered independent uncertainty design "
            "with quantitative risk metrics."
        ),
        "REQ-2024C-Q3-DEPENDENCE": (
            "Q3 plan uses registered substitute, complement, and economic dependence "
            "assumptions and is quantitatively compared with Q2."
        ),
        "REQ-2024C-CONSTRAINTS": (
            "All land, season, capacity, rotation, legume, nonnegativity, and year "
            "constraints are independently recomputed."
        ),
        "REQ-2024C-MANAGEMENT": (
            "The registered minimum-area and dispersion constraints are enforced and "
            "independently recomputed."
        ),
    }
    return {
        requirement_id: {
            "claim_id": "CLAIM-" + requirement_id.removeprefix("REQ-"),
            "claim_text": texts[requirement_id],
            "evidence_artifact_ids": [output_relative],
        }
        for requirement_id in REQUIREMENTS
    }


def scenario_assumptions() -> dict[str, Any]:
    return {
        "q2": {
            "wheat_corn_annual_demand_growth": [0.05, 0.10],
            "other_crop_demand_change": [-0.05, 0.05],
            "yield_change": [-0.10, 0.10],
            "annual_cost_growth": 0.05,
            "vegetable_annual_price_growth": 0.05,
            "fungus_annual_price_decline": [0.01, 0.05],
            "morel_annual_price_decline": 0.05,
            "surplus_treatment": "CONSERVATIVE_WASTE",
        },
        "q3": {
            "substitute_groups": [
                [6, 7, 8, 9],
                [17, 18, 19],
                [21, 22, 29],
                [23, 27, 28, 30],
                [35, 36, 37],
                [38, 39, 40, 41],
            ],
            "complement_pairs": [[1, 6], [2, 7], [17, 20], [21, 29], [35, 38]],
            "demand_price_elasticity": -0.15,
            "shared_market_cost_price_factor": True,
            "shared_climate_yield_factor": True,
            "status": "REGISTERED_SIMULATION_ASSUMPTIONS_NOT_OBSERVED_CAUSAL_FACTS",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-root", required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.candidate_id not in CANDIDATES:
        raise ValueError("candidate is not in frozen registry")
    case_root = Path(args.case_root).resolve()
    output_path = (case_root / args.output).resolve()
    output_relative = str(output_path.relative_to(case_root))
    data = load_case_data(case_root)

    stable = make_scenarios(data, args.seed, "stable", 1)
    independent = make_scenarios(data, args.seed, "independent", VALIDATION_SCENARIOS)
    correlated = make_scenarios(data, args.seed, "correlated", VALIDATION_SCENARIOS)
    plan_q1_waste = build_plan(data, args.candidate_id, stable, 0.0, 0.0)
    plan_q1_discount = build_plan(data, args.candidate_id, stable, 0.5, 0.0)
    plan_q2 = build_plan(data, args.candidate_id, independent, 0.0, RISK_LAMBDA)
    plan_q3 = build_plan(data, args.candidate_id, correlated, 0.0, RISK_LAMBDA)

    plans = {
        "q1_waste": plan_q1_waste,
        "q1_discount": plan_q1_discount,
        "q2_uncertainty": plan_q2,
        "q3_dependence": plan_q3,
    }
    feasibility = {name: recompute_feasibility(data, plan) for name, plan in plans.items()}
    if not all(record["feasible"] for record in feasibility.values()):
        raise RuntimeError("independent feasibility recomputation rejected a generated plan")

    evaluations = {
        "q1_waste": evaluate_schedule(data, plan_q1_waste, stable, 0.0),
        "q1_discount": evaluate_schedule(data, plan_q1_discount, stable, 0.5),
        "q2_uncertainty": evaluate_schedule(data, plan_q2, independent, 0.0),
        "q3_dependence": evaluate_schedule(data, plan_q3, correlated, 0.0),
        "q2_plan_under_q3_dependence": evaluate_schedule(data, plan_q2, correlated, 0.0),
    }
    q3_delta = (
        evaluations["q3_dependence"]["risk_adjusted_profit_yuan"]
        - evaluations["q2_plan_under_q3_dependence"]["risk_adjusted_profit_yuan"]
    )

    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    template_artifacts = {
        "result1_1": write_result_workbook(
            case_root / "raw/case_files/附件3/result1_1.xlsx",
            output_dir / "result1_1.xlsx",
            plan_q1_waste,
            data,
        ),
        "result1_2": write_result_workbook(
            case_root / "raw/case_files/附件3/result1_2.xlsx",
            output_dir / "result1_2.xlsx",
            plan_q1_discount,
            data,
        ),
        "result2": write_result_workbook(
            case_root / "raw/case_files/附件3/result2.xlsx",
            output_dir / "result2.xlsx",
            plan_q2,
            data,
        ),
    }
    for artifact in template_artifacts.values():
        artifact["path"] = str(Path(artifact["path"]).resolve().relative_to(case_root))

    validation_metric = round(
        evaluations["q1_waste"]["mean_profit_yuan"]
        + evaluations["q1_discount"]["mean_profit_yuan"]
        + evaluations["q2_uncertainty"]["risk_adjusted_profit_yuan"]
        + evaluations["q3_dependence"]["risk_adjusted_profit_yuan"],
        6,
    )
    stress_low_demand = make_scenarios(data, args.seed + 700001, "independent", 8)
    stress_correlated = make_scenarios(data, args.seed + 700003, "correlated", 8)
    stress_q2 = evaluate_schedule(data, plan_q2, stress_low_demand, 0.0)
    stress_q3 = evaluate_schedule(data, plan_q3, stress_correlated, 0.0)
    stress_total_independent = round(
        evaluations["q1_waste"]["mean_profit_yuan"]
        + evaluations["q1_discount"]["mean_profit_yuan"]
        + stress_q2["risk_adjusted_profit_yuan"]
        + evaluations["q3_dependence"]["risk_adjusted_profit_yuan"],
        6,
    )
    stress_total_correlated = round(
        evaluations["q1_waste"]["mean_profit_yuan"]
        + evaluations["q1_discount"]["mean_profit_yuan"]
        + evaluations["q2_uncertainty"]["risk_adjusted_profit_yuan"]
        + stress_q3["risk_adjusted_profit_yuan"],
        6,
    )
    q2_under_q3_total = round(
        evaluations["q1_waste"]["mean_profit_yuan"]
        + evaluations["q1_discount"]["mean_profit_yuan"]
        + evaluations["q2_uncertainty"]["risk_adjusted_profit_yuan"]
        + evaluations["q2_plan_under_q3_dependence"]["risk_adjusted_profit_yuan"],
        6,
    )

    output = {
        "candidate_id": args.candidate_id,
        "status": "SUCCESS",
        "validation_metrics": {METRIC: validation_metric},
        "final_metrics": {
            METRIC: validation_metric,
            "q1_waste_profit_yuan": evaluations["q1_waste"]["mean_profit_yuan"],
            "q1_discount_profit_yuan": evaluations["q1_discount"]["mean_profit_yuan"],
            "q2_risk_adjusted_profit_yuan": evaluations["q2_uncertainty"][
                "risk_adjusted_profit_yuan"
            ],
            "q3_risk_adjusted_profit_yuan": evaluations["q3_dependence"][
                "risk_adjusted_profit_yuan"
            ],
            "q3_minus_q2_plan_under_dependence_yuan": round(q3_delta, 6),
        },
        "claim_scope": (
            "Feasible 2024-2030 whole-plot planting strategies under registered input "
            "interpretations and simulation assumptions; no causal claim or "
            "out-of-sample guarantee."
        ),
        "requirement_claims": claim_registry(output_relative),
        "figure_ready_data": [
            {
                "figure_id": "FIG-PROFIT-COMPARISON",
                "x": ["Q1_WASTE", "Q1_DISCOUNT", "Q2", "Q3", "Q2_UNDER_Q3"],
                "y_yuan": [
                    evaluations["q1_waste"]["mean_profit_yuan"],
                    evaluations["q1_discount"]["mean_profit_yuan"],
                    evaluations["q2_uncertainty"]["risk_adjusted_profit_yuan"],
                    evaluations["q3_dependence"]["risk_adjusted_profit_yuan"],
                    evaluations["q2_plan_under_q3_dependence"]["risk_adjusted_profit_yuan"],
                ],
            },
            {
                "figure_id": "FIG-RISK-RANGES",
                "series": {
                    name: {
                        "minimum": record["minimum_profit_yuan"],
                        "mean": record["mean_profit_yuan"],
                        "maximum": record["maximum_profit_yuan"],
                    }
                    for name, record in evaluations.items()
                },
            },
        ],
        "uncertainty": {
            "validation_scenarios_per_stochastic_question": VALIDATION_SCENARIOS,
            "random_seed": args.seed,
            "risk_lambda": RISK_LAMBDA,
            "scenario_assumptions": scenario_assumptions(),
            "quantitative_results": evaluations,
        },
        "limitations": [
            (
                "Correlation and substitute/complement parameters are registered "
                "simulation assumptions rather than estimates from a multiyear panel."
            ),
            (
                "Whole-plot allocation is a conservative management discretization "
                "and can exclude profitable split-plot solutions."
            ),
            (
                "Price intervals are represented by their midpoints before registered "
                "uncertainty factors are applied."
            ),
            (
                "The heuristic primary is deterministic and feasible but does not "
                "claim a global mixed-integer optimum."
            ),
        ],
        "robustness_evidence": {
            "metric": METRIC,
            "metric_direction": "MAX",
            "perturbations": [
                {
                    "perturbation_id": "PERTURB-INDEPENDENT-ALT-SEED",
                    "metric": METRIC,
                    "result": stress_total_independent,
                    "evidence": "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS",
                },
                {
                    "perturbation_id": "PERTURB-CORRELATED-ALT-SEED",
                    "metric": METRIC,
                    "result": stress_total_correlated,
                    "evidence": "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS",
                },
                {
                    "perturbation_id": "PERTURB-Q2-PLAN-EVALUATED-UNDER-Q3",
                    "metric": METRIC,
                    "result": q2_under_q3_total,
                    "evidence": "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS",
                },
            ],
            "failure_cases": [
                (
                    "Joint adverse demand, yield, cost, and price realizations can "
                    "materially reduce profit even when agronomic feasibility is preserved."
                ),
                (
                    "The registered dispersion cap or whole-plot rule can prevent "
                    "allocation to the unconstrained highest-margin crop."
                ),
            ],
        },
        "model": {
            "algorithm": args.candidate_id,
            "baseline": args.candidate_id == "BASELINE_RULE_ROTATION",
            "objective": METRIC,
            "risk_lambda": RISK_LAMBDA,
            "global_optimality_claimed": False,
        },
        "plans": plans,
        "evaluations": evaluations,
        "independent_feasibility": feasibility,
        "template_artifacts": template_artifacts,
        "q3_comparison": {
            "metric": "risk_adjusted_profit_yuan",
            "q3_strategy": evaluations["q3_dependence"]["risk_adjusted_profit_yuan"],
            "q2_strategy_under_q3_scenarios": evaluations["q2_plan_under_q3_dependence"][
                "risk_adjusted_profit_yuan"
            ],
            "difference_yuan": round(q3_delta, 6),
        },
        "input_interpretations": {
            "expected_sales_volume": "2023 planted area multiplied by matching registered yield",
            "price_interval": (
                "arithmetic midpoint followed by crop-level median across registered "
                "land-season records"
            ),
            "single_crop_per_plot_season": True,
            "minimum_area_mu": MIN_AREA_MU,
            "maximum_plots_per_crop_season": MAX_PLOTS_PER_CROP_SEASON,
        },
    }
    write_json(output_path, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
