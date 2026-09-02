import copy
import json
import subprocess
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.models import sha256_json
from cumcm_skill_lab.specification import vault_manifest
from cumcm_skill_lab.specification.benchmark_generator import (
    BENCHMARK_ROOT,
    TRANSFORMATIONS,
    VAULT_ROOT,
    apply_metamorphic,
    generate_case,
)
from cumcm_skill_lab.specification.benchmark_integrity import validate_prospective_benchmark
from cumcm_skill_lab.specification.vault_manifest import check_benchmark_vault


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_prospective_benchmark_integrity_passes(repo_root):
    result = validate_prospective_benchmark(repo_root)
    assert result["status"] == "PASS"
    assert result["historical_answers_used"] is False
    assert result["prototype_runs"] == 0


def test_generator_same_seed_is_stable():
    assert generate_case(101, "R2-TARGET-1") == generate_case(101, "R2-TARGET-1")


def test_generator_seed_change_changes_case():
    assert generate_case(101, "R2-TARGET-1") != generate_case(102, "R2-TARGET-1")


@pytest.mark.parametrize("transformation", TRANSFORMATIONS)
def test_all_metamorphic_transformations_are_supported(transformation):
    case = generate_case(7, "R2-TARGET-1")
    transformed = apply_metamorphic(case, transformation)
    assert transformed["family_id"] == case["family_id"]
    assert transformed != case


@pytest.mark.parametrize(
    "transformation",
    ["row_permutation", "file_order_permutation", "evidence_order_permutation"],
)
def test_order_permutations_preserve_members(transformation):
    case = generate_case(7, "R2-TARGET-1")
    transformed = apply_metamorphic(case, transformation)
    assert {row["entity"] for row in transformed["rows"]} == {row["entity"] for row in case["rows"]}
    assert set(transformed["evidence_order"]) == set(case["evidence_order"])


def test_unit_conversion_preserves_normalized_values():
    case = generate_case(7, "R2-TARGET-1")
    converted = apply_metamorphic(case, "unit_conversion")
    assert [row["measure"] for row in case["rows"]] == [
        row["measure"] // 100 for row in converted["rows"]
    ]


def test_public_and_hidden_separation(repo_root):
    root = repo_root / BENCHMARK_ROOT
    text = " ".join(
        path.read_text(encoding="utf-8") for path in root.rglob("*") if path.is_file()
    ).lower()
    assert "private_salt" not in text
    assert "token_hex" not in text
    assert not (root / "hidden_seeds.json").exists()
    assert not (root / "hidden_oracle_parameters.json").exists()


def test_vault_is_ignored_untracked_and_not_read(repo_root):
    result = check_benchmark_vault(repo_root)
    assert result["status"] == "PASS"
    assert result["private_values_read"] is False
    tracked = subprocess.run(
        ["git", "ls-files", VAULT_ROOT.as_posix()],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    assert tracked.stdout == ""


def test_clean_checkout_without_vault_mount_uses_public_commitment(repo_root, monkeypatch):
    monkeypatch.setattr(
        vault_manifest,
        "VAULT_ROOT",
        Path("benchmark-vault/fresh-checkout-vault-not-mounted"),
    )
    result = vault_manifest.check_benchmark_vault(repo_root)
    assert result["status"] == "PASS"
    assert result["mount_status"] == "NOT_MOUNTED"
    assert result["public_commitment_verified"] is True
    assert result["private_values_read"] is False


def test_hidden_seed_and_oracle_paths_are_git_ignored(repo_root):
    for name in ("hidden_seeds.json", "hidden_oracle_parameters.json"):
        result = subprocess.run(
            ["git", "check-ignore", (VAULT_ROOT / name).as_posix()],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


def test_sealed_manifest_hash_is_stable(repo_root):
    sealed = _json(repo_root / BENCHMARK_ROOT / "sealed_manifest.json")
    body = dict(sealed)
    recorded = body.pop("manifest_hash")
    assert sha256_json(body) == recorded
    assert sealed["contains_hidden_seed"] is False
    assert sealed["contains_hidden_oracle"] is False


def test_public_case_count_and_component_balance(repo_root):
    public = _json(repo_root / BENCHMARK_ROOT / "public_conformance/cases.json")
    assert public["case_count"] == 16
    counts = {}
    for case in public["cases"]:
        counts[case["component_id"]] = counts.get(case["component_id"], 0) + 1
    assert set(counts.values()) == {4}


@pytest.mark.parametrize(
    ("category", "expected"),
    [
        ("TARGETED", 4),
        ("INTERACTION", 4),
        ("VALID_NEGATIVE_CONTROL", 4),
        ("ADVERSARIAL_GAMING", 4),
        ("COMPOSITE", 4),
    ],
)
def test_required_family_categories_are_present(repo_root, category, expected):
    families = _yaml(repo_root / BENCHMARK_ROOT / "case_catalog.yaml")["families"]
    assert len([item for item in families if item["category"] == category]) == expected


def test_targeted_hidden_case_count_is_two_per_component(repo_root):
    families = _yaml(repo_root / BENCHMARK_ROOT / "case_catalog.yaml")["families"]
    targeted = [item for item in families if item["category"] == "TARGETED"]
    assert len(targeted) == 4
    assert all(item["case_count"] == 2 for item in targeted)


@pytest.mark.parametrize(
    "forbidden",
    [
        "historical answer content",
        "arch-s0-retain",
        "arch-w1-workflow",
        "arch-k1-thin",
        "src/cumcm_skill_lab/components",
    ],
)
def test_tracked_benchmark_has_no_historical_or_implementation_hint(repo_root, forbidden):
    implementation_blind_paths = (
        "case_catalog.yaml",
        "public_conformance/cases.json",
        "generators/generator_registry.yaml",
        "metamorphic_properties/properties.yaml",
        "negative_controls/catalog.yaml",
        "interaction_cases/catalog.yaml",
    )
    text = " ".join(
        (repo_root / BENCHMARK_ROOT / relative).read_text(encoding="utf-8")
        for relative in implementation_blind_paths
    ).lower()
    assert forbidden not in text


def test_case_family_schema_fails_closed_on_private_seed(repo_root):
    schema = _json(repo_root / "contracts/prospective_case_family.schema.json")
    family = copy.deepcopy(_yaml(repo_root / BENCHMARK_ROOT / "case_catalog.yaml")["families"][0])
    family["private_seed"] = 123
    assert list(Draft202012Validator(schema).iter_errors(family))


def test_model_in_loop_cases_are_frozen_but_not_executed(repo_root):
    value = _yaml(repo_root / BENCHMARK_ROOT / "model_in_loop/catalog.yaml")
    assert value["status"] == "FROZEN_FOR_FUTURE_EXECUTION"
    assert value["executed_in_phase_002d_r2"] is False
    assert value["repeats_per_family"] == 2
