"""Validate tracked prospective Benchmark artifacts without reading private vault contents."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.models import file_sha256, read_json, read_yaml, sha256_json

from .benchmark_generator import BENCHMARK_ROOT, TRANSFORMATIONS

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
        "benchmark_protocol.yaml",
        "case_catalog.yaml",
        "public_conformance/cases.json",
        "generators/generator_registry.yaml",
        "metamorphic_properties/properties.yaml",
        "negative_controls/catalog.yaml",
        "interaction_cases/catalog.yaml",
        "model_in_loop/catalog.yaml",
        "rubrics/rubric.yaml",
        "manifests/public_manifest.json",
        "sealed_manifest.json",
    )
    for relative in required:
        if not (benchmark_root / relative).is_file():
            errors.append(f"BENCHMARK_ARTIFACT_MISSING:{relative}")
    if errors:
        return {"status": "FAIL", "errors": errors}
    protocol = read_yaml(benchmark_root / "benchmark_protocol.yaml")
    catalog = read_yaml(benchmark_root / "case_catalog.yaml")
    public = read_json(benchmark_root / "public_conformance/cases.json")
    sealed = read_json(benchmark_root / "sealed_manifest.json")
    generator = read_yaml(benchmark_root / "generators/generator_registry.yaml")
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
    protocol_body = dict(protocol)
    protocol_hash = protocol_body.pop("benchmark_hash", None)
    if sha256_json(protocol_body) != protocol_hash:
        errors.append("BENCHMARK_PROTOCOL_HASH_MISMATCH")
    manifest_body = dict(sealed)
    manifest_hash = manifest_body.pop("manifest_hash", None)
    if sha256_json(manifest_body) != manifest_hash:
        errors.append("SEALED_MANIFEST_HASH_MISMATCH")
    generator_path = Path(__file__).with_name("benchmark_generator.py")
    current_generator_hash = file_sha256(generator_path)
    if generator.get("source_hash") != current_generator_hash:
        errors.append("GENERATOR_SOURCE_HASH_MISMATCH")
    if sealed.get("generator_hashes", {}).get("GEN-SYNTHETIC-V1") != current_generator_hash:
        errors.append("SEALED_GENERATOR_HASH_MISMATCH")
    if public.get("case_count") != 16 or len(public.get("cases", [])) != 16:
        errors.append("PUBLIC_CASE_COUNT_INVALID")
    if set(protocol.get("metamorphic_transformations", [])) != set(TRANSFORMATIONS):
        errors.append("METAMORPHIC_SET_INVALID")
    if len([item for item in families if item.get("negative_control")]) != 4:
        errors.append("NEGATIVE_CONTROL_COUNT_INVALID")
    if len([item for item in families if item.get("category") == "INTERACTION"]) != 4:
        errors.append("INTERACTION_CASE_COUNT_INVALID")
    if len([item for item in families if item.get("gaming")]) != 4:
        errors.append("GAMING_CASE_COUNT_INVALID")
    tracked_text = " ".join(
        path.read_text(encoding="utf-8") for path in benchmark_root.rglob("*") if path.is_file()
    ).lower()
    forbidden = (
        "arch-s0-retain",
        "arch-w1-workflow",
        "arch-k1-thin",
        "src/cumcm_skill_lab/components",
        "historical answer content",
    )
    for pattern in forbidden:
        if pattern in tracked_text:
            errors.append(f"BENCHMARK_FORBIDDEN_IMPLEMENTATION_HINT:{pattern}")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "public_case_count": len(public.get("cases", [])),
        "sealed_case_count": protocol.get("sealed_case_count"),
        "model_in_loop_case_count": protocol.get("model_in_loop_case_count"),
        "family_count": len(families),
        "manifest_hash": sealed.get("manifest_hash"),
        "historical_answers_used": protocol.get("historical_answers_used"),
        "prototype_runs": protocol.get("prototype_runs"),
    }


__all__ = ["validate_prospective_benchmark"]
