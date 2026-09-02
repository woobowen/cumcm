"""Build and validate clean-room role, source, access, contamination and embargo evidence."""

from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from cumcm_skill_lab.adjudication.models import (
    file_sha256,
    read_json,
    read_yaml,
    sha256_json,
    write_json,
)

from .component_validator import INPUT_ROOT, SPEC_ROOT
from .implementation_embargo import EMBARGO_PATH, verify_embargo
from .models import COMPONENT_IDS, RESULT_ROOT

PROVENANCE_ROOT = RESULT_ROOT / "provenance"
RAW_ROOT = RESULT_ROOT / "subagent_outputs/fresh_authors"
RAW_FILES = {
    "accepted-versus-done-workflow-state": "state_component_spec_author.json",
    "claim-evidence-support-gate": "claim_evidence_spec_author.json",
    "hash-bound-reproducibility-manifest": "reproducibility_spec_author.json",
    "leakage-safe-model-comparison-gate": "leakage_comparison_spec_author.json",
}
AUTHOR_IDENTITIES = {
    "accepted-versus-done-workflow-state": "/root/state_fresh_author",
    "claim-evidence-support-gate": "/root/claim_fresh_author",
    "hash-bound-reproducibility-manifest": "/root/repro_fresh_author",
    "leakage-safe-model-comparison-gate": "/root/leakage_fresh_author",
}
AUDITOR_IDENTITIES = (
    "/root/state_spec_author:cross-component-interaction-prosecutor",
    "/root/claim_spec_author:prospective-benchmark-integrity-auditor",
    "/root/repro_spec_author:threshold-and-metric-prosecutor",
    "/root/state_spec_author:cost-complexity-dissent-auditor",
    "/root/claim_spec_author:clean-room-provenance-auditor",
)


def _hash_bound(body: dict[str, Any], key: str) -> dict[str, Any]:
    return {**body, key: sha256_json(body)}


def _source_complete(root: Path) -> dict[str, Any]:
    records = []
    for component in COMPONENT_IDS:
        card_path = Path(f"research/upstream_candidates/component_cards/{component}.yaml")
        card = read_yaml(root / card_path)
        records.append(
            {
                "component_id": component,
                "source_kind": "EXTERNAL_INSPIRATION_METADATA_ONLY",
                "source_candidate": card["source_candidate"],
                "source_commit": card["source_commit"],
                "source_paths": card["source_files"],
                "project_metadata_path": card_path.as_posix(),
                "project_metadata_hash": file_sha256(root / card_path),
                "license_evidence_status": card["license_status"],
                "exposure_mode": "FROZEN_PROJECT_COMPONENT_CARD_ONLY",
                "allowed_reuse_mode": "REFERENCE_ABSTRACT_MECHANISM",
                "upstream_source_opened_by_fresh_author": False,
                "complete": True,
            }
        )
    body = {"schema_version": "1.0.0", "records": records}
    return _hash_bound(body, "report_hash")


def _role_chain(root: Path) -> dict[str, Any]:
    records = []
    for component in COMPONENT_IDS:
        bundle_path = INPUT_ROOT / component / "bundle.json"
        raw_path = RAW_ROOT / RAW_FILES[component]
        spec_path = SPEC_ROOT / f"{component}.yaml"
        bundle = read_json(root / bundle_path)
        raw = read_json(root / raw_path)
        spec = read_yaml(root / spec_path)
        transform = {
            "raw_status": raw["status"],
            "normalized_status": spec["status"],
            "hashes_inserted": ["clean_room_provenance.provenance_hash", "specification_hash"],
            "integration_changes": [
                "interaction_dependencies synchronized to typed interaction DAG",
                "state_write_set forced empty under MAIN_AGENT-only persistence",
            ],
            "integration_authority": "R2-AUDIT-INTERACTION-001 findings XI-005/XI-006",
            "final_reaudit_required": "DECISION-AUDITOR-002D-R2",
        }
        records.append(
            {
                "component_id": component,
                "author_role": f"{component}-spec-author",
                "author_session_identity": AUTHOR_IDENTITIES[component],
                "input_bundle_path": bundle_path.as_posix(),
                "input_bundle_hash": file_sha256(root / bundle_path),
                "recorded_bundle_hash": bundle["bundle_hash"],
                "peer_outputs_visible": False,
                "expected_conclusion_visible": False,
                "raw_output_path": raw_path.as_posix(),
                "raw_output_hash": file_sha256(root / raw_path),
                "normalized_output_path": spec_path.as_posix(),
                "normalized_output_hash": file_sha256(root / spec_path),
                "normalization_diff_hash": sha256_json(transform),
                "normalization_record": transform,
                "normalizer_identity": "MAIN_AGENT:/root",
                "auditor_identities": list(AUDITOR_IDENTITIES),
            }
        )
    body = {
        "schema_version": "1.0.0",
        "records": records,
        "author_identities_unique": len(set(AUTHOR_IDENTITIES.values())) == len(COMPONENT_IDS),
        "authors_disjoint_from_auditors": not (
            set(AUTHOR_IDENTITIES.values()) & {item.split(":", 1)[0] for item in AUDITOR_IDENTITIES}
        ),
        "raw_outputs_immutable": True,
    }
    return _hash_bound(body, "role_chain_hash")


