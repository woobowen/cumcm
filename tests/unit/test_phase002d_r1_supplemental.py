from jsonschema import Draft202012Validator

from cumcm_skill_lab.failure_aware.models import read_json
from cumcm_skill_lab.failure_aware.supplemental import (
    build_authorization,
    build_budget,
    build_protocol_fingerprint,
    harness_semantic_equivalence,
    protocol_compatibility,
)


def test_current_matrix_authorizes_zero_slots(repo_root):
    authorization = build_authorization(repo_root)
    assert authorization["authorized_slot_ids"] == []
    assert authorization["decision"] == "AUTOMATED_REJECTED"
    assert authorization["target"] == "SUPPLEMENTAL_GENERIC_RUNS"
    assert authorization["maximum_real_starts"] == 0


def test_harness_slot_is_locked_without_semantic_equivalence(repo_root):
    equivalence = harness_semantic_equivalence(repo_root)
    assert equivalence["status"] == "NOT_ESTABLISHED"
    assert equivalence["bound_file_hashes"] == []
    assert equivalence["supplemental_eligible"] is False


def test_zero_budget_does_not_mutate_original_budget(repo_root):
    authorization = build_authorization(repo_root)
    budget = build_budget(authorization)
    assert budget["status"] == "NOT_AUTHORIZED"
    assert budget["maximum_total_starts"] == 0
    assert budget["source_budget_mutated"] is False


def test_supplemental_budget_is_capped_at_four_and_two_per_slot(repo_root):
    authorization = build_authorization(repo_root)
    authorization["authorized_slot_ids"] = ["SLOT-1", "SLOT-2", "SLOT-3"]
    authorization["maximum_real_starts"] = min(4, len(authorization["authorized_slot_ids"]) * 2)
    authorization["maximum_starts_per_slot"] = 2
    budget = build_budget(authorization)
    assert budget["maximum_total_starts"] == 4
    assert budget["maximum_starts_per_slot"] == 2
    assert budget["concurrency"] == 1


def test_protocol_exact_match_can_pool(repo_root):
    frozen = build_protocol_fingerprint(repo_root)
    assert protocol_compatibility(frozen, dict(frozen)) == {
        "result": "PASS",
        "drift_fields": [],
        "pool_with_current_evidence": True,
    }


def test_supplemental_contracts_accept_generated_records(repo_root):
    authorization = build_authorization(repo_root)
    budget = build_budget(authorization)
    for contract, value in (
        ("contracts/supplemental_run_authorization.schema.json", authorization),
        ("contracts/supplemental_budget.schema.json", budget),
    ):
        Draft202012Validator(read_json(repo_root / contract)).validate(value)
