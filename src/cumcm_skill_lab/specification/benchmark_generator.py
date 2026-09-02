"""Generate synthetic prospective Benchmark metadata; never execute a component or model."""

from __future__ import annotations

import hashlib
import json
import random
import secrets
import subprocess
from pathlib import Path
from typing import Any

from cumcm_skill_lab.adjudication.models import file_sha256, read_json, sha256_json, write_json

from .models import COMPONENT_IDS

BENCHMARK_ROOT = Path("evals/prospective/phase-002d-r2")
VAULT_ROOT = Path("benchmark-vault/phase-002d-r2")
ISOLATION_LEVEL = "POLICY_AND_WORKSPACE_ISOLATED_NOT_OS_ENFORCED"
TRANSFORMATIONS = (
    "row_permutation",
    "column_renaming",
    "unit_conversion",
    "benign_noise",
    "extra_irrelevant_field",
    "time_shift",
    "entity_relabeling",
    "file_order_permutation",
    "evidence_order_permutation",
    "claim_order_permutation",
)


def generate_case(seed: int, family_id: str) -> dict[str, Any]:
    """Generate an implementation-neutral deterministic synthetic case from a public interface."""
    rng = random.Random(f"{seed}:{family_id}")
    rows = [
        {"entity": f"E{index}", "measure": rng.randint(20, 900), "unit": "base"}
        for index in range(4)
    ]
    return {
        "family_id": family_id,
        "field_alias": f"v{rng.randrange(100, 999)}",
        "rows": rows,
        "evidence_order": rng.sample(["E-A", "E-B", "E-C"], 3),
        "noise_scale": rng.choice([0, 1, 2]),
    }


def apply_metamorphic(case: dict[str, Any], transformation: str) -> dict[str, Any]:
    """Apply a public semantics-preserving transformation for conformance testing."""
    value = json.loads(json.dumps(case))
    if transformation in {"row_permutation", "file_order_permutation"}:
        value["rows"] = list(reversed(value["rows"]))
    elif transformation == "column_renaming":
        value["field_alias"] = "renamed_measure"
    elif transformation == "unit_conversion":
        for row in value["rows"]:
            row["measure"] *= 100
            row["unit"] = "centi"
    elif transformation == "benign_noise":
        value["benign_note"] = "synthetic-noise"
    elif transformation == "extra_irrelevant_field":
        value["irrelevant"] = 1
    elif transformation == "time_shift":
        value["relative_time_offset"] = 7
    elif transformation == "entity_relabeling":
        for index, row in enumerate(value["rows"]):
            row["entity"] = f"R{index}"
    elif transformation == "evidence_order_permutation":
        value["evidence_order"] = list(reversed(value["evidence_order"]))
    elif transformation == "claim_order_permutation":
        value["claim_order"] = ["C2", "C1"]
    else:
        raise ValueError(f"UNKNOWN_METAMORPHIC_TRANSFORMATION:{transformation}")
    return value


def _family(
    family_id: str,
    tier: str,
    scope: list[str],
    category: str,
    count: int,
    *,
    negative: bool = False,
    gaming: bool = False,
) -> dict[str, Any]:
    body = {
        "family_id": family_id,
        "tier": tier,
        "component_scope": scope,
        "category": category,
        "generator_id": "GEN-SYNTHETIC-V1",
        "case_count": count,
        "oracle_interface": f"ORACLE-{category}-V1",
        "transformations": list(TRANSFORMATIONS),
        "negative_control": negative,
        "gaming": gaming,
        "frozen_before_prototype": True,
    }
    return {**body, "family_hash": sha256_json(body)}


def _families() -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for index, component_id in enumerate(COMPONENT_IDS, start=1):
        values.append(
            _family(
                f"R2-TARGET-{index}",
                "SEALED_PROPERTY",
                [component_id],
                "TARGETED",
                2,
            )
        )
    for index in range(1, 5):
        values.append(
            _family(
                f"R2-INTERACTION-{index}",
                "SEALED_PROPERTY",
                list(COMPONENT_IDS),
                "INTERACTION",
                1,
            )
        )
        values.append(
            _family(
                f"R2-NEGATIVE-{index}",
                "SEALED_PROPERTY",
                [COMPONENT_IDS[index - 1]],
                "VALID_NEGATIVE_CONTROL",
                1,
                negative=True,
            )
        )
        values.append(
            _family(
                f"R2-GAMING-{index}",
                "SEALED_PROPERTY",
                [COMPONENT_IDS[index - 1]],
                "ADVERSARIAL_GAMING",
                1,
                gaming=True,
            )
        )
        values.append(
            _family(
                f"R2-MODEL-{index}",
                "MODEL_IN_LOOP_FUTURE",
                [COMPONENT_IDS[index - 1]],
                "COMPOSITE",
                2,
            )
        )
    return values


