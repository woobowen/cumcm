"""Bounded synthetic scientific counterexamples, including the live output contract."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import model_pipeline as producer
import numpy as np
import scientific_checks as independent


def fixture():
    rng = np.random.default_rng(912)
    metadata = []
    known = []
    for number in range(1, 41):
        typ = "高钾" if number <= 20 else "铅钡"
        artifact = f"{number:02d}"
        metadata.append(
            {
                "artifact_id": artifact,
                "glass_type": typ,
                "pattern": ["A", "B", "C"][number % 3],
                "color": "未记录" if number % 7 == 0 else ["绿", "蓝"][number % 2],
                "surface_weathering": "风化" if number % 2 else "无风化",
            }
        )
        values = rng.gamma(1.5, 1.0, 14)
        values[0] += 70 if typ == "高钾" else 15
        values[8] += 1 if typ == "高钾" else 60
        values = values / values.sum() * 100
        known.append(
            {
                **metadata[-1],
                "sample_id": artifact,
                "composition": values,
                "total": 100.0,
                "valid": True,
                "local_weathering": metadata[-1]["surface_weathering"],
            }
        )
    # One paired artifact per type; all weighting remains at artifact level.
    for index in [0, 20]:
        sample = copy.deepcopy(known[index])
        sample["sample_id"] += "未风化点"
        sample["local_weathering"] = "无风化"
        sample["composition"] = (
            producer.close_composition(sample["composition"] + rng.uniform(0, 1, 14)) * 100
        )
        known.append(sample)
    unknown = [
        {
            "sample_id": f"U{i + 1}",
            "composition": known[i * 4]["composition"].copy(),
            "surface_weathering": "风化",
            "total": 100.0,
            "valid": True,
        }
        for i in range(8)
    ]
    return metadata, known, unknown


class Repairs(unittest.TestCase):
    def test_historical_test_groups_excluded_from_repeated_cv(self):
        metadata, known, _ = fixture()
        report = producer.grouped_repeated_cv_diagnostic(
            metadata, known, "BASELINE_RAW_CENTROID", 42
        )
        split = producer.deterministic_split(metadata)
        self.assertEqual(report["effective_group_count"], 32)
        self.assertEqual(report["held_out_group_predictions"], 64)
        self.assertEqual(report["n_repeats"], 2)
        self.assertFalse(set(report["effective_artifact_ids"]) & set(split["test"]))
        self.assertTrue(report["historical_internal_test_labels_exposed"])
        self.assertFalse(report["internal_test_split_is_sealed"])

    def test_hellinger_actual_composition_perturbation_changes_features(self):
        metadata, known, _ = fixture()
        changed, _ = producer.perturb_known(known, 113)
        _, base, _ = producer.artifact_level_dataset(metadata, known, "HELLINGER_KNN_COMPLETE")
        _, altered, _ = producer.artifact_level_dataset(metadata, changed, "HELLINGER_KNN_COMPLETE")
        self.assertGreater(float(np.linalg.norm(base - altered)), 0.01)
        np.testing.assert_allclose(known[0]["composition"].sum(), 100.0)

    def test_artifact_equal_weathering_centers_ignore_extra_identical_points(self):
        _, known, _ = fixture()
        effects, _ = producer.weathering_analysis(known, "CLR_RIDGE_WARD")
        duplicates = copy.deepcopy(known) + [copy.deepcopy(known[2]) for _ in range(30)]
        alternate, _ = producer.weathering_analysis(duplicates, "CLR_RIDGE_WARD")
        for typ in producer.TYPE_TO_INT:
            for key in ["unweathered_center_percent", "weathered_center_percent"]:
                np.testing.assert_allclose(
                    list(effects[typ][key].values()), list(alternate[typ][key].values()), atol=1e-9
                )
        self.assertEqual(sum(r["paired_artifact_n"] for r in effects.values()), 2)

    def test_undefined_correlations_preserved_as_null(self):
        values = np.ones((8, 14))
        values[:, 1] = np.arange(8)
        first = producer.correlation_matrix(values)
        second = independent.spearman(values)
        self.assertTrue(np.isnan(first[0, 1]))
        self.assertTrue(np.isnan(second[0, 1]))
        self.assertIsNone(producer.nullable_matrix(first)[0][1])
        self.assertEqual(producer.nullable_matrix(first)[1][1], 1.0)

    def test_sparse_permutation_is_bounded_and_nonzero(self):
        metadata, _, _ = fixture()
        result = producer.contingency_result(metadata, "color", 5)
        self.assertEqual(result["permutation_replicates"], 999)
        self.assertGreaterEqual(result["permutation_p_value"], 0.001)
        self.assertLessEqual(result["permutation_p_value"], 1.0)

    def test_raw_hash_mismatch_before_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / independent.WORKBOOK
            path.parent.mkdir(parents=True)
            path.write_bytes(b"synthetic not a workbook")
            with patch.object(independent, "load_workbook") as reader:
                with self.assertRaisesRegex(ValueError, "HASH_MISMATCH"):
                    independent.read_raw(root)
                reader.assert_not_called()

    def test_three_synthetic_producers_independent_checks_and_live_contract(self):
        repo = Path(__file__).resolve().parents[8]
        core_path = repo / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
        if not core_path.is_file():
            repo = next(
                parent
                for parent in Path(__file__).resolve().parents
                if (
                    parent / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
                ).is_file()
            )
            core_path = repo / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
        spec = importlib.util.spec_from_file_location("c2022_current_output_contract", core_path)
        core = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = core
        spec.loader.exec_module(core)
        metadata, known, unknown = fixture()
        for candidate in producer.CANDIDATES:
            with self.subTest(candidate=candidate), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "models").mkdir()
                (root / "models/assumptions_and_symbols.json").write_text(
                    '{"scope":"synthetic-only"}\n'
                )
                with patch.object(
                    producer, "load_official_workbook", return_value=(metadata, known, unknown)
                ):
                    output = producer.solve(root, candidate, 53)
                output["requirement_claims"] = producer.requirement_claims(
                    "runs/SYNTHETIC/output.json"
                )
                output["claim_scope"] = output["requirement_claims"]["REQ-VALIDITY"]["claim_text"]
                output = producer.json_safe(output)
                contract = core.validate_selected_output_contract(
                    output,
                    expected_candidate_id=candidate,
                    required_requirement_ids=list(output["requirement_claims"]),
                )
                self.assertEqual(contract.status, "PASS", contract.as_dict())
                path = root / "runs/SYNTHETIC/output.json"
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps(output, allow_nan=False))
                with patch.object(independent, "read_raw", return_value=(metadata, known, unknown)):
                    checked = independent.verify_output(root, "SYNTHETIC")
                json.dumps(checked, allow_nan=False)
                self.assertEqual(checked["scientific_metric_binding_mismatch_count"], 0)
                for req, record in checked["requirements"].items():
                    if req in ["REQ-3A", "REQ-EVIDENCE"]:
                        self.assertFalse(record["feasible"])
                    else:
                        self.assertTrue(record["feasible"], (req, record))
                self.assertEqual(
                    output["scientific_evidence"]["REQ-3A"]["generation_method"], "PREDICTION"
                )
                self.assertEqual(output["scientific_evidence"]["REQ-3A"]["status"], "INSUFFICIENT")
                self.assertFalse(output["whole_problem_scientifically_complete"])


if __name__ == "__main__":
    unittest.main()
