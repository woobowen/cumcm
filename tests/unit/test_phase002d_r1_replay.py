from copy import deepcopy

import pytest

from cumcm_skill_lab.failure_aware.replay import (
    _read_inputs,
    build_replay,
    project_from_evidence,
    recorded_projection,
    replay_variants,
)


def test_replay_has_all_five_required_variants(repo_root):
    variants = replay_variants(_read_inputs(repo_root))
    assert set(variants) == {
        "ORIGINAL",
        "ATTEMPT_ORDER_PERMUTATION",
        "EVIDENCE_ITEM_ORDER_PERMUTATION",
        "ANONYMOUS_ARM_LABEL_PERMUTATION",
        "FAILURE_FLAG_ORDER_PERMUTATION",
    }


@pytest.mark.parametrize(
    "variant",
    [
        "ATTEMPT_ORDER_PERMUTATION",
        "EVIDENCE_ITEM_ORDER_PERMUTATION",
        "ANONYMOUS_ARM_LABEL_PERMUTATION",
        "FAILURE_FLAG_ORDER_PERMUTATION",
    ],
)
def test_replay_projection_is_order_and_label_stable(repo_root, variant):
    variants = replay_variants(_read_inputs(repo_root))
    assert variants[variant]["projection"] == variants["ORIGINAL"]["projection"]


def test_replay_projection_matches_seven_recorded_decisions(repo_root):
    projected = project_from_evidence(_read_inputs(repo_root))
    assert len(projected) == 7
    assert projected == recorded_projection(repo_root)


def test_replay_requires_one_canonical_accepted_scope(repo_root):
    projection = recorded_projection(repo_root)
    assert (
        projection["DECISION-RELIABILITY-EVIDENCE-SUFFICIENCY-002D-R1"]["accepted_scope"]
        == "RELIABILITY_ONLY"
    )


def test_replay_rejects_duplicate_attempt_identity(repo_root):
    inputs = _read_inputs(repo_root)
    inputs["classifications"].append(deepcopy(inputs["classifications"][0]))
    with pytest.raises(ValueError, match="REPLAY_DUPLICATE_ATTEMPT_ID"):
        project_from_evidence(inputs)


def test_replay_rejects_duplicate_slot_identity(repo_root):
    inputs = _read_inputs(repo_root)
    inputs["slots"].append(deepcopy(inputs["slots"][0]))
    with pytest.raises(ValueError, match="REPLAY_DUPLICATE_SLOT_ID"):
        project_from_evidence(inputs)


def test_replay_mutated_budget_changes_projection(repo_root):
    inputs = _read_inputs(repo_root)
    supplemental = next(
        item["value"] for item in inputs["evidence_items"] if item["kind"] == "supplemental"
    )
    supplemental["original_budget_mutated"] = True
    projected = project_from_evidence(inputs)
    assert projected["DECISION-SUPPLEMENTAL-RUN-AUTHORIZATION-002D-R1"]["decision"] == (
        "RETEST_REQUIRED"
    )


def test_replay_quality_and_reliability_remain_separate(repo_root):
    projected = project_from_evidence(_read_inputs(repo_root))
    quality = projected["DECISION-QUALITY-EVIDENCE-SUFFICIENCY-002D-R1"]
    reliability = projected["DECISION-RELIABILITY-EVIDENCE-SUFFICIENCY-002D-R1"]
    assert quality["decision"] == "EVIDENCE_INSUFFICIENT"
    assert reliability["decision"] == "AUTOMATED_ACCEPTED"
    assert reliability["accepted_scope"] == "RELIABILITY_ONLY"
    assert reliability["next_phase_allowed"] == "PHASE-EVIDENCE-EXPANSION-002D"
    assert reliability["positive_performance_superiority_claim_allowed"] is False
    assert reliability["quality_reliability_conflated"] is False


def test_replay_is_offline_stable_and_stays_in_phase_002d(repo_root):
    replay = build_replay(repo_root)
    assert replay["stable"] is True
    assert replay["variant_count"] == 5
    assert replay["mode"] == "OFFLINE_NO_MODEL_NO_NETWORK"
    assert replay["model_starts"] == 0
    assert replay["next_phase_allowed"] == "PHASE-EVIDENCE-EXPANSION-002D"
