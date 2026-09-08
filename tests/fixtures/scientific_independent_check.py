"""Independent arithmetic residual check; imports no producer or optimization helper."""

import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads((args.case_root / "data/raw/input.json").read_text())
    path = args.case_root / "runs" / args.run_id / "output.json"
    output = json.loads(path.read_text())
    # Deliberately different from producer's sum/optimization expression.
    demand = 0
    for value in data["x"]:
        demand += value
    capacity = 0
    for value in data["y"]:
        capacity += value
    q = output["quantity"]
    constraints = {
        "demand": {"value": demand - q, "limit": 0, "relation": "LE", "tolerance": 1e-9},
        "capacity": {"value": q - capacity, "limit": 0, "relation": "LE", "tolerance": 1e-9},
    }
    result = {
        "run_id": args.run_id,
        "output_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "requirements": {
            req: {"feasible": demand <= q <= capacity, "constraint_residuals": constraints}
            for req in ["REQ-A", "REQ-B"]
        },
        "metric_values": {"metric_a": q, "metric_b": capacity - q},
    }
    args.output.write_text(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