def _public_cases() -> list[dict[str, Any]]:
    cases = []
    relations = ("valid control", "missing evidence", "stale mutation", "gaming attempt")
    for component_id in COMPONENT_IDS:
        for index, relation in enumerate(relations, start=1):
            body = {
                "case_id": f"PUBLIC-{component_id.upper()}-{index:02d}",
                "component_id": component_id,
                "synthetic_input_class": relation,
                "oracle_relation": "deterministic specification oracle",
                "generalization_evidence": False,
            }
            cases.append({**body, "case_hash": sha256_json(body)})
    return cases


def _benchmark_protocol(families: list[dict[str, Any]]) -> dict[str, Any]:
    body = {
        "schema_version": "1.0.0",
        "benchmark_id": "PHASE-002D-R2-PROSPECTIVE-BENCHMARK-001",
        "status": "BENCHMARK_FROZEN",
        "prospective": True,
        "synthetic_only": True,
        "historical_answers_used": False,
        "third_party_examples_used": False,
        "implementation_specific_fields": False,
        "public_case_count": 16,
        "sealed_case_count": 20,
        "model_in_loop_case_count": 8,
        "case_family_ids": [item["family_id"] for item in families],
        "metamorphic_transformations": list(TRANSFORMATIONS),
        "isolation_level": ISOLATION_LEVEL,
        "prototype_runs": 0,
    }
    return {**body, "benchmark_hash": sha256_json(body)}


def _tracked_values(root: Path, seed_hashes: dict[str, str]) -> dict[Path, Any]:
    families = _families()
    public_cases = _public_cases()
    protocol = _benchmark_protocol(families)
    sealed_families = [item for item in families if item["tier"] == "SEALED_PROPERTY"]
    case_slots = [
        (family, index)
        for family in sealed_families
        for index in range(1, family["case_count"] + 1)
    ]
    seed_identities = sorted(seed_hashes.items())
    if len(case_slots) != len(seed_identities):
        raise ValueError("SEALED_CASE_SEED_CARDINALITY_MISMATCH")
    oracle_records = []
    for (family, index), (seed_slot, seed_hash) in zip(case_slots, seed_identities, strict=True):
        oracle_records.append(
            {
                "case_slot_id": f"{family['family_id']}-{index:02d}",
                "family_id": family["family_id"],
                "oracle_class": (
                    "VALID_CONTROL" if family["negative_control"] else "INVALID_CONTROL"
                ),
                "strata": [family["category"], *family["component_scope"]],
                "seed_slot": seed_slot,
                "seed_identity_hash": seed_hash,
                "inclusion": "INCLUDED",
                "exclusion_reason": None,
            }
        )
    values: dict[Path, Any] = {
        Path("benchmark_protocol.yaml"): protocol,
        Path("case_catalog.yaml"): {"schema_version": "1.0.0", "families": families},
        Path("public_conformance/cases.json"): {"case_count": 16, "cases": public_cases},
        Path("generators/generator_registry.yaml"): {
            "generator_id": "GEN-SYNTHETIC-V1",
            "input": "integer seed and family ID",
            "deterministic": True,
            "architecture_names_present": False,
            "implementation_paths_present": False,
            "candidate_arms_present": False,
            "source_hash": file_sha256(Path(__file__)),
        },
        Path("metamorphic_properties/properties.yaml"): {
            "properties": list(TRANSFORMATIONS),
            "expected_relation": "irrelevant transformations preserve the specification oracle",
        },
        Path("negative_controls/catalog.yaml"): {
            "family_ids": [item["family_id"] for item in families if item["negative_control"]],
            "purpose": "measure false blocking on valid synthetic inputs",
        },
        Path("interaction_cases/catalog.yaml"): {
            "family_ids": [
                item["family_id"] for item in families if item["category"] == "INTERACTION"
            ]
        },
        Path("model_in_loop/catalog.yaml"): {
            "status": "FROZEN_FOR_FUTURE_EXECUTION",
            "executed_in_phase_002d_r2": False,
            "family_ids": [
                item["family_id"] for item in families if item["category"] == "COMPOSITE"
            ],
            "repeats_per_family": 2,
        },
        Path("rubrics/rubric.yaml"): {
            "oracle_source": "project-authored synthetic interface",
            "hard_failures_noncompensatory": True,
            "unknown_is_not_zero": True,
            "recovery_evidence_ranked": False,
        },
        Path("manifests/oracle_class_map.json"): {
            "schema_version": "1.0.0",
            "frozen_before_prototype": True,
            "candidate_results_present": False,
            "record_count": len(oracle_records),
            "records": oracle_records,
        },
    }
    artifact_hashes = {path.as_posix(): sha256_json(value) for path, value in values.items()}
    family_hashes = {item["family_id"]: item["family_hash"] for item in families}
    generator_hash = values[Path("generators/generator_registry.yaml")]["source_hash"]
    manifest_body = {
        "schema_version": "1.0.0",
        "manifest_id": "PHASE-002D-R2-SEALED-BENCHMARK-001",
        "status": "BENCHMARK_FROZEN",
        "benchmark_hash": protocol["benchmark_hash"],
        "generator_hashes": {"GEN-SYNTHETIC-V1": generator_hash},
        "family_hashes": family_hashes,
        "public_artifact_hashes": artifact_hashes,
        "hidden_seed_hashes": seed_hashes,
        "oracle_interface_hashes": {
            "ORACLE-INTERFACE-V1": hashlib.sha256(
                b"project-authored-synthetic-oracle-v1"
            ).hexdigest()
        },
        "hidden_case_count": 20,
        "isolation_level": ISOLATION_LEVEL,
        "vault_path": "IGNORED-PHASE-002D-R2-VAULT",
        "contains_hidden_seed": False,
        "contains_hidden_oracle": False,
        "frozen_before_prototype": True,
    }
    sealed = {**manifest_body, "manifest_hash": sha256_json(manifest_body)}
    values[Path("manifests/public_manifest.json")] = {
        "artifact_hashes": artifact_hashes,
        "public_case_hashes": {item["case_id"]: item["case_hash"] for item in public_cases},
    }
    values[Path("sealed_manifest.json")] = sealed
    return values


