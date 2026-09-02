"""Validate tracked prospective Benchmark artifacts without reading private vault contents."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.models import file_sha256, read_json, read_yaml, sha256_json

from .benchmark_generator import BENCHMARK_ROOT, COHORT_ID, SEALED_CASE_COUNT, TRANSFORMATIONS

CASE_CONTRACT = Path("contracts/prospective_case_family.schema.json")
BENCHMARK_CONTRACT = Path("contracts/prospective_benchmark.schema.json")
MANIFEST_CONTRACT = Path("contracts/sealed_benchmark_manifest.schema.json")


def _schema_errors(schema: dict[str, Any], value: Any, prefix: str) -> list[str]:
    return [
        f"{prefix}:{'/'.join(map(str, item.absolute_path))}:{item.message}"
        for item in Draft202012Validator(schema).iter_errors(value)
    ]


def validate_prospective_benchmark(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    benchmark_root = root / BENCHMARK_ROOT
    required = (
        "README.md",
        "access_policy.yaml",
        "benchmark_protocol.yaml",
        "case_catalog.yaml",
        "public_conformance/cases.json",
        "generators/generator_registry.yaml",
        "metamorphic_properties/properties.yaml",
        "metamorphic_properties/applicability_matrix.yaml",
        "negative_controls/catalog.yaml",
        "interaction_cases/catalog.yaml",
        "model_in_loop/catalog.yaml",
        "rubrics/rubric.yaml",
        "manifests/public_manifest.json",
        "manifests/oracle_commitments.json",
        "manifests/oracle_interface_registry.json",
        "manifests/candidate_visible_manifest.json",
        "manifests/separation_report.json",
        "sealed_manifest.json",
    )
    for relative in required:
        if not (benchmark_root / relative).is_file():
            errors.append(f"BENCHMARK_ARTIFACT_MISSING:{relative}")
    if (benchmark_root / "manifests/oracle_class_map.json").exists():
        errors.append("REJECTED_ORACLE_CLASS_MAP_STILL_TRACKED")
    if errors:
        return {"status": "FAIL", "errors": errors}

    protocol = read_yaml(benchmark_root / "benchmark_protocol.yaml")
    catalog = read_yaml(benchmark_root / "case_catalog.yaml")
    public = read_json(benchmark_root / "public_conformance/cases.json")
    sealed = read_json(benchmark_root / "sealed_manifest.json")
    generator = read_yaml(benchmark_root / "generators/generator_registry.yaml")
    commitments = read_json(benchmark_root / "manifests/oracle_commitments.json")
    interfaces = read_json(benchmark_root / "manifests/oracle_interface_registry.json")
    candidate = read_json(benchmark_root / "manifests/candidate_visible_manifest.json")
    separation = read_json(benchmark_root / "manifests/separation_report.json")
    access = read_yaml(benchmark_root / "access_policy.yaml")

    errors.extend(_schema_errors(read_json(root / BENCHMARK_CONTRACT), protocol, "BENCHMARK"))
    errors.extend(_schema_errors(read_json(root / MANIFEST_CONTRACT), sealed, "SEALED_MANIFEST"))
    case_schema = read_json(root / CASE_CONTRACT)
    families = catalog.get("families", [])
    for family in families:
        errors.extend(_schema_errors(case_schema, family, f"FAMILY:{family.get('family_id')}"))
        body = dict(family)
        recorded = body.pop("family_hash", None)
        if sha256_json(body) != recorded:
            errors.append(f"FAMILY_HASH_MISMATCH:{family.get('family_id')}")

    for value, hash_key, label in (
        (protocol, "benchmark_hash", "BENCHMARK_PROTOCOL"),
        (sealed, "manifest_hash", "SEALED_MANIFEST"),
    ):
        body = dict(value)
        recorded = body.pop(hash_key, None)
        if sha256_json(body) != recorded:
            errors.append(f"{label}_HASH_MISMATCH")

    generator_path = Path(__file__).with_name("benchmark_generator.py")
    current_generator_hash = file_sha256(generator_path)
    if generator.get("source_hash") != current_generator_hash:
        errors.append("GENERATOR_SOURCE_HASH_MISMATCH")
    if sealed.get("generator_hashes", {}).get("GEN-SYNTHETIC-V2") != current_generator_hash:
        errors.append("SEALED_GENERATOR_HASH_MISMATCH")
    if (
        sealed.get("cohort_id") != COHORT_ID
        or protocol.get("sealed_case_count") != SEALED_CASE_COUNT
    ):
        errors.append("SEALED_COHORT_ID_OR_COUNT_INVALID")
    if len(sealed.get("hidden_seed_hashes", {})) != SEALED_CASE_COUNT:
        errors.append("SEALED_SEED_COMMITMENT_COUNT_INVALID")
    if commitments.get("private_mapping_commitment") != sealed.get("private_oracle_commitment"):
        errors.append("PRIVATE_ORACLE_COMMITMENT_MISMATCH")
    if commitments.get("oracle_class_counts") != {"VALID_CONTROL": 20, "INVALID_CONTROL": 16}:
        errors.append("PRIVATE_ORACLE_AGGREGATE_COUNT_INVALID")
    if commitments.get("per_case_metadata_exposed_to_candidate") != []:
        errors.append("CANDIDATE_ORACLE_METADATA_EXPOSURE")
    if public.get("case_count") != 16 or len(public.get("cases", [])) != 16:
        errors.append("PUBLIC_CASE_COUNT_INVALID")
    if set(protocol.get("metamorphic_transformations", [])) != set(TRANSFORMATIONS):
        errors.append("METAMORPHIC_SET_INVALID")
    if len([item for item in families if item.get("negative_control")]) != 4:
        errors.append("NEGATIVE_CONTROL_FAMILY_COUNT_INVALID")
    if sum(item.get("case_count", 0) for item in families if item.get("negative_control")) != 20:
        errors.append("VALID_CONTROL_DENOMINATOR_INVALID")
    catalog_interfaces = {item.get("oracle_interface") for item in families}
    if set(interfaces.get("interfaces", {})) != catalog_interfaces:
        errors.append("ORACLE_INTERFACE_REGISTRY_INCOMPLETE")
    candidate_forbidden = {
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
    if candidate_forbidden & set(candidate):
        errors.append("CANDIDATE_VISIBLE_MANIFEST_METADATA_LEAK")
    if candidate.get("exposed_fields") != ["opaque_case_id", "payload"]:
        errors.append("CANDIDATE_VISIBLE_FIELD_SET_INVALID")
    overlap_fields = (
        "exact_overlap_count",
        "ancestry_overlap_count",
        "semantic_template_overlap_count",
        "transformation_closure_overlap_count",
    )
    if any(separation.get(field) != 0 for field in overlap_fields):
        errors.append("PUBLIC_SEALED_SEPARATION_FAILED")
    if (
        access.get("os_enforcement_required_before_future_execution") is not True
        or access.get("required_access_ledger") is not True
    ):
        errors.append("FUTURE_ACCESS_ENFORCEMENT_NOT_REQUIRED")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "cohort_id": sealed.get("cohort_id"),
        "public_case_count": len(public.get("cases", [])),
        "sealed_case_count": protocol.get("sealed_case_count"),
        "model_in_loop_case_count": protocol.get("model_in_loop_case_count"),
        "family_count": len(families),
        "manifest_hash": sealed.get("manifest_hash"),
        "historical_answers_used": protocol.get("historical_answers_used"),
        "prototype_runs": protocol.get("prototype_runs"),
    }


__all__ = ["validate_prospective_benchmark"]
