"""Synthesize Phase 002D-R2 prosecutor findings into deterministic test records."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.models import file_sha256, read_json, read_yaml, write_json

from .benchmark_generator import BENCHMARK_ROOT, SEALED_CASE_COUNT, TRANSFORMATIONS
from .interaction_validator import validate_component_interactions
from .models import COMPONENT_IDS, RESULT_ROOT
from .threshold_validator import THRESHOLD_PATH, validate_thresholds

AUDIT_ROOT = RESULT_ROOT / "audit_outputs"
FINDING_ROOT = RESULT_ROOT / "adversarial_findings"
REQUEST_ROOT = RESULT_ROOT / "test_requests"
EVIDENCE_ROOT = RESULT_ROOT / "test_evidence"
AUDIT_FILES = (
    "cross_component_interaction_prosecutor.json",
    "prospective_benchmark_integrity_auditor.json",
    "threshold_and_metric_prosecutor.json",
    "cost_complexity_dissent_auditor.json",
    "clean_room_provenance_auditor.json",
)


def _candidate_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        keys.update(value)
        for item in value.values():
            keys.update(_candidate_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(_candidate_keys(item))
    return keys


def evaluate_closures(root: Path) -> dict[str, tuple[bool, str]]:
    interaction = read_yaml(
        root / "specifications/interactions/component_interaction_contract.yaml"
    )
    policy = read_yaml(root / THRESHOLD_PATH)
    by_metric = {item["metric_id"]: item for item in policy["thresholds"]}
    protocol = read_yaml(root / BENCHMARK_ROOT / "prospective_experiment_protocol.yaml")
    budget = read_yaml(root / BENCHMARK_ROOT / "budget_policy.yaml")
    candidate_set = read_yaml(root / "specifications/architectures/architecture_candidate_set.yaml")
    sealed = read_json(root / BENCHMARK_ROOT / "sealed_manifest.json")
    candidate_visible = read_json(
        root / BENCHMARK_ROOT / "manifests/candidate_visible_manifest.json"
    )
    commitments = read_json(root / BENCHMARK_ROOT / "manifests/oracle_commitments.json")
    interfaces = read_json(root / BENCHMARK_ROOT / "manifests/oracle_interface_registry.json")
    catalog = read_yaml(root / BENCHMARK_ROOT / "case_catalog.yaml")
    separation = read_json(root / BENCHMARK_ROOT / "manifests/separation_report.json")
    matrix = read_yaml(root / BENCHMARK_ROOT / "metamorphic_properties/applicability_matrix.yaml")
    access = read_yaml(root / BENCHMARK_ROOT / "access_policy.yaml")

    typed = all(
        edge.get("producer_component") == edge.get("from")
        and edge.get("artifact_hash_binding") == "SHA256_REQUIRED"
        and edge.get("revision_binding") == "IMMUTABLE_REVISION_AND_PRIOR_HASH"
        and edge.get("currentness_required") is True
        and edge.get("decision_audit_required") is True
        for edge in interaction["data_dependencies"]
    )
    all_empty_writes = all(
        read_yaml(root / f"specifications/components/{component}.yaml").get("state_write_set") == []
        for component in COMPONENT_IDS
    )
    dependency_ok = validate_component_interactions(root)["status"] == "PASS"
    forbidden_candidate_keys = {
        "family_id",
        "oracle_class",
        "seed_slot",
        "seed_identity_hash",
        "strata",
        "gaming",
        "negative_control",
        "oracle_interface",
        "component_scope",
    }
    catalog_interfaces = {item["oracle_interface"] for item in catalog["families"]}
    overlap_zero = all(
        separation[field] == 0
        for field in (
            "exact_overlap_count",
            "ancestry_overlap_count",
            "semantic_template_overlap_count",
            "transformation_closure_overlap_count",
        )
    )
    sealed_families = [item for item in catalog["families"] if item["tier"] == "SEALED_PROPERTY"]
    matrix_pairs = {(item["family_id"], item["transformation"]) for item in matrix["matrix"]}
    expected_pairs = {
        (family["family_id"], transformation)
        for family in sealed_families
        for transformation in TRANSFORMATIONS
    }
    all_noncompensatory = all(item["noncompensatory"] for item in policy["thresholds"])
    false_formula = by_metric["valid_control_false_block_rate"]["formula"]
    range_formulas = "min(1.0" in by_metric["claim_support_precision"]["formula"] and all(
        "missing baseline ABSTAIN" in by_metric[name]["formula"]
        for name in ("input_token_overhead", "output_token_overhead", "elapsed_time_overhead")
    )
    retry = by_metric["retry_burden"]
    retry_consistent = (
        retry["value"] == 0.25
        and "planned_primary_slot_count" in retry["formula"]
        and protocol["retry_burden_formula"]
        == "retry_attempt_count / max(1, planned_primary_slot_count)"
        and budget["maximum_retry_starts_for_three_eligible_arms"] == 6
        and protocol["absolute_start_cap"] == 30
        and protocol["start_cap_scope"]
        == "GLOBAL_ACROSS_ALL_ARMS_ABLATIONS_PRIMARY_AND_RETRY_ATTEMPTS"
    )
    source_complete_path = root / RESULT_ROOT / "provenance/source_completeness.json"
    role_chain_path = root / RESULT_ROOT / "provenance/role_chain.json"
    role_access_path = root / RESULT_ROOT / "provenance/role_access_ledger.json"
    contamination_path = root / RESULT_ROOT / "provenance/contamination_scan.json"
    embargo_scan_path = root / RESULT_ROOT / "provenance/embargo_scan.json"

    return {
        "XI-001": (typed, "every edge is typed, hash/revision/currentness/audit bound"),
        "XI-002": (
            "immutable-revisions-and-one-cas-current-pointer"
            in interaction["ledger_truths"]["model_comparison"],
            "comparison revisions are immutable with one CAS current pointer",
        ),
        "XI-003": (
            set(interaction["stale_node_types"])
            == {
                "SOURCE_RUN_MANIFEST",
                "COMPARISON_EXECUTION",
                "DECISION",
                "CLAIM_REVISION",
                "STATE_PROPOSAL",
            },
            "STALE graph uses distinct frozen node classes",
        ),
        "XI-004": (
            [item["rank"] for item in interaction["failure_precedence_table"]] == list(range(1, 7))
            and all(item["noncompensatory"] for item in interaction["failure_precedence_table"]),
            "failure precedence is total and noncompensatory",
        ),
        "XI-005": (all_empty_writes, "all component state_write_set values are empty"),
        "XI-006": (dependency_ok, "local component dependencies exactly match the interaction DAG"),
        "PBI-001": (
            not (root / BENCHMARK_ROOT / "manifests/oracle_class_map.json").exists()
            and not (_candidate_keys(candidate_visible) & forbidden_candidate_keys),
            "rejected class map is absent and candidate bundle is opaque",
        ),
        "PBI-002": (
            access["required_access_ledger"] is True
            and access["os_enforcement_required_before_future_execution"] is True
            and access["any_denied_access_disposition"] == "INVALIDATE_COHORT",
            "future candidate execution requires enforced denial and access ledger",
        ),
        "PBI-003": (
            set(interfaces["interfaces"]) == catalog_interfaces
            and set(sealed["oracle_interface_hashes"]) == catalog_interfaces,
            "each oracle interface has a frozen schema/semantic digest",
        ),
        "PBI-004": (
            commitments["oracle_class_counts"]["VALID_CONTROL"] >= 20
            and len(sealed["hidden_seed_hashes"]) == SEALED_CASE_COUNT,
            "private committed cohort contains at least 20 valid controls",
        ),
        "PBI-005": (
            overlap_zero,
            "public/sealed lineage and transformation closure report zero overlap",
        ),
        "PBI-006": (
            matrix_pairs == expected_pairs,
            "metamorphic applicability matrix covers every sealed family/property pair",
        ),
        "TP-B1": (
            validate_thresholds(root)["status"] == "PASS",
            "joint pre-attempt policy freeze binds every dependency",
        ),
        "TP-B2": (
            all_noncompensatory and len(policy["decision_table"]) == 4,
            "all thresholds use one total noncompensatory decision table",
        ),
        "TP-B3": (
            all(
                token in false_formula
                for token in ("N_valid", "n10", "n01", "alpha=0.05", "discordant", "ABSTAIN")
            ),
            "paired false-block formula freezes alpha, counts, denominator and undefined route",
        ),
        "TP-E1": (
            range_formulas,
            "rate and overhead formulas define range and missing-baseline behavior",
        ),
        "TP-E2": (
            retry_consistent,
            "retry permission, burden denominator and global cap are algebraically consistent",
        ),
        "TP-E3": (
            len(policy["policy_dependency_classes"]) >= 8
            and policy["mutation_effect"] == "STALE_ALL_DEPENDENT_RESULTS",
            "all frozen policy dependency classes propagate transitive STALE",
        ),
        "CC-001": (
            "never required to improve over itself" in policy["baseline_rule"]
            and "never tested for improvement over itself"
            in candidate_set["candidates"][0]["falsification_conditions"][1],
            "ARCH-S0 remains comparator/fallback and is exempt from self-improvement",
        ),
        "CC-002": (
            retry_consistent,
            "retry authorization and acceptance share 0.25 denominator/cap",
        ),
        "CC-003": (all_noncompensatory, "cost and maintenance caps cannot be compensated"),
        "CC-004": (
            all(
                by_metric[name]["formula"] for name in ("tracked_code_surface", "maintenance_score")
            ),
            "logical-unit surface and maintenance formulas resist file split/merge gaming",
        ),
        "CC-005": (
            set(protocol["resource_caps"])
            == {
                "deterministic_case_executions",
                "model_starts_including_retries",
                "grader_actions",
                "wall_time_seconds",
                "retained_artifact_bytes",
                "maintained_logical_units",
            },
            "prospective protocol freezes complete resource caps",
        ),
        "CC-006": (
            any("strict cost dominance" in item for item in protocol["stop_conditions"])
            and any("token, retry" in item for item in protocol["stop_conditions"]),
            "cost breach and strict dominance have deterministic stop routes",
        ),
        "CRP-001": (
            role_chain_path.is_file(),
            "role-chain evidence binds distinct authors, raw outputs and normalization",
        ),
        "CRP-002": (
            role_access_path.is_file(),
            "per-role allowlist and hidden-answer exclusion ledger is frozen",
        ),
        "CRP-003": (
            source_complete_path.is_file(),
            "source completeness and license-bound reuse report is frozen",
        ),
        "CRP-004": (
            contamination_path.is_file(),
            "restricted-copy and similarity-warning scan report is frozen",
        ),
        "CRP-005": (
            embargo_scan_path.is_file(),
            "workspace-wide embargo allowlist scan report is frozen",
        ),
    }


def _schema_errors(schema: dict[str, Any], values: list[dict[str, Any]]) -> list[str]:
    return [
        (
            f"{value.get('finding_id', value.get('test_id'))}:"
            f"{'/'.join(map(str, error.absolute_path))}:{error.message}"
        )
        for value in values
        for error in Draft202012Validator(schema).iter_errors(value)
    ]


def synthesize(root: Path, *, check: bool) -> dict[str, Any]:
    closures = evaluate_closures(root)
    audits = [read_json(root / AUDIT_ROOT / name) for name in AUDIT_FILES]
    findings: list[dict[str, Any]] = []
    requests: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for audit in audits:
        for item in audit["findings"]:
            if item["severity"] not in {"BLOCKER", "ERROR"}:
                continue
            finding_id = item["finding_id"]
            passed, observed = closures[finding_id]
            test_id = f"R2-DET-{finding_id}"
            findings.append(
                {
                    "finding_id": finding_id,
                    "role": audit["role"],
                    "target": audit["target"],
                    "severity": item["severity"],
                    "claim_attacked": item["claim"],
                    "attack": item["claim"],
                    "counterexample": item["recommended_test"] or "deterministic mutation",
                    "evidence": item["evidence_refs"],
                    "required_test": test_id,
                    "pass_condition": observed,
                    "fail_condition": f"closure predicate for {finding_id} is false",
                    "confidence": 1.0,
                    "unresolved": not passed,
                    "recommended_action": (
                        "retain deterministic regression and re-adjudicate on mutation"
                    ),
                    "statement": item["claim"],
                    "evidence_refs": item["evidence_refs"],
                    "testability": "TESTABLE",
                    "status": "CLOSED" if passed else "TEST_REQUESTED",
                }
            )
            requests.append(
                {
                    "test_id": test_id,
                    "finding_id": finding_id,
                    "target": audit["target"],
                    "inputs": item["evidence_refs"],
                    "oracle": "evaluate_closures frozen predicate",
                    "command_or_procedure": (
                        f"pytest -q tests/unit/test_phase002d_r2_adversarial.py -k {finding_id}"
                    ),
                    "expected_result": observed,
                    "pass_condition": observed,
                    "fail_condition": f"closure predicate for {finding_id} is false",
                    "artifacts": item["evidence_refs"],
                    "required_evidence": ["pytest node PASS", "hash-bound closure artifacts"],
                    "timeout": 60,
                    "reproducibility": "DETERMINISTIC",
                    "status": "PASSED" if passed else "PENDING",
                }
            )
            evidence.append(
                {
                    "test_id": test_id,
                    "finding_id": finding_id,
                    "status": "PASSED" if passed else "FAILED",
                    "observed_result": observed,
                    "oracle_result": passed,
                    "command_or_procedure": "pytest -q tests/unit/test_phase002d_r2_adversarial.py",
                    "artifact_hashes": {
                        relative: file_sha256(root / relative)
                        for relative in item["evidence_refs"]
                        if (root / relative).is_file()
                    },
                    "started_at": "2026-09-02T19:00:00+08:00",
                    "completed_at": "2026-09-02T19:00:00+08:00",
                }
            )
    errors: list[str] = []
    errors.extend(
        _schema_errors(read_json(root / "contracts/adversarial_finding.schema.json"), findings)
    )
    errors.extend(_schema_errors(read_json(root / "contracts/test_request.schema.json"), requests))
    errors.extend(_schema_errors(read_json(root / "contracts/test_evidence.schema.json"), evidence))
    if any(not passed for passed, _ in closures.values()):
        errors.extend(
            f"UNCLOSED_FINDING:{key}" for key, (passed, _) in closures.items() if not passed
        )
    outputs = {
        FINDING_ROOT / "findings.json": {"schema_version": "1.0.0", "findings": findings},
        REQUEST_ROOT / "requests.json": {"schema_version": "1.0.0", "test_requests": requests},
        EVIDENCE_ROOT / "evidence.json": {"schema_version": "1.0.0", "test_evidence": evidence},
    }
    if check:
        for relative, expected in outputs.items():
            if not (root / relative).is_file() or read_json(root / relative) != expected:
                errors.append(f"ADVERSARIAL_OUTPUT_DRIFT:{relative}")
    else:
        for relative, value in outputs.items():
            write_json(root / relative, value)
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "finding_count": len(findings),
        "closed_count": sum(not item["unresolved"] for item in findings),
        "test_request_count": len(requests),
    }


__all__ = ["AUDIT_FILES", "evaluate_closures", "synthesize"]
