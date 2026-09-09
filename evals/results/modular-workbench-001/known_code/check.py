"""Independent scalar normal equations from original workbook; no producer imports."""

import argparse
import hashlib
import json
from pathlib import Path

from openpyxl import load_workbook


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output_path = args.case_root / "runs" / args.run_id / "output.json"
    output = json.loads(output_path.read_text())
    plan = json.loads((args.case_root / "experiments/experiment_plan.json").read_text())["content"]
    book = load_workbook(args.case_root / "data/raw/appendix.xlsx", read_only=True, data_only=True)
    raw_rows = list(book["附件2"].values)[2:303]
    book.close()
    design = plan["temporal_design"]
    all_error = 0.0
    scores = []
    remaining = None
    for shift in (0, 1):
        errors = []
        for sample in design["samples"]:
            state = int(sample["feature_observation_ids"][0].split("-")[0][1:])
            size = len(sample["feature_observation_ids"])
            features = [f"S{state}-U{j}" for j in range(size)]
            if sample["feature_observation_ids"] != features:
                raise ValueError("KNOWN_Q3_FEATURE_PREFIX_IDENTITY_INVALID")
            actual_fit_ids = [f"S{s}-U{j}" for s in range(state) for j in range(301)] + features
            for field in ("preprocess_fit_observation_ids", "model_fit_observation_ids"):
                if set(sample[field]) != set(actual_fit_ids) or len(sample[field]) != len(
                    actual_fit_ids
                ):
                    raise ValueError("KNOWN_Q3_ACTUAL_FIT_LINEAGE_MISMATCH")
            x = [sum(float(r[s + 1]) for s in range(state)) / state for r in raw_rows]
            y = [float(raw_rows[j][state + 1]) + shift for j in range(size)]
            sx, sy = sum(x[:size]), sum(y)
            sxx = sum(t * t for t in x[:size])
            sxy = sum(a * b for a, b in zip(x[:size], y, strict=True))
            if output["candidate_id"] == "BASELINE":
                a, b = 0.0, sxy / sxx
            else:
                center_x, center_y = sx / size, sy / size
                variance = sum((t - center_x) ** 2 for t in x[:size])
                if variance <= 0:
                    raise ValueError("KNOWN_Q3_DEGENERATE_REFERENCE")
                b = (
                    sum((t - center_x) * (u - center_y) for t, u in zip(x[:size], y, strict=True))
                    / variance
                )
                a = center_y - b * center_x
            expected = [a + b * t for t in x]
            supplied = output["shifted_curves" if shift else "curves"][sample["sample_id"]]
            all_error = max(
                all_error, *(abs(a - b) for a, b in zip(expected, supplied, strict=True))
            )
            end = state * 10000 + expected[-1]
            if sample["split"] == "VALIDATION":
                truth = state * 10000 + float(raw_rows[-1][state + 1])
                denominator = truth - sample["origin"]
                assert denominator > 0
                errors.append(abs(end - truth) / denominator)
                if not shift:
                    row = next(
                        r
                        for r in output["metric_samples"]["q3_remaining_MRE"]
                        if r["sample_id"] == sample["sample_id"]
                    )
                    all_error = max(
                        all_error,
                        abs(row["predicted_end_time"] - end),
                        abs(row["observed_end_time"] - truth),
                        abs(row["origin"] - sample["origin"]),
                    )
            elif not shift:
                remaining = end - sample["origin"]
                value = output["scientific_evidence"]["REQ-Q3"]["prediction_evidence"][
                    "predictions"
                ][0]["value"]
                all_error = max(all_error, abs(remaining - value))
        scores.append(sum(errors) / len(errors))
    metrics = {"q3_remaining_MRE": scores[0], "q3_remaining_min": remaining}
    all_error = max(
        all_error,
        *(abs(output["final_metrics"][k] - v) for k, v in metrics.items()),
        abs(scores[1] - output["robustness_evidence"]["perturbations"][0]["result"]),
    )

    def residual(value, relation="EQ"):
        return {"value": value, "limit": 0, "relation": relation, "tolerance": 1e-6}

    result = {
        "run_id": args.run_id,
        "output_sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
        "requirements": {
            "REQ-Q3": {
                "feasible": remaining >= 0,
                "metric_values": metrics,
                "constraint_residuals": {"nonnegative_remaining": residual(remaining, "GE")},
                "recalculation_residuals": {
                    "every_curve_point_history_forecast_and_perturbation": residual(all_error)
                },
                "prediction_evidence": output["scientific_evidence"]["REQ-Q3"][
                    "prediction_evidence"
                ],
            }
        },
        "metric_definitions": plan["metric_definitions"],
        "metric_samples": output["metric_samples"],
        "temporal_lineage": design,
    }
    args.output.write_text(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
