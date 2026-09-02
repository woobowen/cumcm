"""Offline deterministic replay for Phase 002D-R2 automated decisions."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from cumcm_skill_lab.adjudication.models import (
    check_or_write,
    file_sha256,
    read_json,
    sha256_json,
)

from .adjudication import DECISION_FILES, DECISION_ROOT, build_decisions
from .benchmark_generator import BENCHMARK_ROOT, COHORT_ID, SEALED_CASE_COUNT
from .models import CREATED_AT, RESULT_ROOT
from .vault_manifest import check_benchmark_vault

REPLAY_PATH = RESULT_ROOT / "replay/replay.json"
REPLAY_ID = "PHASE-002D-R2-AUTOMATED-DECISION-REPLAY-001"


def _recorded(root: Path) -> list[dict[str, Any]]:
    return [
        read_json(root / DECISION_ROOT / DECISION_FILES[decision_id])
        for decision_id in sorted(DECISION_FILES)
    ]


def _projection(envelope: dict[str, Any]) -> dict[str, Any]:
    core = envelope["automated_decision"]
    return {
        "decision_id": core["decision_id"],
        "decision": core["decision"],
        "core_scope": core["accepted_scope"],
        "phase_scope": envelope["phase_scope"],
        "hard_gate_status": core["hard_gate_status"],
        "evidence_sufficiency": core["evidence_sufficiency"],
        "next_phase_allowed": core["next_phase_allowed"],
        "reason_codes": sorted(core["reason_codes"]),
        "rejected_scope": sorted(core["rejected_scope"]),
        "retest_requirements": sorted(core["retest_requirements"]),
        "target_count": len(core["target_ids"]),
        "majority_vote_used": envelope["majority_vote_used"],
        "human_technical_gate_used": envelope["human_technical_gate_used"],
        "architecture_selected": envelope["architecture_selected"],
        "prototype_executed": envelope["prototype_executed"],
    }


def _canonical_projection(values: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        item["automated_decision"]["decision_id"]: _projection(item)
        for item in sorted(values, key=lambda value: value["automated_decision"]["decision_id"])
    }


def _reverse_evidence(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mutated = deepcopy(values)
    for envelope in mutated:
        core = envelope["automated_decision"]
        for field in (
            "eligible_evidence",
            "excluded_evidence",
            "dissent_findings",
            "tests",
        ):
            core[field] = list(reversed(core[field]))
    return mutated


def _seed_manifest_verification(root: Path) -> dict[str, Any]:
    sealed_path = root / BENCHMARK_ROOT / "sealed_manifest.json"
    sealed = read_json(sealed_path)
    body = dict(sealed)
    recorded_hash = body.pop("manifest_hash", None)
    vault = check_benchmark_vault(root)
    checks = {
        "canonical_manifest_hash_valid": sha256_json(body) == recorded_hash,
        "cohort_id_matches": sealed.get("cohort_id") == COHORT_ID,
        "seed_commitment_count_matches": (
            len(sealed.get("hidden_seed_hashes", {})) == SEALED_CASE_COUNT
        ),
        "private_oracle_commitment_present": len(sealed.get("private_oracle_commitment", "")) == 64,
        "vault_ignored_and_untracked": vault["status"] == "PASS",
        "private_values_read": vault["private_values_read"],
    }
    return {
        "checks": checks,
        "stable": all(value for key, value in checks.items() if key != "private_values_read")
        and checks["private_values_read"] is False,
        "sealed_manifest_file_hash": file_sha256(sealed_path),
        "sealed_manifest_hash": sealed.get("manifest_hash"),
    }


def build_replay(root: Path) -> dict[str, Any]:
    rebuilt = build_decisions(root)
    recorded = _recorded(root)
    expected = _canonical_projection(recorded)
    rebuilt_projection = _canonical_projection(rebuilt)
    reversed_projection = _canonical_projection(list(reversed(rebuilt)))
    evidence_projection = _canonical_projection(_reverse_evidence(rebuilt))
    labels = {
        target: f"opaque-target-{index:02d}"
        for index, target in enumerate(
            sorted(
                {
                    target
                    for envelope in rebuilt
                    for target in envelope["automated_decision"]["target_ids"]
                }
            ),
            start=1,
        )
    }
    label_projection = {
        decision_id: {
            **value,
            "opaque_target_labels": sorted(
                labels[target]
                for envelope in rebuilt
                if envelope["automated_decision"]["decision_id"] == decision_id
                for target in envelope["automated_decision"]["target_ids"]
            ),
        }
        for decision_id, value in rebuilt_projection.items()
    }
    label_stable = all(
        {key: item for key, item in value.items() if key != "opaque_target_labels"}
        == rebuilt_projection[decision_id]
        for decision_id, value in label_projection.items()
    )
    seed = _seed_manifest_verification(root)
    variants = {
        "original_rebuild": rebuilt_projection == expected,
        "decision_order_permutation": reversed_projection == expected,
        "evidence_order_permutation": evidence_projection == expected,
        "target_label_permutation": label_stable,
        "seed_manifest_verification": seed["stable"],
    }
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "replay_id": REPLAY_ID,
        "decision_ids": sorted(DECISION_FILES),
        "recorded_decision_hashes": {
            item["automated_decision"]["decision_id"]: item["decision_hash"] for item in recorded
        },
        "projection": expected,
        "variants": variants,
        "target_label_map_hash": sha256_json(labels),
        "seed_manifest": seed,
        "stable": all(variants.values()),
        "offline": True,
        "network_calls": 0,
        "model_calls": 0,
        "api_calls": 0,
        "prototype_executions": 0,
        "third_party_executions": 0,
        "created_at": CREATED_AT,
    }
    return {**body, "replay_hash": sha256_json(body)}


def validate_replay(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    body = dict(value)
    replay_hash = body.pop("replay_hash", None)
    if sha256_json(body) != replay_hash:
        errors.append("PHASE002D_R2_REPLAY_HASH_MISMATCH")
    if value.get("stable") is not True or not all(value.get("variants", {}).values()):
        errors.append("PHASE002D_R2_REPLAY_UNSTABLE")
    if any(
        value.get(field) != 0
        for field in (
            "network_calls",
            "model_calls",
            "api_calls",
            "prototype_executions",
            "third_party_executions",
        )
    ):
        errors.append("PHASE002D_R2_REPLAY_EXECUTION_BOUNDARY_VIOLATION")
    private_read = value.get("seed_manifest", {}).get("checks", {}).get("private_values_read")
    if private_read is not False:
        errors.append("PHASE002D_R2_REPLAY_PRIVATE_VAULT_READ")
    return errors


def check_or_write_replay(root: Path, *, check: bool) -> dict[str, Any]:
    value = build_replay(root)
    errors = validate_replay(value)
    errors.extend(check_or_write(root / REPLAY_PATH, value, check=check))
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "replay_id": value["replay_id"],
        "stable": value["stable"],
        "variants": value["variants"],
        "replay_hash": value["replay_hash"],
    }


__all__ = [
    "REPLAY_ID",
    "REPLAY_PATH",
    "build_replay",
    "check_or_write_replay",
    "validate_replay",
]
