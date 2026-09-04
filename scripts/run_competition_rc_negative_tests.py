#!/usr/bin/env python3
"""Run the fixed 30-scenario Competition RC fail-closed matrix."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import math
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_PATH = REPO_ROOT / ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py"
SENSITIVE_CANARIES = (
    "SYNTHETIC_PRIVATE_KEY_CANARY_DO_NOT_EMIT",
    "SYNTHETIC_REFRESH_TOKEN_CANARY_DO_NOT_EMIT",
)


def load_core():
    spec = importlib.util.spec_from_file_location("cumcm_case_negative", CORE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("RC_CORE_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def valid_context(core: Any) -> dict[str, Any]:
    return {
        "stage": core.STAGES[0],
        "enabled_components": ["workflow", "manifest", "comparison", "claim"],
        "execution_scope": "CASE",
    }


def valid_comparison(core: Any) -> tuple[dict[str, Any], dict[str, str]]:
    freezes = {
        "candidate_set": core.canonical_hash(["BASE", "CAND"]),
        "metric": core.canonical_hash({"name": "MAE", "direction": "MIN"}),
        "seed_schedule": core.canonical_hash([7]),
    }
    comparison = {
        "candidate_ids": ["BASE", "CAND"],
        "baseline_id": "BASE",
        "splits": {"train": [1], "validation": [2], "test": [3]},
        "metric": "MAE",
        "metric_direction": "MIN",
        "random_seeds": [7],
        "attempts": [
            {
                "candidate_id": "BASE",
                "run_id": "RUN-BASE",
                "outcome": "SUCCESS",
                "validation_score": 2.0,
                "random_seed": 7,
            },
            {
                "candidate_id": "CAND",
                "run_id": "RUN-CAND",
                "outcome": "SUCCESS",
                "validation_score": 1.0,
                "random_seed": 7,
            },
        ],
        "selected_candidate_id": "CAND",
        "freeze_bindings": copy.deepcopy(freezes),
        "leakage_checks": {
            "test_used_for_candidate_generation": False,
            "test_used_for_feature_selection": False,
            "test_used_for_threshold_selection": False,
            "future_information": False,
            "group_overlap": False,
            "target_in_features": False,
            "time_order_valid": True,
        },
        "test_access": {"authorized": True, "count": 1, "used_for_selection": False},
    }
    return comparison, freezes


def valid_manifest(core: Any, case_root: Path) -> tuple[dict[str, Any], dict[str, str]]:
    input_path = case_root / "data/raw/input.json"
    core.write_json(input_path, {"value": 1})
    input_file_hash = core.file_hash(input_path)
    output_path = case_root / "runs/RUN-CAND/output.json"
    core.write_json(output_path, {"metric": 1.0})
    output_file_hash = core.file_hash(output_path)
    freezes = {
        "candidate_set": core.canonical_hash(["BASE", "CAND"]),
        "metric": core.canonical_hash("MAE"),
        "seed_schedule": core.canonical_hash([7]),
    }
    configuration = {"candidate_id": "CAND", "seed": 7}
    manifest = {
        "run_id": "RUN-CAND",
        "input_files": [{"path": "data/raw/input.json", "sha256": input_file_hash}],
        "input_hash": core.canonical_hash([input_file_hash]),
        "code_commit": core.current_git_commit(),
        "code_files": [
            {
                "scope": "SKILL_ROOT",
                "path": "scripts/cumcm_case.py",
                "repository_path": ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py",
                "sha256": core.file_hash(core.SKILL_ROOT / "scripts/cumcm_case.py"),
            }
        ],
        "code_tree_hash": core.canonical_hash(
            [core.file_hash(core.SKILL_ROOT / "scripts/cumcm_case.py")]
        ),
        "configuration": configuration,
        "configuration_hash": core.canonical_hash(configuration),
        "random_seed": 7,
        "argv": ["model.py", "--run"],
        "cwd_policy": "CASE_ROOT_RELATIVE",
        "environment_allowlist": {"PYTHONHASHSEED": "0", "TZ": "UTC"},
        "output_files": [
            {
                "path": "runs/RUN-CAND/output.json",
                "sha256": output_file_hash,
            }
        ],
        "output_hash": core.canonical_hash([output_file_hash]),
        "outcome": "SUCCESS",
        "failure": None,
        "supersession": None,
        "trusted_capture": True,
        "freeze_bindings": freezes,
        "decision_hash": "4" * 64,
    }
    return manifest, freezes


def valid_claim(core: Any, manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "claim_id": "CLAIM-1",
        "claim_text": "candidate validation score is 1.0",
        "supported_scope": "candidate validation score is 1.0",
        "run_id": manifest["run_id"],
        "run_manifest_hash": core.canonical_hash(manifest),
        "input_hash": manifest["input_hash"],
        "code_hash": manifest["code_tree_hash"],
        "configuration_hash": manifest["configuration_hash"],
        "output_hash": manifest["output_hash"],
        "decision_hash": manifest["decision_hash"],
        "evidence_artifact_ids": ["EVIDENCE-1"],
        "evidence_status": "CURRENT",
        "contradiction_status": "NONE",
    }


def comparison_case(
    core: Any,
    mutate: Callable[[dict[str, Any], dict[str, str]], None],
) -> tuple[Any, Any, str]:
    value, freezes = valid_comparison(core)
    mutate(value, freezes)
    before = copy.deepcopy(value)
    result = core.validate_comparison(value, freezes)
    return result, value == before, "NONE"


def manifest_case(
    core: Any,
    case_root: Path,
    mutate: Callable[[dict[str, Any], dict[str, str]], None],
) -> tuple[Any, Any, str]:
    value, freezes = valid_manifest(core, case_root)
    mutate(value, freezes)
    before = copy.deepcopy(value)
    result = core.validate_manifest(
        value,
        case_root=case_root,
        trusted_freezes=freezes,
    )
    return result, value == before, "NONE"


def claim_case(
    core: Any,
    case_root: Path,
    mutate: Callable[[dict[str, Any], dict[str, Any]], None],
) -> tuple[Any, Any, str]:
    manifest, _ = valid_manifest(core, case_root)
    claim = valid_claim(core, manifest)
    mutate(claim, manifest)
    final = {
        "run_id": manifest["run_id"],
        "output_hash": manifest["output_hash"],
        "decision_hash": manifest["decision_hash"],
    }
    before = copy.deepcopy((claim, manifest, final))
    result = core.validate_claim(claim, manifest, final)
    return result, (claim, manifest, final) == before, "NONE"


def run_scenario(core: Any, case_root: Path, scenario_id: str) -> tuple[Any, bool, str]:
    if scenario_id == "01_MALFORMED_CONTEXT":
        payload: dict[str, Any] = {}
        context = None
        before = copy.deepcopy((payload, context))
        return core.boundary_validate(payload, context), (payload, context) == before, "NONE"
    if scenario_id == "02_MALFORMED_ENABLED_COMPONENTS":
        payload = {}
        context = valid_context(core)
        context["enabled_components"] = "workflow"
        before = copy.deepcopy((payload, context))
        return core.boundary_validate(payload, context), (payload, context) == before, "NONE"
    comparison_mutations: dict[str, Callable[[dict[str, Any], dict[str, str]], None]] = {
        "03_NAN_SCORE": lambda value, _freeze: value["attempts"][1].update(
            validation_score=math.nan
        ),
        "04_INF_SCORE": lambda value, _freeze: value["attempts"][1].update(
            validation_score=math.inf
        ),
        "05_NUMERIC_STRING_SCORE": lambda value, _freeze: value["attempts"][1].update(
            validation_score="1.0"
        ),
        "06_EMPTY_CANDIDATE_SET": lambda value, _freeze: value.update(candidate_ids=[]),
        "07_EMPTY_SPLIT": lambda value, _freeze: value["splits"].update(validation=[]),
        "08_FAILED_ATTEMPT_SCORED": lambda value, _freeze: value["attempts"][1].update(
            outcome="FAILED"
        ),
        "09_TEST_LEAKAGE": lambda value, _freeze: value["leakage_checks"].update(
            test_used_for_candidate_generation=True
        ),
        "10_FUTURE_LEAKAGE": lambda value, _freeze: value["leakage_checks"].update(
            future_information=True
        ),
        "11_GROUP_LEAKAGE": lambda value, _freeze: value["leakage_checks"].update(
            group_overlap=True
        ),
        "12_TARGET_LEAKAGE": lambda value, _freeze: value["leakage_checks"].update(
            target_in_features=True
        ),
        "13_UNAUTHORIZED_TEST_ACCESS": lambda value, _freeze: value["test_access"].update(
            authorized=False
        ),
        "14_ARBITRARY_FREEZE_HASH": lambda value, _freeze: value["freeze_bindings"].update(
            metric="f" * 64
        ),
    }
    if scenario_id in comparison_mutations:
        return comparison_case(core, comparison_mutations[scenario_id])
    manifest_mutations: dict[str, Callable[[dict[str, Any], dict[str, str]], None]] = {
        "15_PRIVATE_KEY": lambda value, _freeze: value.update(
            {"private-key": SENSITIVE_CANARIES[0]}
        ),
        "16_REFRESH_TOKEN": lambda value, _freeze: value.update(
            {"Refresh_Token": SENSITIVE_CANARIES[1]}
        ),
        "17_UNC_PATH": lambda value, _freeze: value.update(
            {"artifact_location": "\\\\server\\share"}
        ),
        "18_MANIFEST_MUTATION": lambda value, _freeze: value["output_files"][0].update(
            sha256="0" * 64
        ),
        "19_OUTPUT_HASH_MISMATCH": lambda value, _freeze: value.update(output_hash="0" * 64),
    }
    if scenario_id in manifest_mutations:
        return manifest_case(core, case_root, manifest_mutations[scenario_id])
    claim_mutations: dict[str, Callable[[dict[str, Any], dict[str, Any]], None]] = {
        "20_UNBOUND_VERIFIED_RUN_DECISION": lambda claim, _manifest: claim.pop("decision_hash"),
        "21_STALE_EVIDENCE": lambda claim, _manifest: claim.update(evidence_status="STALE"),
        "22_CONTRADICTORY_CLAIM": lambda claim, _manifest: claim.update(
            contradiction_status="CONTRADICTED"
        ),
        "23_UNSUPPORTED_CLAIM": lambda claim, _manifest: claim.update(
            claim_text="broader unsupported claim"
        ),
        "28_CROSS_COMPONENT_RUN_HASH_MISMATCH": lambda claim, _manifest: claim.update(
            output_hash="9" * 64
        ),
    }
    if scenario_id in claim_mutations:
        return claim_case(core, case_root, claim_mutations[scenario_id])
    if scenario_id == "24_DONE_WITHOUT_VALIDATION":
        core.initialize_case(case_root, "NEG-DONE-024", "general")
        draft = copy.deepcopy(
            core.load_json(case_root / core.ARTIFACT_PATHS["problem_requirements"])
        )
        try:
            core.advance_once(case_root)
        except ValueError as exc:
            return (
                core.blocked(*str(exc).split(";")),
                core.load_json(case_root / core.ARTIFACT_PATHS["problem_requirements"]) == draft,
                core.load_state(case_root)["state"],
            )
        return core.passed("UNEXPECTED_PASS"), False, core.load_state(case_root)["state"]
    if scenario_id in {"25_FORMAL_STATE_WRITE_ATTEMPT", "26_SECOND_STATE_TRUTH_ATTEMPT"}:
        context = {
            "writer": "modeling_orchestrator",
            "formal_project_state_write": False,
            "second_state_truth": False,
            "execution_scope": "CASE",
            "state_path": "case_state.json",
        }
        if scenario_id.startswith("25"):
            context["formal_project_state_write"] = True
        else:
            context["second_state_truth"] = True
        before = copy.deepcopy(context)
        return core.validate_state_boundary(context), context == before, "NONE"
    if scenario_id == "27_PRODUCTION_STAGE_ATTEMPT":
        payload = {}
        context = valid_context(core)
        context["execution_scope"] = "PRODUCTION"
        before = copy.deepcopy((payload, context))
        return core.boundary_validate(payload, context), (payload, context) == before, "NONE"
    if scenario_id == "29_UPSTREAM_STALE_PROPAGATION":
        core.initialize_case(case_root, "NEG-STALE-029", "general")
        accepted = core.artifact(
            "problem_requirements",
            {
                "case_id": "NEG-STALE-029",
                "requirements": [{"requirement_id": "R-1", "text": "test"}],
            },
        )
        artifact_path = case_root / core.ARTIFACT_PATHS["problem_requirements"]
        core.write_json(artifact_path, accepted)
        core.advance_once(case_root)
        accepted["content"]["requirements"][0]["text"] = "changed"
        accepted["content_hash"] = core.canonical_hash(accepted["content"])
        core.write_json(artifact_path, accepted)
        before = copy.deepcopy(accepted)
        result = core.stale_check(case_root, mutate=False)
        return result, core.load_json(artifact_path) == before, core.load_state(case_root)["state"]
    if scenario_id == "30_INCOMPLETE_MODELING_TO_PAPER_PACKAGE":
        handoff = {"contract_version": "modeling-to-paper/v1"}
        before = copy.deepcopy(handoff)
        return core.validate_handoff(handoff), handoff == before, "NONE"
    raise ValueError(f"unknown scenario: {scenario_id}")


EXPECTED = {
    "01_MALFORMED_CONTEXT": ("BLOCK", "RC_CONTEXT_INVALID"),
    "02_MALFORMED_ENABLED_COMPONENTS": ("BLOCK", "RC_CONTEXT_ENABLED_COMPONENTS_INVALID"),
    "03_NAN_SCORE": ("BLOCK", "RC_COMPARISON_SCORE_TYPE_OR_FINITE_INVALID"),
    "04_INF_SCORE": ("BLOCK", "RC_COMPARISON_SCORE_TYPE_OR_FINITE_INVALID"),
    "05_NUMERIC_STRING_SCORE": ("BLOCK", "RC_COMPARISON_SCORE_TYPE_OR_FINITE_INVALID"),
    "06_EMPTY_CANDIDATE_SET": ("BLOCK", "RC_COMPARISON_EMPTY_CANDIDATE_SET"),
    "07_EMPTY_SPLIT": ("BLOCK", "RC_COMPARISON_EMPTY_SPLIT"),
    "08_FAILED_ATTEMPT_SCORED": ("BLOCK", "RC_COMPARISON_NON_SUCCESS_ATTEMPT_SCORED"),
    "09_TEST_LEAKAGE": ("BLOCK", "RC_COMPARISON_LEAKAGE:test_used_for_candidate_generation"),
    "10_FUTURE_LEAKAGE": ("BLOCK", "RC_COMPARISON_LEAKAGE:future_information"),
    "11_GROUP_LEAKAGE": ("BLOCK", "RC_COMPARISON_LEAKAGE:group_overlap"),
    "12_TARGET_LEAKAGE": ("BLOCK", "RC_COMPARISON_LEAKAGE:target_in_features"),
    "13_UNAUTHORIZED_TEST_ACCESS": ("BLOCK", "RC_COMPARISON_UNAUTHORIZED_TEST_ACCESS"),
    "14_ARBITRARY_FREEZE_HASH": ("BLOCK", "RC_COMPARISON_UNTRUSTED_FREEZE"),
    "15_PRIVATE_KEY": ("BLOCK", "RC_SECRET_FIELD_REJECTED"),
    "16_REFRESH_TOKEN": ("BLOCK", "RC_SECRET_FIELD_REJECTED"),
    "17_UNC_PATH": ("BLOCK", "RC_PRIVATE_ABSOLUTE_PATH_REJECTED"),
    "18_MANIFEST_MUTATION": ("BLOCK", "RC_MANIFEST_OUTPUT_MUTATION"),
    "19_OUTPUT_HASH_MISMATCH": ("BLOCK", "RC_MANIFEST_OUTPUT_HASH_MISMATCH"),
    "20_UNBOUND_VERIFIED_RUN_DECISION": ("BLOCK", "RC_CLAIM_REQUIRED_BINDING_MISSING"),
    "21_STALE_EVIDENCE": ("BLOCK", "RC_CLAIM_STALE_EVIDENCE"),
    "22_CONTRADICTORY_CLAIM": ("BLOCK", "RC_CLAIM_CONTRADICTED"),
    "23_UNSUPPORTED_CLAIM": ("BLOCK", "RC_CLAIM_OVERBROAD_OR_UNSUPPORTED"),
    "24_DONE_WITHOUT_VALIDATION": ("BLOCK", "RC_ARTIFACT_NOT_ACCEPTED"),
    "25_FORMAL_STATE_WRITE_ATTEMPT": ("BLOCK", "RC_FORMAL_STATE_WRITE_PROHIBITED"),
    "26_SECOND_STATE_TRUTH_ATTEMPT": ("BLOCK", "RC_SECOND_STATE_TRUTH_PROHIBITED"),
    "27_PRODUCTION_STAGE_ATTEMPT": ("BLOCK", "RC_CONTEXT_EXECUTION_SCOPE_PROHIBITED"),
    "28_CROSS_COMPONENT_RUN_HASH_MISMATCH": ("BLOCK", "RC_CLAIM_RUN_BINDING_MISMATCH"),
    "29_UPSTREAM_STALE_PROPAGATION": ("STALE", "RC_UPSTREAM_DEPENDENCY_STALE"),
    "30_INCOMPLETE_MODELING_TO_PAPER_PACKAGE": ("BLOCK", "RC_HANDOFF_REQUIRED_FIELDS_MISSING"),
}


def evaluate(output: Path) -> dict[str, Any]:
    core = load_core()
    records: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="cumcm-rc-negative-") as temporary:
        root = Path(temporary)
        for scenario_id, (expected_status, expected_reason) in EXPECTED.items():
            case_root = root / scenario_id.casefold()
            try:
                result, unchanged, state = run_scenario(core, case_root, scenario_id)
                actual_status = result.status
                reason_codes = list(result.reason_codes)
                unhandled = False
            except Exception as exc:  # pragma: no cover - converted into auditable failure
                actual_status = "UNHANDLED_EXCEPTION"
                reason_codes = [f"{type(exc).__name__}"]
                unchanged = False
                state = "UNKNOWN"
                unhandled = True
            ready = state == "READY_FOR_PAPER_HANDOFF"
            passed_case = (
                actual_status == expected_status
                and expected_reason in reason_codes
                and unchanged
                and not unhandled
                and not ready
            )
            records.append(
                {
                    "scenario_id": scenario_id,
                    "expected_status": expected_status,
                    "expected_reason_code": expected_reason,
                    "actual_status": actual_status,
                    "reason_codes": reason_codes,
                    "input_unchanged": unchanged,
                    "unhandled_exception": unhandled,
                    "ready_for_paper_handoff": ready,
                    "pass": passed_case,
                }
            )
    serialized_records = json.dumps(records, ensure_ascii=False, sort_keys=True)
    sensitive_values_reported = sum(
        serialized_records.count(canary) for canary in SENSITIVE_CANARIES
    )
    payload = {
        "schema_version": "1.0.0",
        "skill_version": core.VERSION,
        "architecture": core.ARCHITECTURE,
        "scenario_count": len(records),
        "passed": sum(record["pass"] for record in records),
        "failed": sum(not record["pass"] for record in records),
        "unhandled_exceptions": sum(record["unhandled_exception"] for record in records),
        "sensitive_values_reported": sensitive_values_reported,
        "cases": records,
    }
    core.write_json(output, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = evaluate(args.output)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if payload["failed"] == 0 and payload["scenario_count"] == 30 else 1


if __name__ == "__main__":
    raise SystemExit(main())