README = """# Phase 002D-R2 Prospective Benchmark

This is a synthetic, prospective Benchmark frozen before prototype implementation. Public cases
provide conformance feedback, not generalization evidence. Exact hidden seeds and oracle parameters
remain in the ignored workspace vault. Isolation is policy/workspace based and is not OS-enforced.
No historical CUMCM answer, third-party example, model run, API call or prototype execution is used.
"""


def _write_vault(root: Path) -> dict[str, str]:
    vault = root / VAULT_ROOT
    if vault.exists():
        raise ValueError("VAULT_ALREADY_EXISTS_REFUSE_OVERWRITE")
    check = subprocess.run(
        ["git", "check-ignore", VAULT_ROOT.as_posix()],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if check.returncode != 0:
        raise ValueError("VAULT_NOT_ISOLATED")
    seeds = {f"R2-HIDDEN-{index:02d}": secrets.token_hex(32) for index in range(1, 21)}
    seed_hashes = {key: hashlib.sha256(value.encode()).hexdigest() for key, value in seeds.items()}
    oracle = {"version": "1.0.0", "private_salt": secrets.token_hex(32), "case_count": 20}
    write_json(vault / "hidden_seeds.json", seeds)
    write_json(vault / "hidden_oracle_parameters.json", oracle)
    write_json(vault / "generated_case_hashes.json", seed_hashes)
    write_json(
        vault / "vault_manifest.json",
        {
            "schema_version": "1.0.0",
            "isolation_level": ISOLATION_LEVEL,
            "files": [
                "hidden_seeds.json",
                "hidden_oracle_parameters.json",
                "generated_case_hashes.json",
            ],
            "contains_private_material": True,
        },
    )
    return seed_hashes


def materialize_benchmark(root: Path, *, initialize_vault: bool) -> dict[str, Any]:
    if not initialize_vault:
        raise ValueError("INITIAL_VAULT_CREATION_REQUIRES_EXPLICIT_FLAG")
    seed_hashes = _write_vault(root)
    values = _tracked_values(root, seed_hashes)
    benchmark_root = root / BENCHMARK_ROOT
    benchmark_root.mkdir(parents=True, exist_ok=True)
    (benchmark_root / "README.md").write_text(README, encoding="utf-8")
    for relative, value in values.items():
        write_json(benchmark_root / relative, value)
    return {
        "status": "PASS",
        "public_case_count": 16,
        "hidden_case_count": 20,
        "model_in_loop_case_count": 8,
        "manifest_hash": values[Path("sealed_manifest.json")]["manifest_hash"],
        "hidden_values_emitted": False,
    }


def refresh_tracked_benchmark(root: Path) -> dict[str, Any]:
    """Refresh public artifacts from their sealed seed hashes without opening the vault."""
    sealed_path = root / BENCHMARK_ROOT / "sealed_manifest.json"
    if not sealed_path.is_file():
        raise ValueError("SEALED_MANIFEST_REQUIRED_FOR_SAFE_REFRESH")
    seed_hashes = read_json(sealed_path)["hidden_seed_hashes"]
    values = _tracked_values(root, seed_hashes)
    benchmark_root = root / BENCHMARK_ROOT
    (benchmark_root / "README.md").write_text(README, encoding="utf-8")
    for relative, value in values.items():
        write_json(benchmark_root / relative, value)
    return {
        "status": "PASS",
        "public_case_count": 16,
        "hidden_case_count": 20,
        "model_in_loop_case_count": 8,
        "manifest_hash": values[Path("sealed_manifest.json")]["manifest_hash"],
        "hidden_values_emitted": False,
        "private_values_read": False,
    }


__all__ = [
    "BENCHMARK_ROOT",
    "ISOLATION_LEVEL",
    "README",
    "TRANSFORMATIONS",
    "VAULT_ROOT",
    "apply_metamorphic",
    "generate_case",
    "materialize_benchmark",
    "refresh_tracked_benchmark",
]
