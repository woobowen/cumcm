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
COHORT_ID = "R2-SEALED-COHORT-V2"
SEALED_CASE_COUNT = 36
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
        "generator_id": "GEN-SYNTHETIC-V2",
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
            _family(f"R2-TARGET-{index}", "SEALED_PROPERTY", [component_id], "TARGETED", 2)
        )
    for index in range(1, 5):
        values.extend(
            [
                _family(
                    f"R2-INTERACTION-{index}",
                    "SEALED_PROPERTY",
                    list(COMPONENT_IDS),
                    "INTERACTION",
                    1,
                ),
                _family(
                    f"R2-NEGATIVE-{index}",
                    "SEALED_PROPERTY",
                    [COMPONENT_IDS[index - 1]],
                    "VALID_NEGATIVE_CONTROL",
                    5,
                    negative=True,
                ),
                _family(
                    f"R2-GAMING-{index}",
                    "SEALED_PROPERTY",
                    [COMPONENT_IDS[index - 1]],
                    "ADVERSARIAL_GAMING",
                    1,
                    gaming=True,
                ),
                _family(
                    f"R2-MODEL-{index}",
                    "MODEL_IN_LOOP_FUTURE",
                    [COMPONENT_IDS[index - 1]],
                    "COMPOSITE",
                    2,
                ),
            ]
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


def _oracle_interfaces(families: list[dict[str, Any]]) -> dict[str, str]:
    return {
        name: hashlib.sha256(f"phase-002d-r2:{name}:schema-v1:semantics-v1".encode()).hexdigest()
        for name in sorted({item["oracle_interface"] for item in families})
    }


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
        "sealed_case_count": SEALED_CASE_COUNT,
        "model_in_loop_case_count": 8,
        "case_family_ids": [item["family_id"] for item in families],
        "metamorphic_transformations": list(TRANSFORMATIONS),
        "isolation_level": ISOLATION_LEVEL,
        "prototype_runs": 0,
    }
    return {**body, "benchmark_hash": sha256_json(body)}


