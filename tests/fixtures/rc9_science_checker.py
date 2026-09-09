"""Independent normal-equation and error arithmetic; never imports the producer."""

import argparse
import hashlib
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--case-root", type=Path, required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    raw = json.loads((a.case_root / "data/raw/input.json").read_text())
    if a.output.name == "final_check.json" and raw.get("final_behavior"):
        a.output.write_text('{"partial": true}')
        print("partial output after Final STARTED", flush=True)
        if raw["final_behavior"] == "TIMEOUT":
            import time

            time.sleep(3)
        raise SystemExit(23)
    path = a.case_root / "runs" / a.run_id / "output.json"
    output = json.loads(path.read_text())
    plan = json.loads((a.case_root / "experiments/experiment_plan.json").read_text())["content"]
    reqs = json.loads((a.case_root / "problem/problem_requirements.json").read_text())["content"][
        "requirements"
    ]
    observations = {r["observation_id"]: r for r in raw.get("observations", [])}
    design = plan.get("temporal_design")
    bias = (
        float(output["candidate_id"] == "BASE")
        if raw["experiment_kind"] != "mixed"
        else float(output["candidate_id"] == "CAND")
    )
    ends = {}
    for sample in (design or {}).get("samples", []):
        rows = [observations[k] for k in sample["feature_observation_ids"]]
        n = len(rows)
        sx = sy = sxx = sxy = 0
        for row in rows:
            x, y = row["observed_at"], row["value"]
            sx += x
            sy += y
            sxx += x * x
            sxy += x * y
        slope = (n * sxy - sx * sy) / (n * sxx - sx * sx)
        intercept = (sy - slope * sx) / n
        ends[sample["sample_id"]] = (10 - intercept) / slope + bias
    metric_samples, requirements = {}, {}
    for req in reqs:
        key = req["requirement_id"]
        metric = next(iter(req["metric_contracts"]))
        definition = req["metric_contracts"][metric]
        if "prediction_spec" in req:
            records = []
            for s in design["samples"]:
                if s["split"] == "VALIDATION":
                    records.append(
                        {
                            "sample_id": s["sample_id"],
                            "target": definition["target"],
                            "unit": definition["target_unit"],
                            "origin": s["origin"],
                            "predicted_end_time": ends[s["sample_id"]],
                            "observed_end_time": observations[s["target_observation_id"]][
                                "observed_at"
                            ],
                        }
                    )
            for expected, supplied in zip(records, output["metric_samples"][metric], strict=True):
                assert set(expected) == set(supplied)
                assert all(
                    supplied[k] == expected[k] for k in expected if k != "predicted_end_time"
                )
            # Independent arithmetic uses a numeric tolerance; sample identity stays exact.
            residual = max(
                abs(x["predicted_end_time"] - y["predicted_end_time"])
                for x, y in zip(records, output["metric_samples"][metric], strict=True)
            )
            score = sum(
                abs(r["predicted_end_time"] - r["observed_end_time"])
                / (r["observed_end_time"] - r["origin"])
                * 100
                for r in records
            ) / len(records)
            prediction_rows = output["scientific_evidence"][key]["prediction_evidence"][
                "predictions"
            ]
            residual = max(
                residual,
                *(abs(p["value"] - (ends[p["sample_id"]] - p["origin"])) for p in prediction_rows),
            )
            constraint = {
                "value": min(p["value"] for p in prediction_rows),
                "limit": 0,
                "relation": "GE",
                "tolerance": 0,
            }
        else:
            demand = 0
            for number in raw["x"]:
                demand += number
            score = demand + int(output["candidate_id"] == "BASE")
            residual = abs(score - output["quantity"])
            constraint = {
                "value": output["quantity"] - demand,
                "limit": 0,
                "relation": "GE",
                "tolerance": 0,
            }
        assert residual < 1e-9
        assert abs(score - output["final_metrics"][metric]) < 1e-9
        metric_samples[metric] = output["metric_samples"][metric]
        requirements[key] = {
            "feasible": True,
            "metric_values": {metric: score},
            "constraint_residuals": {"domain": constraint},
            "recalculation_residuals": {
                "full_numeric_vector": {
                    "value": residual,
                    "limit": 0,
                    "relation": "EQ",
                    "tolerance": 1e-9,
                }
            },
        }
    for req in reqs:
        if "prediction_spec" in req:
            requirements[req["requirement_id"]]["prediction_evidence"] = output[
                "scientific_evidence"
            ][req["requirement_id"]]["prediction_evidence"]
    first_rows = metric_samples["metric_a"]
    if plan["metric_definitions"]["metric_a"]["formula"] == "ABSOLUTE_RELATIVE_ERROR":
        sensitivity = sum(
            abs(ends[r["sample_id"]] + 1 - r["observed_end_time"])
            / (r["observed_end_time"] - r["origin"])
            * 100
            for r in first_rows
        ) / len(first_rows)
    else:
        sensitivity = sum(raw["x"]) + int(output["candidate_id"] == "BASE") + 1
    assert abs(sensitivity - output["robustness_evidence"]["perturbations"][0]["result"]) < 1e-9
    result = {
        "run_id": a.run_id,
        "output_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "requirements": requirements,
        "metric_definitions": plan["metric_definitions"],
        "metric_samples": metric_samples,
        "temporal_lineage": design,
    }
    a.output.write_text(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
