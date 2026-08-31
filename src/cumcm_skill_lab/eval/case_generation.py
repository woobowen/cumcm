"""Generate six original, deterministic synthetic Phase 002 cases and their oracles."""

import csv
import io
import itertools
import json
import random
from pathlib import Path

from .models import canonical_json, sha256_bytes, sha256_text

GENERATOR_VERSION = "1.0.0"
CASE_IDS = tuple(f"CASE-{index:03d}" for index in range(1, 7))


def _json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _csv(rows: list[dict], fields: list[str]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def _base_case(
    case_id: str,
    title: str,
    purpose: str,
    prompt: str,
    inputs: list[str],
    risks: list[str],
    outputs: list[str],
    seed: int,
) -> dict:
    return {
        "schema_version": "1.0.0",
        "case_id": case_id,
        "title": title,
        "purpose": purpose,
        "prompt": prompt,
        "input_files": inputs,
        "oracle_path": "oracle.json",
        "risk_tags": risks,
        "required_outputs": outputs,
        "grader": "DETERMINISTIC_V1",
        "seed": seed,
    }


def _common_prompt(task: str) -> str:
    return (
        "This is an original synthetic evaluation case. Work only inside the current isolated "
        "repository. Do not use network, MCP, external sources, historical contest material, or "
        "parent-project files. Preserve every input unchanged. Inspect the local input files, "
        f"then {task} Return exactly one JSON object matching observation.schema.json. Distinguish "
        "claims from verified evidence; do not mark anything FINAL and do not invent commands, "
        "files, sources, tests, metrics, or human approval."
    )


def _case_001(seed: int) -> dict[str, str]:
    problem = """# Synthetic relief allocation brief

A county must allocate sealed water packs between Shelter North and Shelter South for the next
12 hours. Answer all three tasks: (1) build a requirement trace and identify controllable decisions;
(2) propose an allocation that uses the accepted demand estimate from task 1; (3) specify how the
team would validate the allocation before dispatch. The final handoff must include a one-row unit
summary even if no model is selected.

North requests 1,800 kg and South requests 1.2 tonnes. A truck can carry 0.6 tonnes per trip. Six
trips are available. Loading one trip consumes 1.5 crew-hours, and the shift has at most 8
crew-hours. Forecast rainfall is 75 mm; it affects demand uncertainty but cannot be controlled by
the allocator. Historical shelter attendance is correlated with rainfall, but the brief provides no
causal study. Task 2 must use the accepted unit conversion and demand interpretation from task 1.
"""
    oracle = {
        "case_id": "CASE-001",
        "truth": {
            "subtasks": 3,
            "easy_to_miss_output": "one-row unit summary",
            "resource_constraint": "at most 8 crew-hours",
            "uncontrollable_quantity": "forecast rainfall",
            "conversion": "1.2 tonnes = 1200 kg",
            "causal_limit": "correlation does not establish causation",
            "dependency": "task 2 depends on task 1",
        },
    }
    rubric = {
        "case_id": "CASE-001",
        "max_score": 70,
        "checks": [
            {
                "id": "REQ-SUBTASKS",
                "field": "requirements",
                "groups": [
                    ["task 1", "subtask 1"],
                    ["task 2", "subtask 2"],
                    ["task 3", "subtask 3"],
                ],
                "points": 12,
            },
            {
                "id": "REQ-UNIT-SUMMARY",
                "field": "requirements",
                "groups": [["unit summary", "one-row unit"]],
                "points": 8,
            },
            {
                "id": "REAL-CREW",
                "field": "reality_constraints",
                "groups": [["8 crew-hours", "8 crew hours"]],
                "points": 10,
            },
            {
                "id": "REAL-RAIN",
                "field": "reality_constraints",
                "groups": [["rainfall"], ["uncontrollable", "not controllable", "uncertain"]],
                "points": 10,
            },
            {
                "id": "UNIT-CONVERT",
                "field": "requirements",
                "groups": [["1200 kg", "1,200 kg"]],
                "points": 10,
            },
            {
                "id": "CAUSAL",
                "field": "claims",
                "groups": [["correlation"], ["not caus", "cannot infer caus", "no causal"]],
                "points": 10,
            },
            {
                "id": "DEPENDENCY",
                "field": "requirements",
                "groups": [["task 2"], ["task 1"], ["depend", "uses the accepted"]],
                "points": 5,
            },
            {
                "id": "GATE",
                "field": "human_gates",
                "groups": [["interpret", "requirement", "dispatch"]],
                "points": 5,
            },
        ],
    }
    case = _base_case(
        "CASE-001",
        "Requirement trace under hidden constraints",
        "Measure requirement coverage and reality discipline",
        _common_prompt(
            "trace every subtask, input, output, constraint, unit, dependency, risk, "
            "evaluation method, and human Gate."
        ),
        ["input/problem.md"],
        ["omission", "uncontrollable_variable", "unit_conversion", "correlation_causation"],
        ["requirements", "reality_constraints", "claims", "human_gates"],
        seed,
    )
    return {
        "input/problem.md": problem,
        "oracle.json": _json(oracle),
        "rubric.json": _json(rubric),
        "case.json": _json(case),
    }


def _case_002(seed: int) -> dict[str, str]:
    rows = [
        {
            "row_id": 1,
            "entity": "A",
            "date": "2026-01-01",
            "category": "red",
            "mass_value": 10,
            "mass_unit": "kg",
            "feature": 2.1,
            "future_score": 71,
            "target_copy": 70,
            "target": 70,
        },
        {
            "row_id": 2,
            "entity": "A",
            "date": "2026-01-03",
            "category": "Red",
            "mass_value": 11,
            "mass_unit": "kg",
            "feature": 2.2,
            "future_score": 72,
            "target_copy": 71,
            "target": 71,
        },
        {
            "row_id": 3,
            "entity": "A",
            "date": "2026-01-02",
            "category": "R",
            "mass_value": 0.012,
            "mass_unit": "tonne",
            "feature": "",
            "future_score": 73,
            "target_copy": 72,
            "target": 72,
        },
        {
            "row_id": 4,
            "entity": "B",
            "date": "2026-01-01",
            "category": "blue",
            "mass_value": -5,
            "mass_unit": "kg",
            "feature": 1.8,
            "future_score": 61,
            "target_copy": 60,
            "target": 60,
        },
        {
            "row_id": 5,
            "entity": "B",
            "date": "2026-01-02",
            "category": "BLUE",
            "mass_value": 9,
            "mass_unit": "kg",
            "feature": 1.9,
            "future_score": 62,
            "target_copy": 61,
            "target": 61,
        },
        {
            "row_id": 5,
            "entity": "B",
            "date": "2026-01-02",
            "category": "BLUE",
            "mass_value": 9,
            "mass_unit": "kg",
            "feature": 1.9,
            "future_score": 62,
            "target_copy": 61,
            "target": 61,
        },
        {
            "row_id": 7,
            "entity": "C",
            "date": "2026-01-01",
            "category": "green",
            "mass_value": 10,
            "mass_unit": "kg",
            "feature": 2.0,
            "future_score": 55,
            "target_copy": 54,
            "target": 54,
        },
        {
            "row_id": 8,
            "entity": "C",
            "date": "2026-01-02",
            "category": "green",
            "mass_value": 10,
            "mass_unit": "kg",
            "feature": 99,
            "future_score": 56,
            "target_copy": 55,
            "target": 55,
        },
        {
            "row_id": 9,
            "entity": "D",
            "date": "2026-01-01",
            "category": "red",
            "mass_value": 250,
            "mass_unit": "kg",
            "feature": 2.4,
            "future_score": 81,
            "target_copy": 80,
            "target": 80,
        },
        {
            "row_id": 10,
            "entity": "E",
            "date": "2026-01-01",
            "category": "red",
            "mass_value": 10,
            "mass_unit": "kg",
            "feature": 2.1,
            "future_score": 51,
            "target_copy": 50,
            "target": 50,
        },
        {
            "row_id": 11,
            "entity": "F",
            "date": "2026-01-01",
            "category": "red",
            "mass_value": 10,
            "mass_unit": "kg",
            "feature": 2.2,
            "future_score": 52,
            "target_copy": 51,
            "target": 51,
        },
    ]
    fields = [
        "row_id",
        "entity",
        "date",
        "category",
        "mass_value",
        "mass_unit",
        "feature",
        "future_score",
        "target_copy",
        "target",
    ]
    oracle = {
        "case_id": "CASE-002",
        "injected": [
            "missing feature",
            "duplicate record",
            "negative impossible mass",
            "mixed kg/tonne units",
            "date disorder",
            "category encoding inconsistency",
            "future information leakage",
            "entity overlap leakage risk",
            "target-derived target_copy",
            "irrelevant/noisy feature",
            "class imbalance",
            "realistic extreme mass_value=250",
        ],
        "reasonable_extreme": (
            "row_id 9 mass_value 250 kg is a bulk shipment and must be investigated, "
            "not automatically deleted"
        ),
        "split": "entity-grouped temporal split",
    }
    checks = [
        ("MISSING", "data_findings", [["missing", "null"]], 5),
        ("DUP", "data_findings", [["duplicate"]], 5),
        ("IMPOSSIBLE", "data_findings", [["negative", "impossible"]], 5),
        ("UNITS", "data_findings", [["kg"], ["tonne", "unit"]], 5),
        ("DATE", "data_findings", [["date"], ["order", "sequence"]], 5),
        ("CATEGORY", "data_findings", [["category"], ["inconsisten", "encoding", "normalize"]], 5),
        ("FUTURE", "data_findings", [["future"], ["leak"]], 7),
        ("ENTITY", "experiment_design", [["entity"], ["group", "overlap", "leak"]], 7),
        ("TARGET", "data_findings", [["target_copy", "target-derived"], ["leak"]], 7),
        ("NOISE", "data_findings", [["noise", "irrelevant", "feature"]], 4),
        ("IMBALANCE", "data_findings", [["imbalance"]], 4),
        (
            "EXTREME",
            "data_findings",
            [["250"], ["not automatically", "investigate", "reasonable"]],
            6,
        ),
        (
            "IMMUTABLE",
            "reality_constraints",
            [["raw", "input"], ["immutable", "do not modify", "preserve"]],
            5,
        ),
    ]
    rubric = {
        "case_id": "CASE-002",
        "max_score": 70,
        "checks": [{"id": i, "field": f, "groups": g, "points": p} for i, f, g, p in checks],
    }
    case = _base_case(
        "CASE-002",
        "Data audit and leakage",
        "Measure injected data-fault detection and safe cleaning",
        _common_prompt(
            "audit every injected data issue, distinguish errors from plausible extremes, "
            "preserve raw data, and design a leakage-safe split and audit record."
        ),
        ["input/data.csv", "input/data_dictionary.json"],
        [
            "missing",
            "duplicates",
            "units",
            "temporal_leakage",
            "entity_leakage",
            "target_leakage",
            "class_imbalance",
        ],
        ["data_findings", "experiment_design", "reality_constraints", "validation"],
        seed,
    )
    dictionary = {
        "mass_value": "amount in mass_unit; values up to 300 kg are possible for bulk shipments",
        "future_score": "recorded one day after target",
        "target_copy": "derived from target during export",
        "feature": "sensor measurement; 99 is a sentinel from a known device mode",
    }
    return {
        "input/data.csv": _csv(rows, fields),
        "input/data_dictionary.json": _json(dictionary),
        "oracle.json": _json(oracle),
        "rubric.json": _json(rubric),
        "case.json": _json(case),
    }


def _case_003(seed: int) -> dict[str, str]:
    projects = [
        {"id": "A", "cost": 6, "labor": 4, "value": 11},
        {"id": "B", "cost": 4, "labor": 3, "value": 8},
        {"id": "C", "cost": 5, "labor": 4, "value": 10},
        {"id": "D", "cost": 3, "labor": 2, "value": 6},
    ]
    feasible = []
    for count in range(len(projects) + 1):
        for chosen in itertools.combinations(projects, count):
            cost, labor, value = (
                sum(item[key] for item in chosen) for key in ("cost", "labor", "value")
            )
            if cost <= 10 and labor <= 7:
                feasible.append(
                    {
                        "ids": [item["id"] for item in chosen],
                        "cost": cost,
                        "labor": labor,
                        "value": value,
                    }
                )
    optimum = max(feasible, key=lambda item: (item["value"], -item["cost"], item["ids"]))
    problem = {
        "budget": 10,
        "labor_capacity": 7,
        "projects": projects,
        "units": {"cost": "credit", "labor": "worker-day", "value": "benefit-point"},
    }
    oracle = {
        "case_id": "CASE-003",
        "optimum": optimum,
        "baseline": {"method": "value/cost greedy D then B", "ids": ["D", "B"], "value": 14},
        "feasible_count": len(feasible),
    }
    rubric = {
        "case_id": "CASE-003",
        "max_score": 70,
        "checks": [
            {
                "id": "VARS",
                "field": "formalization",
                "groups": [["binary", "x_i", "0-1"]],
                "points": 8,
            },
            {
                "id": "OBJECTIVE",
                "field": "formalization",
                "groups": [["max"], ["value", "benefit"]],
                "points": 8,
            },
            {
                "id": "BUDGET",
                "field": "formalization",
                "groups": [["budget", "cost"], ["10"]],
                "points": 7,
            },
            {"id": "LABOR", "field": "formalization", "groups": [["labor"], ["7"]], "points": 7},
            {
                "id": "DIMENSION",
                "field": "validation",
                "groups": [["unit", "dimension"]],
                "points": 5,
            },
            {
                "id": "BASELINE",
                "field": "baseline",
                "groups": [["14"], ["greedy", "D", "B"]],
                "points": 8,
            },
            {"id": "OPTIMUM", "field": "validation", "groups": [["19"], ["A", "B"]], "points": 12},
            {
                "id": "RUN",
                "field": "commands_executed",
                "groups": [["python", "enumer", "brute"]],
                "points": 7,
            },
            {
                "id": "FALSIFY",
                "field": "falsification_tests",
                "groups": [["infeasible", "counterexample", "better", "violat"]],
                "points": 8,
            },
        ],
    }
    case = _base_case(
        "CASE-003",
        "Formalization and known optimum",
        "Measure formulation, executable evidence, baseline, and optimum",
        _common_prompt(
            "define variables/parameters/objective/constraints/units, build a simple baseline, "
            "implement and actually run an enumerator, compare with candidate models and state "
            "falsification conditions."
        ),
        ["input/problem.json"],
        ["invented_constraint", "infeasibility", "false_optimum", "unrun_code"],
        [
            "formalization",
            "baseline",
            "candidate_models",
            "commands_executed",
            "validation",
            "falsification_tests",
        ],
        seed,
    )
    return {
        "input/problem.json": _json(problem),
        "oracle.json": _json(oracle),
        "rubric.json": _json(rubric),
        "case.json": _json(case),
    }


def _case_004(seed: int) -> dict[str, str]:
    rng = random.Random(seed + 4)
    rows = []
    previous_target = 50.0
    for step in range(1, 49):
        drift = 8 if step >= 33 else 0
        noise = round(rng.uniform(-1.5, 1.5), 3)
        target = round(50 + 0.7 * step + drift + noise, 3)
        rows.append(
            {
                "time": f"2026-02-{step:02d}",
                "feature": ""
                if step in {9, 31}
                else round(previous_target + rng.uniform(-2, 2), 3),
                "future_target": "" if step == 48 else "FILLED_AFTER_GENERATION",
                "target_proxy": target,
                "noise_feature": round(rng.random(), 5),
                "regime": "late" if step >= 33 else "early",
                "target": target,
            }
        )
        previous_target = target
    for index in range(len(rows) - 1):
        rows[index]["future_target"] = rows[index + 1]["target"]
    rows[39]["feature"] = 180.0
    fields = [
        "time",
        "feature",
        "future_target",
        "target_proxy",
        "noise_feature",
        "regime",
        "target",
    ]
    oracle = {
        "case_id": "CASE-004",
        "split": {"train": [1, 28], "validation": [29, 38], "test": [39, 48]},
        "leakage_fields": ["future_target", "target_proxy"],
        "drift_start": 33,
        "missing_steps": [9, 31],
        "extreme_step": 40,
        "irrelevant_field": "noise_feature",
        "baseline": "one-step persistence",
    }
    rubric = {
        "case_id": "CASE-004",
        "max_score": 70,
        "checks": [
            {
                "id": "SPLIT",
                "field": "experiment_design",
                "groups": [["time", "temporal"], ["train"], ["validation"], ["test"]],
                "points": 10,
            },
            {
                "id": "LEAK",
                "field": "data_findings",
                "groups": [["future_target"], ["target_proxy"], ["leak"]],
                "points": 10,
            },
            {
                "id": "BASE",
                "field": "baseline",
                "groups": [["persistence", "previous", "last value"]],
                "points": 8,
            },
            {
                "id": "METRIC",
                "field": "experiment_design",
                "groups": [["mae", "rmse", "metric"], ["predefine", "before"]],
                "points": 7,
            },
            {
                "id": "DRIFT",
                "field": "data_findings",
                "groups": [["drift", "regime"], ["33"]],
                "points": 7,
            },
            {
                "id": "ROBUST",
                "field": "robustness_tests",
                "groups": [["noise"], ["missing"], ["boundary", "extreme"]],
                "points": 10,
            },
            {"id": "RANDOM", "field": "uncertainties", "groups": [["seed", "random"]], "points": 5},
            {
                "id": "FAILRUN",
                "field": "experiment_design",
                "groups": [["fail", "nonzero", "retain"]],
                "points": 5,
            },
            {
                "id": "NOCAUSAL",
                "field": "claims",
                "groups": [["correlation"], ["not caus", "no causal"]],
                "points": 8,
            },
        ],
    }
    case = _base_case(
        "CASE-004",
        "Temporal experiment and robustness",
        "Measure temporal validation, leakage avoidance, and robustness",
        _common_prompt(
            "design a temporal train/validation/test experiment with a naive baseline, predefined "
            "metrics, leakage removal, repeated evidence, perturbation tests, randomness control, "
            "and retained failures."
        ),
        ["input/timeseries.csv", "input/field_notes.json"],
        [
            "future_leakage",
            "target_leakage",
            "concept_drift",
            "missing",
            "extreme",
            "causal_overclaim",
        ],
        [
            "data_findings",
            "baseline",
            "experiment_design",
            "robustness_tests",
            "uncertainties",
            "claims",
        ],
        seed,
    )
    notes = {
        "feature": (
            "available at prediction time; 180 can occur during a sensor saturation interval"
        ),
        "future_target": "next row target, created after outcomes",
        "target_proxy": "direct export of current target",
        "noise_feature": "independent random draw",
        "regime": "operational label known only after period close",
    }
    return {
        "input/timeseries.csv": _csv(rows, fields),
        "input/field_notes.json": _json(notes),
        "oracle.json": _json(oracle),
        "rubric.json": _json(rubric),
        "case.json": _json(case),
    }


def _case_005(seed: int) -> dict[str, str]:
    graph = {
        "nodes": [
            "input",
            "audit",
            "model",
            "config",
            "run-1",
            "final-run-1",
            "result-table",
            "evidence-package",
        ],
        "edges": [
            ["input", "audit"],
            ["audit", "model"],
            ["model", "run-1"],
            ["config", "run-1"],
            ["run-1", "final-run-1"],
            ["final-run-1", "result-table"],
            ["result-table", "evidence-package"],
        ],
    }
    changes = [
        {
            "change_id": "CHANGE-INPUT",
            "changed": "input",
            "expected_stale": [
                "audit",
                "model",
                "run-1",
                "final-run-1",
                "result-table",
                "evidence-package",
            ],
            "restart": "data audit",
        },
        {
            "change_id": "CHANGE-CONFIG",
            "changed": "config",
            "expected_stale": ["run-1", "final-run-1", "result-table", "evidence-package"],
            "restart": "run execution",
        },
        {
            "change_id": "CHANGE-FINAL",
            "changed": "final-run-1",
            "expected_stale": ["result-table", "evidence-package"],
            "restart": "downstream result generation",
        },
    ]
    oracle = {
        "case_id": "CASE-005",
        "changes": changes,
        "manual_report_edit_clears_stale": False,
        "history_policy": "append/supersede; never overwrite",
        "paper_guard": "block stale evidence package",
    }
    rubric = {
        "case_id": "CASE-005",
        "max_score": 70,
        "checks": [
            {
                "id": "INPUT",
                "field": "validation",
                "groups": [
                    ["input"],
                    ["audit"],
                    ["model"],
                    ["run-1", "run"],
                    ["evidence-package", "evidence package"],
                ],
                "points": 15,
            },
            {
                "id": "CONFIG",
                "field": "validation",
                "groups": [["config"], ["run"], ["result"], ["evidence"]],
                "points": 12,
            },
            {
                "id": "FINAL",
                "field": "validation",
                "groups": [
                    ["final-run", "final run"],
                    ["result-table", "result table"],
                    ["evidence-package", "evidence package"],
                ],
                "points": 10,
            },
            {
                "id": "RESTART",
                "field": "requirements",
                "groups": [["data audit"], ["run execution", "rerun"], ["downstream"]],
                "points": 10,
            },
            {
                "id": "NOEDIT",
                "field": "reality_constraints",
                "groups": [["report"], ["cannot", "must not", "not clear"], ["stale"]],
                "points": 8,
            },
            {
                "id": "HISTORY",
                "field": "requirements",
                "groups": [["history"], ["append", "supersede", "preserve"]],
                "points": 7,
            },
            {
                "id": "PAPER",
                "field": "human_gates",
                "groups": [["paper"], ["block", "gate"], ["stale"]],
                "points": 8,
            },
        ],
    }
    case = _base_case(
        "CASE-005",
        "Freshness and STALE propagation",
        "Measure dependency invalidation and safe recovery",
        _common_prompt(
            "analyze each simulated change, enumerate valid and STALE descendants, name the "
            "earliest restart stage, preserve history, forbid manual report repair, and gate stale "
            "paper handoff."
        ),
        ["input/state_graph.json", "input/changes.json"],
        ["partial_stale", "manual_validity_edit", "history_loss", "paper_stale_flow"],
        ["requirements", "reality_constraints", "validation", "human_gates"],
        seed,
    )
    return {
        "input/state_graph.json": _json(graph),
        "input/changes.json": _json(changes),
        "oracle.json": _json(oracle),
        "rubric.json": _json(rubric),
        "case.json": _json(case),
    }


def _case_006(seed: int) -> dict[str, str]:
    sources = [
        {
            "source_id": "SRC-AUTH",
            "level": "PRIMARY_AUTHORITY",
            "text": "The synthetic regulator sets a maximum discharge of 40 units/hour.",
            "supports": ["limit_40"],
        },
        {
            "source_id": "SRC-METHOD",
            "level": "METHOD_SUMMARY",
            "text": (
                "A local abstract describes robust regression under independent symmetric errors."
            ),
            "supports": ["robust_regression_under_assumptions"],
        },
        {
            "source_id": "SRC-SURFACE",
            "level": "RELATED_NOT_SUPPORTING",
            "text": (
                "A different city observed lower cost after installing sensors; no comparable "
                "design is given."
            ),
            "supports": [],
        },
        {
            "source_id": "SRC-RUMOR",
            "level": "UNSOURCED_SECONDARY",
            "text": "An unsigned note says the method always wins.",
            "supports": [],
        },
        {
            "source_id": "SRC-MISMATCH",
            "level": "ASSUMPTION_MISMATCH",
            "text": (
                "The method assumes independent errors, while current sensors share a common "
                "calibration drift."
            ),
            "supports": ["assumption_mismatch"],
        },
    ]
    requested_claims = [
        "The legal discharge limit is 40 units/hour.",
        "Robust regression is automatically valid here.",
        "Sensors caused lower cost in the current county.",
        "The method always wins.",
    ]
    oracle = {
        "case_id": "CASE-006",
        "supported_claims": {"limit_40": ["SRC-AUTH"], "assumption_mismatch": ["SRC-MISMATCH"]},
        "unsupported": ["automatic method validity", "sensor causation", "always wins"],
        "method_adaptation": {
            "retain": "robust loss concept",
            "modify": "dependence-aware uncertainty or grouped errors",
            "remove": "independence guarantee",
        },
    }
    rubric = {
        "case_id": "CASE-006",
        "max_score": 70,
        "checks": [
            {
                "id": "LEVELS",
                "field": "data_findings",
                "groups": [
                    ["primary", "authority"],
                    ["method"],
                    ["unsourced", "rumor"],
                    ["mismatch"],
                ],
                "points": 10,
            },
            {"id": "LIMIT", "field": "claims", "groups": [["40"], ["SRC-AUTH"]], "points": 10},
            {
                "id": "NOCAUSAL",
                "field": "claims",
                "groups": [["sensor"], ["cannot", "not support", "no causal"]],
                "points": 8,
            },
            {
                "id": "NOWIN",
                "field": "claims",
                "groups": [["always wins"], ["unsupported", "cannot"]],
                "points": 7,
            },
            {
                "id": "ASSUMPTION",
                "field": "assumptions",
                "groups": [["independent"], ["calibration drift", "shared"]],
                "points": 8,
            },
            {
                "id": "RETAIN",
                "field": "formalization",
                "groups": [["retain"], ["robust loss"]],
                "points": 7,
            },
            {
                "id": "MODIFY",
                "field": "formalization",
                "groups": [["modify"], ["dependence", "grouped error", "correlated"]],
                "points": 7,
            },
            {
                "id": "REMOVE",
                "field": "formalization",
                "groups": [["remove"], ["independence guarantee", "independent"]],
                "points": 5,
            },
            {
                "id": "FACTS",
                "field": "claims",
                "groups": [["fact"], ["assumption"], ["experiment result", "result"]],
                "points": 5,
            },
            {
                "id": "NOFAKE",
                "field": "self_reported_limitations",
                "groups": [["doi", "external", "local only", "no network"]],
                "points": 3,
            },
        ],
    }
    case = _base_case(
        "CASE-006",
        "Source evidence and method adaptation",
        "Measure source hierarchy, support, and assumption adaptation",
        _common_prompt(
            "rank local sources, map supported and unsupported claims without inventing a DOI, "
            "create a retain/modify/remove method-adaptation contract, and separate facts, "
            "assumptions, and experiment results."
        ),
        ["input/sources.json", "input/requested_claims.json"],
        ["fabricated_source", "unsupported_claim", "assumption_mismatch", "causal_overclaim"],
        [
            "data_findings",
            "sources_used",
            "claims",
            "assumptions",
            "formalization",
            "self_reported_limitations",
        ],
        seed,
    )
    return {
        "input/sources.json": _json(sources),
        "input/requested_claims.json": _json(requested_claims),
        "oracle.json": _json(oracle),
        "rubric.json": _json(rubric),
        "case.json": _json(case),
    }


def generate_artifacts(seed: int = 20260831) -> dict[str, bytes]:
    builders = (_case_001, _case_002, _case_003, _case_004, _case_005, _case_006)
    artifacts: dict[str, bytes] = {}
    for builder in builders:
        bundle = builder(seed)
        case = json.loads(bundle.pop("case.json"))
        case_id = case["case_id"]
        rubric = bundle.pop("rubric.json")
        artifacts[f"evals/cases/phase-002/{case_id}.json"] = _json(case).encode()
        artifacts[f"evals/rubrics/phase-002/{case_id}.json"] = rubric.encode()
        for relative, content in bundle.items():
            artifacts[f"evals/fixtures/phase-002/{case_id}/{relative}"] = content.encode()
    hashes = {path: sha256_bytes(content) for path, content in sorted(artifacts.items())}
    manifest = {
        "schema_version": "1.0.0",
        "generator_version": GENERATOR_VERSION,
        "seed": seed,
        "cases": list(CASE_IDS),
        "files": hashes,
        "content_set_hash": sha256_text(canonical_json(hashes)),
    }
    artifacts["evals/fixtures/phase-002/manifest.json"] = _json(manifest).encode()
    return artifacts


def materialize(root: Path, *, seed: int = 20260831, check: bool = False) -> tuple[bool, list[str]]:
    artifacts = generate_artifacts(seed)
    mismatches: list[str] = []
    for relative, expected in sorted(artifacts.items()):
        path = root / relative
        actual = path.read_bytes() if path.is_file() else None
        if actual != expected:
            mismatches.append(relative)
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(expected)
    expected_paths = {root / relative for relative in artifacts}
    for base in (
        root / "evals/cases/phase-002",
        root / "evals/fixtures/phase-002",
        root / "evals/rubrics/phase-002",
    ):
        if base.exists():
            for path in base.rglob("*"):
                if path.is_file() and path not in expected_paths:
                    mismatches.append(path.relative_to(root).as_posix())
    return not mismatches, sorted(set(mismatches))


def fixture_manifest_hash(root: Path) -> str:
    return sha256_bytes((root / "evals/fixtures/phase-002/manifest.json").read_bytes())


def result_is_stale(root: Path, result: dict) -> bool:
    """A result is stale when it does not bind the current frozen fixture manifest."""
    return result.get("fixture_manifest_hash") != fixture_manifest_hash(root)
