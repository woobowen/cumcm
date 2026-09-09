"""Construct a dual witness for an existing, fixed 2021 conditional transport LP.

This does not rerun or change the original supplier models or their selected plan.
The optimizer proposes multipliers; a separate exact-arithmetic verifier accepts them.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import lil_matrix


def construct(output: dict) -> dict:
    p = output["parameters"]
    suppliers = sorted(p["supplier_types"])
    carriers = sorted(p["carrier_loss_rates"])
    n, m = len(suppliers), len(carriers)
    capacity = [F(str(p["supplier_supply_capacity_m3"][s])) for s in suppliers]
    carrier_cap = F(str(p["carrier_capacity_m3"]))
    coefficients = [
        [
            (1 - F(str(p["carrier_loss_rates"][t])))
            / F(str(p["consumption"][p["supplier_types"][s]]))
            for t in carriers
        ]
        for s in suppliers
    ]
    matrix = lil_matrix((n * m, n + m))
    for i in range(n):
        for j in range(m):
            matrix[i * m + j, i] = -1
            matrix[i * m + j, n + j] = -1
    result = linprog(
        np.asarray([float(x) for x in capacity] + [float(carrier_cap)] * m),
        A_ub=matrix.tocsr(),
        b_ub=-np.asarray([[float(x) for x in row] for row in coefficients]).ravel(),
        bounds=(0, None),
        method="highs",
        options={"time_limit": 120},
    )
    if not result.success or not np.all(np.isfinite(result.x)):
        raise ValueError(f"DUAL_CONSTRUCTION_FAILED:{result.status}:{result.message}")
    # Repair every dual inequality with exact rational arithmetic. HiGHS status is
    # retained as diagnostic information and is never the acceptance certificate.
    v = [max(F(0), F(str(x))) for x in result.x[n:]]
    u = [max([F(0)] + [coefficients[i][j] - v[j] for j in range(m)]) for i in range(n)]
    original = output["question_4"]["weekly_plan_repeated_for_24_weeks"]["transport"]
    flows = {(r["supplier_id"], r["carrier_id"]): F(str(r["volume_m3"])) for r in original}
    if len(flows) != len(original) or any(x < 0 for x in flows.values()):
        raise ValueError("INVALID_ORIGINAL_FLOW")
    ratios = [F(1)]
    for i, s in enumerate(suppliers):
        total = sum((flows.get((s, t), F(0)) for t in carriers), F(0))
        if total:
            ratios.append(capacity[i] / total)
    for t in carriers:
        total = sum((flows.get((s, t), F(0)) for s in suppliers), F(0))
        if total:
            ratios.append(carrier_cap / total)
    scale = min(ratios)
    if scale <= 0:
        raise ValueError("NO_POSITIVE_FEASIBLE_SCALE")
    return {
        "schema_version": "rc8-development-q4-rational-certificate/v1",
        "scope": "FIXED_DECIMAL_PARAMETER_STATIONARY_TRANSPORT_LP",
        "solver_status_is_not_proof": True,
        "solver": {"name": "scipy.optimize.linprog/highs", "status": int(result.status)},
        "supplier_multipliers": dict(zip(suppliers, map(str, u), strict=True)),
        "carrier_multipliers": dict(zip(carriers, map(str, v), strict=True)),
        "primal_scale": str(scale),
        "primal_flows": [
            {"supplier_id": s, "carrier_id": t, "volume_m3": str(x * scale)}
            for (s, t), x in sorted(flows.items())
        ],
        "original_model_rerun": False,
        "final_access_count": 0,
        "whole_problem_scientifically_complete": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-output", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    raw = args.source_output.read_bytes()
    certificate = construct(json.loads(raw))
    certificate["source_output_sha256"] = hashlib.sha256(raw).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(certificate, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {"status": "CONSTRUCTED_PENDING_INDEPENDENT_VERIFICATION", "path": str(args.output)}
        )
    )


if __name__ == "__main__":
    main()