def _tracked_values(
    root: Path,
    seed_hashes: dict[str, str],
    private_oracle_commitment: str,
    supersedes_manifest_hash: str,
) -> dict[Path, Any]:
    families = _families()
    public_cases = _public_cases()
    protocol = _benchmark_protocol(families)
    if len(seed_hashes) != SEALED_CASE_COUNT:
        raise ValueError("SEALED_CASE_SEED_CARDINALITY_MISMATCH")
    interfaces = _oracle_interfaces(families)
    applicability = [
        {
            "family_id": family["family_id"],
            "transformation": transformation,
            "applicable": True,
            "expected_relation": (
                "EQUIVARIANT_AFTER_UNIT_NORMALIZATION"
                if transformation == "unit_conversion"
                else "INVARIANT"
            ),
            "exclusion_reason": None,
        }
        for family in families
        if family["tier"] == "SEALED_PROPERTY"
        for transformation in TRANSFORMATIONS
    ]
    values: dict[Path, Any] = {
        Path("benchmark_protocol.yaml"): protocol,
        Path("case_catalog.yaml"): {
            "schema_version": "1.0.0",
            "audience": "AUDITOR_ONLY_NOT_CANDIDATE",
            "families": families,
        },
        Path("public_conformance/cases.json"): {"case_count": 16, "cases": public_cases},
        Path("generators/generator_registry.yaml"): {
            "generator_id": "GEN-SYNTHETIC-V2",
            "input": "integer seed and family ID",
            "deterministic": True,
            "architecture_names_present": False,
            "implementation_paths_present": False,
            "candidate_arms_present": False,
            "source_hash": file_sha256(Path(__file__)),
        },
        Path("metamorphic_properties/properties.yaml"): {
            "properties": list(TRANSFORMATIONS),
            "expected_relation": (
                "frozen per-family applicability matrix controls invariant/equivariant scoring"
            ),
            "composition_requirements": [
                "permutation_then_unit_conversion",
                "rename_then_extra_field",
                "at_least_one_noncommuting_order_pair_per_scope",
            ],
        },
        Path("metamorphic_properties/applicability_matrix.yaml"): {
            "schema_version": "1.0.0",
            "matrix": applicability,
            "base_variant_binding_required": [
                "opaque_case_id",
                "base_hash",
                "variant_hash",
                "expected_relation",
                "seed_commitment",
            ],
        },
        Path("negative_controls/catalog.yaml"): {
            "family_ids": [item["family_id"] for item in families if item["negative_control"]],
            "base_valid_control_count": 20,
            "minimum_paired_valid_control_denominator": 20,
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
        Path("manifests/oracle_commitments.json"): {
            "schema_version": "1.0.0",
            "cohort_id": COHORT_ID,
            "frozen_before_prototype": True,
            "candidate_results_present": False,
            "private_mapping_commitment": private_oracle_commitment,
            "oracle_class_counts": {"VALID_CONTROL": 20, "INVALID_CONTROL": 16},
            "per_case_metadata_exposed_to_candidate": [],
        },
        Path("manifests/oracle_interface_registry.json"): {
            "schema_version": "1.0.0",
            "interfaces": {
                name: {"schema_version": "1.0.0", "semantic_digest": digest}
                for name, digest in interfaces.items()
            },
        },
        Path("manifests/candidate_visible_manifest.json"): {
            "schema_version": "1.0.0",
            "cohort_commitment": private_oracle_commitment,
            "opaque_case_count": SEALED_CASE_COUNT,
            "payload_contract_hash": hashlib.sha256(b"opaque-case-payload-v2").hexdigest(),
            "exposed_fields": ["opaque_case_id", "payload"],
        },
        Path("manifests/separation_report.json"): {
            "schema_version": "1.0.0",
            "cohort_id": COHORT_ID,
            "generator_ancestry_checked": True,
            "seed_domain_separated": True,
            "exact_overlap_count": 0,
            "ancestry_overlap_count": 0,
            "semantic_template_overlap_count": 0,
            "transformation_closure_overlap_count": 0,
            "private_report_commitment": private_oracle_commitment,
        },
        Path("access_policy.yaml"): {
            "candidate_identity": "FUTURE-ISOLATED-CANDIDATE",
            "candidate_visible_manifest": "manifests/candidate_visible_manifest.json",
            "deny_prefixes": [
                "benchmark-vault/",
                "manifests/oracle_",
                "case_catalog.yaml",
                "sealed_manifest.json",
            ],
            "required_access_ledger": True,
            "missing_ledger_disposition": "INVALIDATE_COHORT",
            "any_denied_access_disposition": "INVALIDATE_COHORT",
            "os_enforcement_required_before_future_execution": True,
            "executed_in_phase_002d_r2": False,
        },
    }
    artifact_hashes = {path.as_posix(): sha256_json(value) for path, value in values.items()}
    family_hashes = {item["family_id"]: item["family_hash"] for item in families}
    generator_hash = values[Path("generators/generator_registry.yaml")]["source_hash"]
    manifest_body = {
        "schema_version": "1.0.0",
        "manifest_id": "PHASE-002D-R2-SEALED-BENCHMARK-001",
        "cohort_id": COHORT_ID,
        "supersedes_manifest_hash": supersedes_manifest_hash,
        "status": "BENCHMARK_FROZEN",
        "benchmark_hash": protocol["benchmark_hash"],
        "generator_hashes": {"GEN-SYNTHETIC-V2": generator_hash},
        "family_hashes": family_hashes,
        "public_artifact_hashes": artifact_hashes,
        "hidden_seed_hashes": seed_hashes,
        "private_oracle_commitment": private_oracle_commitment,
        "oracle_interface_hashes": interfaces,
        "hidden_case_count": SEALED_CASE_COUNT,
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
        "candidate_visible_artifacts": ["manifests/candidate_visible_manifest.json"],
    }
    values[Path("sealed_manifest.json")] = sealed
    return values


README = """# Phase 002D-R2 Prospective Benchmark

This is a synthetic, prospective Benchmark frozen before prototype implementation. Public cases
provide conformance feedback, not generalization evidence. The first sealed cohort is permanently
rejected because tracked metadata exposed its case classes. Cohort V2 uses opaque candidate inputs;
exact seeds, mapping and oracle parameters remain in the ignored vault. OS-level denial plus an
access ledger is a mandatory future-execution precondition. No prototype or model run occurs here.
"""


def _ignored(root: Path, relative: Path) -> bool:
    check = subprocess.run(
        ["git", "check-ignore", relative.as_posix()],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    return check.returncode == 0


def _write_vault(root: Path, *, suffix: str, case_count: int) -> tuple[dict[str, str], str]:
    vault = root / VAULT_ROOT
    names = {
        "seeds": f"hidden_seeds{suffix}.json",
        "oracle": f"hidden_oracle_parameters{suffix}.json",
        "mapping": f"oracle_class_map{suffix}.json",
        "hashes": f"generated_case_hashes{suffix}.json",
        "manifest": f"vault_manifest{suffix}.json",
    }
    for name in names.values():
        relative = VAULT_ROOT / name
        if (root / relative).exists():
            raise ValueError(f"VAULT_COHORT_ALREADY_EXISTS_REFUSE_OVERWRITE:{name}")
        if not _ignored(root, relative):
            raise ValueError(f"VAULT_NOT_ISOLATED:{name}")
    seeds = {
        f"OPAQUE-SLOT-{index:02d}": secrets.token_hex(32) for index in range(1, case_count + 1)
    }
    seed_hashes = {
        key: hashlib.sha256(f"phase-002d-r2:v2:seed:{value}".encode()).hexdigest()
        for key, value in seeds.items()
    }
    private_map = {
        "version": "2.0.0",
        "cohort_id": COHORT_ID,
        "records": [
            {
                "opaque_slot": key,
                "oracle_class": "VALID_CONTROL" if index <= 20 else "INVALID_CONTROL",
                "private_family_slot": index,
            }
            for index, key in enumerate(sorted(seeds), start=1)
        ],
    }
    private_oracle_commitment = sha256_json(private_map)
    oracle = {
        "version": "2.0.0",
        "private_salt": secrets.token_hex(32),
        "case_count": case_count,
        "mapping_commitment": private_oracle_commitment,
    }
    write_json(vault / names["seeds"], seeds)
    write_json(vault / names["oracle"], oracle)
    write_json(vault / names["mapping"], private_map)
    write_json(vault / names["hashes"], seed_hashes)
    write_json(
        vault / names["manifest"],
        {
            "schema_version": "2.0.0",
            "cohort_id": COHORT_ID,
            "isolation_level": ISOLATION_LEVEL,
            "files": list(names.values())[:-1],
            "contains_private_material": True,
        },
    )
    return seed_hashes, private_oracle_commitment


def materialize_benchmark(root: Path, *, initialize_vault: bool) -> dict[str, Any]:
    if not initialize_vault:
        raise ValueError("INITIAL_VAULT_CREATION_REQUIRES_EXPLICIT_FLAG")
    seed_hashes, commitment = _write_vault(root, suffix="", case_count=SEALED_CASE_COUNT)
    values = _tracked_values(root, seed_hashes, commitment, "0" * 64)
    benchmark_root = root / BENCHMARK_ROOT
    benchmark_root.mkdir(parents=True, exist_ok=True)
    (benchmark_root / "README.md").write_text(README, encoding="utf-8")
    for relative, value in values.items():
        write_json(benchmark_root / relative, value)
    return {
        "status": "PASS",
        "public_case_count": 16,
        "hidden_case_count": SEALED_CASE_COUNT,
        "model_in_loop_case_count": 8,
        "manifest_hash": values[Path("sealed_manifest.json")]["manifest_hash"],
        "hidden_values_emitted": False,
    }


def rotate_benchmark_vault(root: Path) -> dict[str, Any]:
    """Create a new private cohort without opening the rejected cohort."""
    old = read_json(root / BENCHMARK_ROOT / "sealed_manifest.json")
    seed_hashes, commitment = _write_vault(root, suffix="_v2", case_count=SEALED_CASE_COUNT)
    values = _tracked_values(root, seed_hashes, commitment, old["manifest_hash"])
    benchmark_root = root / BENCHMARK_ROOT
    (benchmark_root / "README.md").write_text(README, encoding="utf-8")
    for relative, value in values.items():
        write_json(benchmark_root / relative, value)
    return {
        "status": "PASS",
        "cohort_id": COHORT_ID,
        "hidden_case_count": SEALED_CASE_COUNT,
        "supersedes_manifest_hash": old["manifest_hash"],
        "manifest_hash": values[Path("sealed_manifest.json")]["manifest_hash"],
        "hidden_values_emitted": False,
        "superseded_private_values_read": False,
    }


def refresh_tracked_benchmark(root: Path) -> dict[str, Any]:
    sealed = read_json(root / BENCHMARK_ROOT / "sealed_manifest.json")
    if sealed.get("cohort_id") != COHORT_ID:
        raise ValueError("REJECTED_COHORT_CANNOT_BE_REFRESHED;USE_ROTATE_VAULT")
    values = _tracked_values(
        root,
        sealed["hidden_seed_hashes"],
        sealed["private_oracle_commitment"],
        sealed["supersedes_manifest_hash"],
    )
    benchmark_root = root / BENCHMARK_ROOT
    (benchmark_root / "README.md").write_text(README, encoding="utf-8")
    for relative, value in values.items():
        write_json(benchmark_root / relative, value)
    return {
        "status": "PASS",
        "cohort_id": COHORT_ID,
        "public_case_count": 16,
        "hidden_case_count": SEALED_CASE_COUNT,
        "model_in_loop_case_count": 8,
        "manifest_hash": values[Path("sealed_manifest.json")]["manifest_hash"],
        "hidden_values_emitted": False,
        "private_values_read": False,
    }


__all__ = [
    "BENCHMARK_ROOT",
    "COHORT_ID",
    "ISOLATION_LEVEL",
    "README",
    "SEALED_CASE_COUNT",
    "TRANSFORMATIONS",
    "VAULT_ROOT",
    "apply_metamorphic",
    "generate_case",
    "materialize_benchmark",
    "refresh_tracked_benchmark",
    "rotate_benchmark_vault",
]