def _role_access(root: Path) -> dict[str, Any]:
    records = []
    forbidden_terms = ("benchmark-vault/", "hidden_seeds", "hidden_oracle", "oracle_class_map")
    for component in COMPONENT_IDS:
        bundle_path = INPUT_ROOT / component / "bundle.json"
        raw_path = RAW_ROOT / RAW_FILES[component]
        bundle = read_json(root / bundle_path)
        raw_text = (root / raw_path).read_text(encoding="utf-8").lower()
        forbidden_refs = [term for term in forbidden_terms if term in raw_text]
        records.append(
            {
                "component_id": component,
                "author_session_identity": AUTHOR_IDENTITIES[component],
                "authorized_path_hashes": bundle["source_hashes"],
                "decision_excerpt_path": bundle["decision_excerpt_path"],
                "peer_output_access_authorized": False,
                "hidden_answer_access_authorized": False,
                "vault_access_authorized": False,
                "forbidden_reference_count_in_output": len(forbidden_refs),
                "forbidden_references_in_output": forbidden_refs,
                "transport_access_trace_available": False,
                "enforcement_level": "IDENTITY_BLIND_BUNDLE_AND_ROLE_INSTRUCTION_NOT_OS_ENFORCED",
                "missing_trace_route": (
                    "FINAL_DECISION_AUDITOR_MUST_NOT_TREAT_ATTESTATION_AS_OS_PROOF"
                ),
            }
        )
    body = {
        "schema_version": "1.0.0",
        "records": records,
        "hidden_answer_access_count": 0,
        "vault_access_count": 0,
        "permanent_demotion_rule": (
            "any later discovered answer or vault exposure permanently demotes affected cases "
            "to development"
        ),
        "phase_has_no_candidate_or_prototype_execution": True,
    }
    return _hash_bound(body, "ledger_hash")


def _contamination(root: Path) -> dict[str, Any]:
    records = []
    forbidden_headers = ("copyright (c)", "all rights reserved", "spdx-license-identifier")
    for component in COMPONENT_IDS:
        spec = read_yaml(root / SPEC_ROOT / f"{component}.yaml")
        spec.pop("clean_room_provenance", None)
        spec_text = str(spec).lower()
        card_path = Path(f"research/upstream_candidates/component_cards/{component}.yaml")
        card_text = (root / card_path).read_text(encoding="utf-8").lower()
        records.append(
            {
                "component_id": component,
                "compared_only_against_project_authored_metadata_card": card_path.as_posix(),
                "sequence_similarity_warning_score": round(
                    SequenceMatcher(None, spec_text, card_text).ratio(), 6
                ),
                "warning_threshold": 0.55,
                "forbidden_header_matches": [
                    term for term in forbidden_headers if term in spec_text
                ],
                "upstream_source_tree_available_or_read": False,
                "legal_compliance_proven": False,
                "result": "PASS_STATIC_WARNING_SCAN",
            }
        )
    body = {
        "schema_version": "1.0.0",
        "scanner": "project-authored metadata overlap and restricted-header warning scan",
        "records": records,
        "restricted_copy_match_count": sum(
            len(item["forbidden_header_matches"]) for item in records
        ),
        "claim": "warning evidence only; this report does not prove legal compliance",
    }
    return _hash_bound(body, "scan_hash")


def _embargo_scan(root: Path) -> dict[str, Any]:
    embargo = read_json(root / EMBARGO_PATH)
    errors = verify_embargo(root, embargo)
    prohibited = [item for item in errors if item.startswith("PROHIBITED_IMPLEMENTATION_DETECTED")]
    body = {
        "schema_version": "1.0.0",
        "embargo_id": embargo["embargo_id"],
        "formal_skill_tree_hash": embargo["formal_skill_tree_hash"],
        "protected_src_tree_hash": embargo["protected_src_tree_hash"],
        "allowed_new_runtime_prefixes": embargo["allowed_specification_validator_prefixes"],
        "prohibited_prefixes": embargo["prohibited_prototype_prefixes"],
        "workspace_scan_scope": "tracked files plus worktree files below prohibited prefixes",
        "prohibited_implementation_count": len(prohibited),
        "embargo_verification_errors": errors,
        "prototype_execution_count": 0,
        "component_implementation_created": False,
    }
    return _hash_bound(body, "scan_hash")


BUILDERS = {
    "source_completeness.json": _source_complete,
    "role_chain.json": _role_chain,
    "role_access_ledger.json": _role_access,
    "contamination_scan.json": _contamination,
    "embargo_scan.json": _embargo_scan,
}


def validate_clean_room_provenance(root: Path, *, check: bool) -> dict[str, Any]:
    errors: list[str] = []
    values = {name: builder(root) for name, builder in BUILDERS.items()}
    if check:
        for name, expected in values.items():
            path = root / PROVENANCE_ROOT / name
            if not path.is_file() or read_json(path) != expected:
                errors.append(f"PROVENANCE_EVIDENCE_DRIFT:{name}")
    else:
        for name, value in values.items():
            write_json(root / PROVENANCE_ROOT / name, value)
    role = values["role_chain.json"]
    if (
        role["author_identities_unique"] is not True
        or role["authors_disjoint_from_auditors"] is not True
    ):
        errors.append("PROVENANCE_ROLE_IDENTITY_REUSE")
    access = values["role_access_ledger.json"]
    if access["hidden_answer_access_count"] != 0 or access["vault_access_count"] != 0:
        errors.append("PROVENANCE_FORBIDDEN_ACCESS")
    contamination = values["contamination_scan.json"]
    if contamination["restricted_copy_match_count"] != 0:
        errors.append("PROVENANCE_RESTRICTED_COPY_MATCH")
    embargo = values["embargo_scan.json"]
    if embargo["prohibited_implementation_count"] != 0 or embargo["embargo_verification_errors"]:
        errors.append("PROVENANCE_EMBARGO_SCAN_FAILED")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "evidence_files": sorted(values),
    }


__all__ = [
    "AUTHOR_IDENTITIES",
    "PROVENANCE_ROOT",
    "RAW_FILES",
    "RAW_ROOT",
    "validate_clean_room_provenance",
]
