"""Build and verify the immutable Phase 002D-R2A authorization input manifest."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from cumcm_skill_lab.adjudication.models import (
    check_or_write,
    file_sha256,
    read_json,
    sha256_json,
)
from cumcm_skill_lab.historical_compat import (
    competition_rc_successor,
    git_repository_file_hashes,
)

from .models import (
    CREATED_AT,
    FREEZE_ID,
    FREEZE_PATH,
    IMMUTABLE_ROOTS,
    OLD_AUTHORIZATION_ID,
    R2_ROOT,
    SUBJECT_COMMIT,
    git_file_sha256,
    git_tree_hash,
    repository_file_hashes,
    tree_hash,
)

PREREQUISITE_FILES = (
    "component_specification_freeze.json",
    "interaction_contract.json",
    "architecture_candidate_set.json",
    "prospective_benchmark_freeze.json",
    "threshold_policy_freeze.json",
)
OLD_AUTHORIZATION_PATH = R2_ROOT / "automated_decisions/shadow_prototype_authorization.json"
AUDIT_PATH = R2_ROOT / "decision_audit/audit.json"
REPLAY_PATH = R2_ROOT / "replay/replay.json"
EVIDENCE_PATH = R2_ROOT / "test_evidence/evidence.json"
FINDINGS_PATH = R2_ROOT / "adversarial_findings/findings.json"
FORMAL_SKILL_ROOT = Path(".agents/skills/cumcm-modeling-evidence")
PROVENANCE_PATH = Path("specifications/clean_room_provenance.yaml")
SUBAGENT_POLICY_PATH = Path("rules/phase002d_r2a_workflow_rules.yaml")


def _decision_bindings(root: Path) -> dict[str, dict[str, str]]:
    values: dict[str, dict[str, str]] = {}
    for name in PREREQUISITE_FILES:
        path = R2_ROOT / "automated_decisions" / name
        record = read_json(root / path)
        decision_id = record["automated_decision"]["decision_id"]
        values[decision_id] = {
            "path": path.as_posix(),
            "decision_hash": record["decision_hash"],
            "file_sha256": file_sha256(root / path),
        }
    return dict(sorted(values.items()))


def _serious_closure_hashes(root: Path) -> dict[str, str]:
    findings = read_json(root / FINDINGS_PATH)["findings"]
    evidence = read_json(root / EVIDENCE_PATH)["test_evidence"]
    evidence_by_finding = {item["finding_id"]: item for item in evidence}
    serious = [item for item in findings if item["severity"] in {"BLOCKER", "ERROR"}]
    return {
        item["finding_id"]: sha256_json(evidence_by_finding[item["finding_id"]])
        for item in sorted(serious, key=lambda value: value["finding_id"])
    }


def build_input_freeze(root: Path) -> dict[str, Any]:
    immutable = repository_file_hashes(root, IMMUTABLE_ROOTS)
    r2_freeze = read_json(root / R2_ROOT / "input_freeze_manifest.json")
    old_authorization = read_json(root / OLD_AUTHORIZATION_PATH)
    audit = read_json(root / AUDIT_PATH)
    replay = read_json(root / REPLAY_PATH)
    component_hashes = repository_file_hashes(root, (Path("specifications/components"),))
    interaction_hashes = repository_file_hashes(root, (Path("specifications/interactions"),))
    body: dict[str, Any] = {
        "schema_version": "1.0.0",
        "freeze_id": FREEZE_ID,
        "phase": "PHASE-EVIDENCE-EXPANSION-002D",
        "subphase": "PHASE-002D-R2A-SHADOW-PROTOTYPE-AUTHORIZATION-CLOSURE",
        "created_at": CREATED_AT,
        "subject_commit": SUBJECT_COMMIT,
        "r2_input_freeze_hash": r2_freeze["manifest_hash"],
        "accepted_prerequisite_decision_hashes": _decision_bindings(root),
        "old_shadow_authorization": {
            "decision_id": OLD_AUTHORIZATION_ID,
            "decision": old_authorization["automated_decision"]["decision"],
            "decision_hash": old_authorization["decision_hash"],
            "file_sha256": file_sha256(root / OLD_AUTHORIZATION_PATH),
            "path": OLD_AUTHORIZATION_PATH.as_posix(),
        },
        "r2_decision_audit": {
            "result": audit["result"],
            "checkpoint_hash": audit["checkpoint_hash"],
            "file_sha256": file_sha256(root / AUDIT_PATH),
        },
        "r2_replay": {
            "stable": replay["stable"],
            "replay_hash": replay["replay_hash"],
            "file_sha256": file_sha256(root / REPLAY_PATH),
        },
        "component_spec_hashes": component_hashes,
        "component_spec_tree_hash": tree_hash(component_hashes),
        "interaction_contract_hashes": interaction_hashes,
        "interaction_contract_tree_hash": tree_hash(interaction_hashes),
        "candidate_set_hash": file_sha256(
            root / "specifications/architectures/architecture_candidate_set.yaml"
        ),
        "benchmark_manifest_hash": file_sha256(
            root / "evals/prospective/phase-002d-r2/sealed_manifest.json"
        ),
        "threshold_policy_hash": file_sha256(
            root / "evals/prospective/phase-002d-r2/threshold_policy.yaml"
        ),
        "prospective_protocol_hash": file_sha256(
            root / "evals/prospective/phase-002d-r2/prospective_experiment_protocol.yaml"
        ),
        "implementation_embargo_hash": file_sha256(root / R2_ROOT / "implementation_embargo.json"),
        "clean_room_provenance_hash": file_sha256(root / PROVENANCE_PATH),
        "formal_skill_tree_hash": tree_hash(repository_file_hashes(root, (FORMAL_SKILL_ROOT,))),
        "src_tree_baseline_hash": git_tree_hash(root, SUBJECT_COMMIT, "src"),
        "src_tree_baseline_subject_commit": SUBJECT_COMMIT,
        "serious_finding_closure_hashes": _serious_closure_hashes(root),
        "subagent_policy_hash": file_sha256(root / SUBAGENT_POLICY_PATH),
        "immutable_file_count": len(immutable),
        "immutable_tree_hash": tree_hash(immutable),
        "immutable_file_hashes": immutable,
        "prototype_executions": 0,
        "third_party_executions": 0,
        "api_calls": 0,
        "real_batch_model_runs": 0,
        "hidden_values_read": False,
    }
    body["manifest_hash"] = sha256_json(body)
    return body


def verify_input_freeze(root: Path, manifest: dict[str, Any] | None = None) -> list[str]:
    if manifest is None:
        if not (root / FREEZE_PATH).is_file():
            return ["PHASE002D_R2A_INPUT_FREEZE_MISSING"]
        manifest = read_json(root / FREEZE_PATH)
    errors: list[str] = []
    body = dict(manifest)
    recorded_hash = body.pop("manifest_hash", None)
    if sha256_json(body) != recorded_hash:
        errors.append("PHASE002D_R2A_MANIFEST_HASH_MISMATCH")
    if manifest.get("subject_commit") != SUBJECT_COMMIT:
        errors.append("PHASE002D_R2A_SUBJECT_COMMIT_MISMATCH")
    immutable = repository_file_hashes(root, IMMUTABLE_ROOTS)
    if immutable != manifest.get("immutable_file_hashes"):
        errors.append("PHASE002D_R2A_IMMUTABLE_INPUT_MUTATED")
    if len(immutable) != manifest.get("immutable_file_count"):
        errors.append("PHASE002D_R2A_IMMUTABLE_FILE_COUNT_MISMATCH")
    if tree_hash(immutable) != manifest.get("immutable_tree_hash"):
        errors.append("PHASE002D_R2A_IMMUTABLE_TREE_HASH_MISMATCH")
    old = manifest.get("old_shadow_authorization", {})
    if old.get("decision_id") != OLD_AUTHORIZATION_ID:
        errors.append("PHASE002D_R2A_OLD_AUTHORIZATION_ID_MISMATCH")
    if not (root / OLD_AUTHORIZATION_PATH).is_file() or file_sha256(
        root / OLD_AUTHORIZATION_PATH
    ) != old.get("file_sha256"):
        errors.append("PHASE002D_R2A_OLD_AUTHORIZATION_BYTES_CHANGED")
    current_skill_hash = tree_hash(
        git_repository_file_hashes(root, (FORMAL_SKILL_ROOT,), commit=SUBJECT_COMMIT)
        if competition_rc_successor(root)
        else repository_file_hashes(root, (FORMAL_SKILL_ROOT,))
    )
    if current_skill_hash != manifest.get("formal_skill_tree_hash"):
        errors.append("PHASE002D_R2A_FORMAL_SKILL_HASH_CHANGED")
    if file_sha256(root / SUBAGENT_POLICY_PATH) != manifest.get("subagent_policy_hash"):
        errors.append("PHASE002D_R2A_SUBAGENT_POLICY_CHANGED")
    try:
        subject_old_hash = git_file_sha256(root, SUBJECT_COMMIT, OLD_AUTHORIZATION_PATH.as_posix())
    except subprocess.CalledProcessError:
        errors.append("PHASE002D_R2A_OLD_AUTHORIZATION_ABSENT_AT_SUBJECT")
    else:
        if subject_old_hash != old.get("file_sha256"):
            errors.append("PHASE002D_R2A_OLD_AUTHORIZATION_SUBJECT_MISMATCH")
    if len(manifest.get("accepted_prerequisite_decision_hashes", {})) != 5:
        errors.append("PHASE002D_R2A_PREREQUISITE_DECISION_COUNT_MISMATCH")
    if len(manifest.get("serious_finding_closure_hashes", {})) != 29:
        errors.append("PHASE002D_R2A_SERIOUS_CLOSURE_COUNT_MISMATCH")
    if any(
        manifest.get(field) != 0
        for field in (
            "prototype_executions",
            "third_party_executions",
            "api_calls",
            "real_batch_model_runs",
        )
    ):
        errors.append("PHASE002D_R2A_EXECUTION_BASELINE_NONZERO")
    return sorted(set(errors))


def check_or_write_input_freeze(root: Path, *, check: bool) -> dict[str, Any]:
    manifest = read_json(root / FREEZE_PATH) if check and (root / FREEZE_PATH).is_file() else None
    if check:
        errors = verify_input_freeze(root, manifest)
    else:
        manifest = build_input_freeze(root)
        errors = check_or_write(root / FREEZE_PATH, manifest, check=False)
        errors.extend(verify_input_freeze(root, manifest))
    return {
        "status": "PASS" if not errors else "INPUT_FREEZE_BROKEN",
        "errors": sorted(set(errors)),
        "freeze_id": manifest.get("freeze_id") if manifest else None,
        "manifest_hash": manifest.get("manifest_hash") if manifest else None,
        "file_count": manifest.get("immutable_file_count") if manifest else None,
        "subject_commit": manifest.get("subject_commit") if manifest else None,
    }
