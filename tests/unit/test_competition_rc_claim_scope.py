"""Prospective neutral Claim contract tests; never use contest inputs or model calls."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest


@pytest.fixture
def core(repo_root):
    path = repo_root / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
    spec = importlib.util.spec_from_file_location("neutral_claim_core", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def bundle(core, root: Path, count=2, *, optional=False, same=False, legacy=False):
    """Synthetic unit context, not a registered contest Run or execution evidence."""
    ids = [f"REQ-N-{i}" for i in range(1, count + 1)]
    statement = "The aggregate is limited to the registered evidence."
    output_path = "runs/RUN-NEUTRAL/output.json"
    records = {
        rid: {
            "claim_id": f"CLAIM-N-{i}",
            "claim_text": statement if same else f"Bound synthetic scope {i}.",
            "evidence_artifact_ids": [output_path],
        }
        for i, rid in enumerate(ids, 1)
    }
    requirements = [
        {"requirement_id": rid, "text": f"Check synthetic quantity {i}.", "role": "PRIMARY"}
        for i, rid in enumerate(ids, 1)
    ]
    if optional:
        requirements += [
            {"requirement_id": f"REQ-{role}", "text": "Auxiliary scope.", "role": role}
            for role in ("OPTIONAL", "DIAGNOSTIC", "SUPPORTING")
        ]
    output = {
        "candidate_id": "NEUTRAL",
        "status": "SUCCESS",
        "claim_scope": statement,
        "requirement_claims": records,
        "final_metrics": {"synthetic_quantity": 1.0},
        "figure_ready_data": [{"figure_id": "NEUTRAL", "series": [1.0]}],
        "uncertainty": {"scope": "synthetic unit fixture"},
        "limitations": ["No contest or empirical inference."],
    }
    core.write_json(root / output_path, output)
    digest = core.file_hash(root / output_path)
    manifest = {
        "run_id": "RUN-NEUTRAL",
        "input_hash": "1" * 64,
        "code_tree_hash": "2" * 64,
        "configuration_hash": "3" * 64,
        "output_hash": core.canonical_hash([digest]),
        "decision_hash": "4" * 64,
        "output_files": [{"path": output_path, "sha256": digest}],
        "outcome": "SUCCESS",
        "supersession": None,
        "trusted_capture": True,
    }
    final = {
        "status": "FINAL_CANDIDATE",
        "selected_model": "NEUTRAL",
        "run_id": manifest["run_id"],
        "output_hash": manifest["output_hash"],
        "decision_hash": manifest["decision_hash"],
        "claim_scope": statement,
        "final_metrics": output["final_metrics"],
    }
    artifacts = {
        "problem_requirements": {"requirements": requirements},
        "source_ledger": {"sources": [{"source_id": "SRC-NEUTRAL", "kind": "PROJECT_ORIGINAL"}]},
        "assumptions_and_symbols": {
            "assumptions": ["Synthetic fixture."],
            "symbols": {"q": "quantity"},
            "formulas": ["q=1"],
        },
        "data_audit": {"raw_immutable": True, "data_hashes": {"data/raw/synthetic": "1" * 64}},
        "model_candidates": {"candidates": [{"candidate_id": "NEUTRAL", "baseline": True}]},
        "experiment_plan": {"handoff_generated_at": "2000-01-01T00:00:00Z"},
        "model_comparison": {
            "attempts": [{"run_id": "RUN-NEUTRAL", "outcome": "SUCCESS"}],
            "test_access": {"used_for_selection": False},
        },
        "robustness_analysis": {"failure_cases": ["Synthetic scope only."]},
        "final_result": final,
    }
    state = {"case_kind": "general", "evidence_bindings": {}}
    for key, value in artifacts.items():
        path = root / core.ARTIFACT_PATHS[key]
        core.write_json(path, core.artifact(key, value))
        state["evidence_bindings"][core.ARTIFACT_PATHS[key]] = core.file_hash(path)
    manifest_path = "runs/RUN-NEUTRAL/manifest.json"
    core.write_json(root / manifest_path, manifest)
    state["evidence_bindings"][manifest_path] = core.file_hash(root / manifest_path)
    state["evidence_bindings"][output_path] = digest
    claim = {
        "claim_id": "CLAIM-AGGREGATE-N",
        "claim_text": statement,
        "supported_scope": statement,
        "run_id": manifest["run_id"],
        "run_manifest_hash": core.canonical_hash(manifest),
        "input_hash": manifest["input_hash"],
        "code_hash": manifest["code_tree_hash"],
        "configuration_hash": manifest["configuration_hash"],
        "output_hash": manifest["output_hash"],
        "decision_hash": manifest["decision_hash"],
        "evidence_artifact_ids": [
            output_path,
            "results/model_comparison.json",
            "results/robustness.json",
            "results/final_result.json",
        ],
        "supported_requirement_ids": ids,
        "requirement_claims": copy.deepcopy(records),
        "evidence_status": "CURRENT",
        "contradiction_status": "NONE",
    }
    if legacy:
        claim["claim_id"] = records[ids[0]]["claim_id"]
        for req in requirements:
            req.pop("role", None)
        path = root / core.ARTIFACT_PATHS["problem_requirements"]
        core.write_json(path, core.artifact("problem_requirements", {"requirements": requirements}))
        state["evidence_bindings"][core.ARTIFACT_PATHS["problem_requirements"]] = core.file_hash(
            path
        )
    else:
        claim.update(
            contract_version="claim-evidence/v2",
            claim_kind="AGGREGATE_FINAL",
            scope_type="REQUIREMENT_UNION",
            aggregate_scope={rid: records[rid]["claim_text"] for rid in ids},
            supporting_requirement_claim_ids=[records[rid]["claim_id"] for rid in ids],
            requirement_bindings={
                rid: {
                    **{
                        key: claim[key]
                        for key in (
                            "run_id",
                            "run_manifest_hash",
                            "input_hash",
                            "code_hash",
                            "configuration_hash",
                            "output_hash",
                            "decision_hash",
                            "evidence_status",
                            "contradiction_status",
                        )
                    },
                    "claim_kind": "REQUIREMENT",
                    "requirement_id": rid,
                    "status": "ACCEPTED",
                }
                for rid in ids
            },
            non_primary_requirements={
                req["requirement_id"]: {"role": req["role"], "status": "NOT_CLAIMED"}
                for req in requirements
                if req.get("role") != "PRIMARY"
            },
        )
    path = root / core.ARTIFACT_PATHS["claim_evidence"]
    core.write_json(path, core.artifact("claim_evidence", claim))
    state["evidence_bindings"][core.ARTIFACT_PATHS["claim_evidence"]] = core.file_hash(path)
    return claim, manifest, final, state


def alter(core, root, name, claim, manifest, final, state):
    first = "REQ-N-1"
    binding = claim.get("requirement_bindings", {}).get(first, {})
    if name in {"claim_order", "file_order"}:
        claim["requirement_claims"] = dict(reversed(list(claim["requirement_claims"].items())))
    elif name == "support_order":
        claim["supporting_requirement_claim_ids"].reverse()
    elif name == "coverage_order":
        claim["supported_requirement_ids"].reverse()
    elif name in {"trace_order", "first_changed"}:
        path = root / core.ARTIFACT_PATHS["problem_requirements"]
        content = core.read_artifact(root, "problem_requirements")["content"]
        content["requirements"].reverse()
        core.write_json(path, core.artifact("problem_requirements", content))
        state["evidence_bindings"][core.ARTIFACT_PATHS["problem_requirements"]] = core.file_hash(
            path
        )
    elif name in {"missing", "handoff_missing", "legacy_invalid"}:
        claim["requirement_claims"].pop(first)
    elif name == "duplicate":
        claim["requirement_claims"]["REQ-N-2"] = copy.deepcopy(claim["requirement_claims"][first])
    elif name == "unknown":
        claim["requirement_claims"]["REQ-UNKNOWN"] = copy.deepcopy(
            claim["requirement_claims"][first]
        )
    elif name == "optional_as_primary":
        claim["supported_requirement_ids"].append("REQ-OPTIONAL")
    elif name in {"output_hash", "manifest_hash", "decision_hash", "wrong_run"}:
        field = {"manifest_hash": "run_manifest_hash", "wrong_run": "run_id"}.get(name, name)
        binding[field] = "RUN-WRONG" if field == "run_id" else "f" * 64
    elif name == "stale":
        binding["evidence_status"] = "STALE"
    elif name == "contradiction":
        binding["contradiction_status"] = "CONTRADICTED"
    elif name in {"superseded", "failed", "unsealed"}:
        if name == "superseded":
            manifest["supersession"] = "RUN-NEW"
        elif name == "failed":
            manifest["outcome"] = "FAILED"
        else:
            manifest["trusted_capture"] = False
        claim["run_manifest_hash"] = core.canonical_hash(manifest)
        for item in claim["requirement_bindings"].values():
            item["run_manifest_hash"] = claim["run_manifest_hash"]
    elif name == "overreach":
        claim["aggregate_scope"][first] = "Universal unsupported scope."
    elif name == "coverage_subset":
        claim["supported_requirement_ids"].pop()
    elif name == "coverage_extra":
        claim["supported_requirement_ids"].append("REQ-UNKNOWN")
    elif name == "coverage_duplicate":
        claim["supported_requirement_ids"].append(first)
    elif name == "support_duplicate":
        claim["supporting_requirement_claim_ids"].append("CLAIM-N-1")
    elif name == "output_missing":
        (root / manifest["output_files"][0]["path"]).unlink()
    elif name == "output_mutation":
        path = root / manifest["output_files"][0]["path"]
        value = core.load_json(path)
        value["final_metrics"]["synthetic_quantity"] = 999
        core.write_json(path, value)
    elif name == "final_lineage":
        final["decision_hash"] = "f" * 64
    elif name == "statement_overclaim":
        claim["claim_text"] = claim["supported_scope"] = "Universal optimality."
    elif name == "uncaptured_claim":
        claim["requirement_claims"][first]["claim_text"] = "An uncaptured value is 999."


MATRIX = [
    ("single", 1, None),
    ("two_scopes", 2, None),
    ("six_scopes", 6, None),
    ("claim_order", 2, None),
    ("support_order", 2, None),
    ("different_statement", 2, None),
    ("same_statement", 2, None),
    ("missing", 2, "RC_CLAIM_PRIMARY_REQUIREMENT_MISSING"),
    ("duplicate", 2, "RC_CLAIM_PRIMARY_REQUIREMENT_DUPLICATE"),
    ("unknown", 2, "RC_CLAIM_PRIMARY_REQUIREMENT_UNKNOWN"),
    ("optional_missing", 2, None),
    ("optional_as_primary", 2, "RC_CLAIM_AGGREGATE_COVERAGE_INVALID"),
    ("output_hash", 2, "RC_CLAIM_OUTPUT_BINDING_MISMATCH"),
    ("manifest_hash", 2, "RC_CLAIM_MANIFEST_HASH_MISMATCH"),
    ("decision_hash", 2, "RC_CLAIM_FINAL_DECISION_BINDING_MISMATCH"),
    ("stale", 2, "RC_CLAIM_EVIDENCE_STALE"),
    ("superseded", 2, "RC_CLAIM_RUN_NOT_CURRENT_SUCCESS"),
    ("failed", 2, "RC_CLAIM_RUN_NOT_CURRENT_SUCCESS"),
    ("unsealed", 2, "RC_CLAIM_RUN_UNSEALED"),
    ("contradiction", 2, "RC_CLAIM_CONTRADICTED"),
    ("overreach", 2, "RC_CLAIM_AGGREGATE_SCOPE_OVERREACH"),
    ("coverage_subset", 2, "RC_CLAIM_AGGREGATE_COVERAGE_INVALID"),
    ("coverage_extra", 2, "RC_CLAIM_AGGREGATE_COVERAGE_INVALID"),
    ("trace_order", 2, None),
    ("file_order", 2, None),
    ("first_changed", 2, None),
    ("legacy_single", 1, None),
    ("legacy_invalid", 1, "RC_CLAIM_PRIMARY_REQUIREMENT_MISSING"),
    ("handoff_complete", 2, None),
    ("handoff_missing", 2, "RC_CLAIM_PRIMARY_REQUIREMENT_MISSING"),
    ("wrong_run", 2, "RC_CLAIM_RUN_BINDING_MISMATCH"),
    ("coverage_order", 2, None),
    ("coverage_duplicate", 2, "RC_CLAIM_AGGREGATE_COVERAGE_INVALID"),
    ("support_duplicate", 2, "RC_CLAIM_AGGREGATE_COVERAGE_INVALID"),
    ("output_missing", 2, "RC_CLAIM_EVIDENCE_NOT_CURRENT_OR_MISSING"),
    ("output_mutation", 2, "RC_CLAIM_EVIDENCE_NOT_CURRENT_OR_MISSING"),
    ("final_lineage", 2, "RC_CLAIM_FINAL_RESULT_BINDING_MISMATCH"),
    ("statement_overclaim", 2, "RC_CLAIM_FINAL_SCOPE_MISMATCH"),
    ("uncaptured_claim", 2, "RC_CLAIM_OUTPUT_BINDING_MISMATCH"),
]


@pytest.mark.parametrize("name,count,reason", MATRIX, ids=[item[0] for item in MATRIX])
def test_neutral_claim_contract(core, tmp_path, name, count, reason):
    root = tmp_path / "neutral"
    values = bundle(
        core,
        root,
        count,
        optional=name.startswith("optional"),
        same=name in {"same_statement", "legacy_single", "legacy_invalid"},
        legacy=name.startswith("legacy"),
    )
    claim, manifest, final, state = values
    alter(core, root, name, *values)
    before = copy.deepcopy(values)
    result = core.validate_claim(claim, manifest, final, case_root=root, state=state)
    assert values == before
    assert result.accepted is (reason is None), result.as_dict()
    if reason:
        assert reason in result.reason_codes
    if name in {"handoff_complete", "handoff_missing", "optional_missing"}:
        path = root / core.ARTIFACT_PATHS["claim_evidence"]
        core.write_json(path, core.artifact("claim_evidence", claim))
        state["evidence_bindings"][core.ARTIFACT_PATHS["claim_evidence"]] = core.file_hash(path)
        if reason:
            try:
                handoff = core.build_expected_handoff(root, state)
            except (KeyError, ValueError):
                return
            assert not core.validate_handoff(handoff, case_root=root, state=state).accepted
        else:
            handoff = core.build_expected_handoff(root, state)
            assert core.validate_handoff(handoff, case_root=root, state=state).accepted
            assert set(handoff["requirement_traceability"]) == set(
                claim["supported_requirement_ids"]
            )
            assert handoff["validation_results"]["aggregate_claim"][
                "covered_primary_requirement_ids"
            ] == sorted(claim["supported_requirement_ids"])


def test_prospective_matrix_matches_frozen_expectations(repo_root):
    record = json.loads(
        (repo_root / "evals/results/phase-004c2/neutral_test_freeze.json").read_text()
    )
    assert record["expectations"] == [
        {
            "case": name,
            "primary_count": count,
            "expected": "PASS" if reason is None else "BLOCK",
            "reason_code": reason,
        }
        for name, count, reason in MATRIX
    ]
