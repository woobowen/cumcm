"""Synthetic scientific counterexamples only; never opens official inputs."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import c2021_independent_check as independent
import c2021_supply_plan as producer
import numpy as np
from c2021_feasibility import verify_plan


class ScientificRepairTests(unittest.TestCase):
    def make_case(self):
        order = np.full((3, 216), 20000.0)
        supply = order.copy()
        loss = np.full((8, 216), 1.0)
        data = producer.CaseData(
            ["S1", "S2", "S3"], ["A", "B", "C"], order, supply, [f"T{i}" for i in range(8)], loss
        )
        raw = {
            "supplier_ids": data.supplier_ids,
            "types": data.supplier_types,
            "carrier_ids": data.carrier_ids,
            "order": order,
            "supply": supply,
            "loss_pct": loss,
        }
        estimates = {
            "order_capacity": np.full(3, 30000.0),
            "delivery_ratio": np.ones(3),
            "delivered_capacity": np.full(3, 30000.0),
        }
        p = {
            "order_capacity": estimates["order_capacity"],
            "ratio": estimates["delivery_ratio"],
            "supply_capacity": estimates["delivered_capacity"],
            "loss": np.full(8, 0.01),
        }
        return data, raw, estimates, p

    def test_actual_supply_purchase_not_order(self):
        plan = {
            "orders": [{"supplier_id": "S1", "volume_m3": 100.0}],
            "transport": [{"supplier_id": "S1", "carrier_id": "T1", "volume_m3": 50.0}],
        }
        checked = verify_plan(
            plan,
            supplier_types={"S1": "A"},
            delivery_ratios={"S1": 0.5},
            carrier_loss_rates={"T1": 0.0},
            weekly_demand_product_m3=50 / 0.6,
            carrier_capacity_m3=6000.0,
        )
        self.assertTrue(checked["feasible"])
        self.assertEqual(checked["weekly_normalized_purchase_cost"], 60.0)

    def test_exact_cardinality_and_cost_loss_stages(self):
        data, raw, estimates, p = self.make_case()
        result = producer.optimize_lexicographic(data, estimates, p["loss"], 2, time_limit=10.0)
        self.assertTrue(result["lexicographic_complete"])
        self.assertEqual(result["actual_used_supplier_count"], 1)
        self.assertEqual(
            [r["stage"] for r in result["stages"]],
            [
                "MINIMUM_SUPPLIER_CARDINALITY",
                "MINIMUM_ALL_SUPPLY_PURCHASE_COST",
                "MINIMUM_TRANSPORT_LOSS_AT_FROZEN_COST",
            ],
        )
        self.assertEqual(result["stages"][0]["dual_bound"], 1.0)
        plan = producer.sparse_plan(data, estimates, result["allocation"], 28200.0)
        report = independent.recompute_plan(plan, raw, p, 2)
        self.assertTrue(report["feasible"])
        expected = 28200 * 0.6 * 1.2 / 0.99
        self.assertAlmostEqual(
            report["metric_values"]["weekly_all_supply_purchase_cost"], expected, places=3
        )
        # Fixed actual-supply capacity makes purchase cost invariant to the order ratio.
        changed = copy.deepcopy(estimates)
        changed["delivery_ratio"] = np.asarray([0.5, 1.0, 1.5])
        changed["order_capacity"] = changed["delivered_capacity"] / changed["delivery_ratio"]
        other = producer.optimize_lexicographic(data, changed, p["loss"], 2, time_limit=10.0)
        self.assertAlmostEqual(other["stages"][1]["incumbent_objective"], expected, places=3)

    def test_q3_material_and_q4_inventory(self):
        data, raw, estimates, p = self.make_case()
        q3 = producer.optimize_lexicographic(data, estimates, p["loss"], 3, time_limit=10.0)
        self.assertTrue(q3["lexicographic_complete"])
        self.assertLess(q3["allocation"][2].sum(), 1e-3)
        self.assertGreater(q3["allocation"][0].sum(), 10000.0)
        q4 = producer.optimize_lexicographic(data, estimates, p["loss"], 4, time_limit=10.0)
        self.assertTrue(q4["lexicographic_complete"])
        achieved = float(
            np.sum(q4["allocation"] * producer._effective_coefficients(data, p["loss"]))
        )
        self.assertGreater(achieved, 28200.0)
        plan = producer.sparse_plan(data, estimates, q4["allocation"], achieved)
        checked = independent.recompute_plan(plan, raw, p, 4)
        self.assertTrue(checked["feasible"])
        self.assertEqual(len(checked["inventory_trace_product_m3"]), 24)
        plan["initial_inventory_product_m3"] = 56400.0
        self.assertFalse(independent.recompute_plan(plan, raw, p, 4)["feasible"])

    def test_surplus_is_all_paid_and_overload_preserved(self):
        data, raw, estimates, p = self.make_case()
        q2 = producer.optimize_lexicographic(data, estimates, p["loss"], 2, time_limit=10.0)
        plan = producer.sparse_plan(data, estimates, q2["allocation"], 28200.0)
        raw["supply"][:, 168:] = raw["order"][:, 168:] * 3.5
        # CaseData shares raw arrays; realized 3.5 is deliberately beyond old ratio clipping.
        current = producer.historical_stress(data, plan, estimates, p["loss"])
        independent_stress = independent.recompute_stress(plan, raw, p, 2)
        self.assertFalse(current["conditional_historical_feasible"])
        self.assertFalse(independent_stress["feasible"])
        nominal = independent.recompute_plan(plan, raw, p, 2)["metric_values"][
            "weekly_all_supply_purchase_cost"
        ]
        self.assertAlmostEqual(
            current["weeks"][0]["all_supply_purchase_cost"], 3.5 * nominal, places=5
        )
        self.assertGreater(current["maximum_carrier_excess_m3"], 0.0)
        self.assertAlmostEqual(
            current["validation_penalized_cost_per_effective_m3"],
            independent_stress["metric_values"]["validation_penalized_cost_per_effective_m3"],
            places=7,
        )

    def test_inventory_shortfall_survives_and_compounds(self):
        data, raw, estimates, p = self.make_case()
        q2 = producer.optimize_lexicographic(data, estimates, p["loss"], 2, time_limit=10.0)
        plan = producer.sparse_plan(data, estimates, q2["allocation"], 28200.0)
        raw["supply"][:, 168:] = raw["order"][:, 168:] * 0.9
        checked = independent.recompute_stress(plan, raw, p, 2)
        self.assertFalse(checked["feasible"])
        self.assertEqual(checked["metric_values"]["stress_inventory_floor_violation_weeks"], 48)
        self.assertLess(checked["weeks"][23]["end_inventory_product_m3"], 0.0)
        self.assertGreater(checked["weeks"][24]["end_inventory_product_m3"], 0.0)

    def test_duplicate_and_under_shipment_rejected(self):
        data, raw, estimates, p = self.make_case()
        q2 = producer.optimize_lexicographic(data, estimates, p["loss"], 2, time_limit=10.0)
        plan = producer.sparse_plan(data, estimates, q2["allocation"], 28200.0)
        plan["transport"][0]["volume_m3"] *= 0.9
        self.assertFalse(independent.recompute_plan(plan, raw, p, 2)["feasible"])
        plan["orders"].append(copy.deepcopy(plan["orders"][0]))
        with self.assertRaisesRegex(ValueError, "DUPLICATE"):
            independent.recompute_plan(plan, raw, p, 2)

    def test_derived_csv_tables_are_real_but_template_gap_preserved(self):
        data, raw, estimates, p = self.make_case()
        q2 = producer.optimize_lexicographic(data, estimates, p["loss"], 2, time_limit=10.0)
        plan = producer.sparse_plan(data, estimates, q2["allocation"], 28200.0)
        result = {
            "parameters": {
                "supplier_types": dict(zip(data.supplier_ids, data.supplier_types, strict=True)),
                "carrier_loss_rates": dict(zip(data.carrier_ids, p["loss"], strict=True)),
            }
        }
        for q in [2, 3, 4]:
            result[f"question_{q}"] = {"weekly_plan_repeated_for_24_weeks": plan}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result["plan_table_artifacts"] = producer.write_plan_tables(
                root, root / "output.json", result
            )
            checked = independent.check_tables(root, result, raw)
            self.assertTrue(checked["derived_tables_consistent"])
            self.assertFalse(checked["feasible"])

    def test_synthetic_end_to_end_metric_binding_and_json_serialization(self):
        data, raw, _, _ = self.make_case()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "models").mkdir()
            (root / "models/assumptions_and_symbols.json").write_text(
                '{"scope":"synthetic test only"}\n'
            )
            output_path = root / "runs/SYNTHETIC/output.json"
            output_path.parent.mkdir(parents=True)
            with patch.object(producer, "load_case_data", return_value=data):
                result = producer.solve(root, "BASELINE_MEAN_GREEDY", 17)
            result["plan_table_artifacts"] = producer.write_plan_tables(root, output_path, result)
            result["scientific_evidence"] = producer.scientific_evidence(
                result, result["assumption_artifact_sha256"]
            )
            producer.bind_scientific_metrics(result)
            output_path.write_text(json.dumps(result, allow_nan=False))
            raw["input_hashes"] = {"SYNTHETIC": "NOT_OFFICIAL"}
            with patch.object(independent, "read_inputs", return_value=raw):
                checked = independent.check(root, "SYNTHETIC")
            json.dumps(checked, allow_nan=False)
            self.assertTrue(checked["producer_primary_metric_matches_independent"])
            for req, fact in result["scientific_evidence"].items():
                observed = checked["requirements"][req]["metric_values"]
                for metric, value in fact["metric_values"].items():
                    self.assertIn(metric, result["final_metrics"], (req, metric))
                    self.assertIn(metric, observed, (req, metric))
                    self.assertAlmostEqual(value, observed[metric], places=5, msg=(req, metric))
            certificate = checked["requirements"]["REQ-Q2-MINIMUM-SUPPLIERS"][
                "optimality_certificate"
            ]
            self.assertEqual(certificate["lower_bound"], certificate["upper_bound"])

    def test_official_hash_mismatch_stops_before_workbook_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in independent.RAW:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"synthetic invalid workbook")
            with patch.object(independent, "load_workbook") as workbook:
                with self.assertRaisesRegex(ValueError, "HASH_MISMATCH"):
                    independent.read_inputs(root)
                workbook.assert_not_called()

    def test_milp_timeout_and_missing_incumbent_preserved(self):
        data, _, estimates, p = self.make_case()
        feasible = producer.optimize_lexicographic(data, estimates, p["loss"], 2, time_limit=10.0)
        allocation = feasible["allocation"]
        selected = (allocation.sum(axis=1) > 1e-7).astype(float)
        timed = SimpleNamespace(
            status=1,
            message="synthetic time limit reached",
            success=False,
            x=np.r_[selected, allocation.ravel()],
            fun=float(selected.sum()),
            mip_dual_bound=0.5,
            mip_gap=0.5,
            mip_node_count=1,
        )
        with patch.object(producer, "milp", return_value=timed) as solver:
            result = producer.optimize_lexicographic(data, estimates, p["loss"], 2)
            self.assertEqual(solver.call_count, 1)
        self.assertFalse(result["lexicographic_complete"])
        self.assertIsNotNone(result["allocation"])
        self.assertEqual(result["stages"][0]["status_code"], 1)
        self.assertEqual(result["stages"][0]["relative_gap"], 0.5)
        timed.x = None
        timed.fun = None
        with patch.object(producer, "milp", return_value=timed):
            result = producer.optimize_lexicographic(data, estimates, p["loss"], 2)
        self.assertIsNone(result["allocation"])
        self.assertFalse(result["stages"][0]["has_incumbent"])


if __name__ == "__main__":
    unittest.main()
