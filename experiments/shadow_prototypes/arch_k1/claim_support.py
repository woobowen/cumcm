"""Deterministic claim/evidence binding and exact-support kernel."""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Any

from experiments.shadow_prototypes.common.interface import sha256_json

from .reproducibility import verified_run_record


class ClaimDisposition(StrEnum):
    SUPPORTED = "SUPPORTED"
    REJECTED = "REJECTED"
    ABSTAINED = "ABSTAINED"


ALLOWED_CLAIM_TYPES = frozenset(
    {
        "FACT",
        "COMPUTATIONAL_RESULT",
        "ASSUMPTION",
        "LIMITATION",
        "METHOD",
        "CAUSAL",
        "CONCLUSION",
    }
)
SEMANTIC_FIELDS = ("bounded_proposition", "scope", "modality", "strength")
RUN_BINDING_FIELDS = ("run_id", "input_hash", "code_commit", "output_hash", "lineage")
STRENGTH_RANK = {"NONE": 0, "WEAK": 1, "MODERATE": 2, "STRONG": 3}
EVIDENCE_AUTHORITIES = {
    "RUN": "existing-native-run-ledger",
    "SOURCE": "existing-native-source-ledger",
    "RAW_DATA": "existing-native-source-ledger",
    "FORMULA": "existing-native-run-ledger",
    "TABLE": "existing-native-run-ledger",
    "FIGURE": "existing-native-run-ledger",
    "TRANSFORMATION": "existing-native-run-ledger",
}


def _safe_locator(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    locator = PurePosixPath(value)
    return bool(
        locator.parts
        and not locator.is_absolute()
        and ".." not in locator.parts
        and locator.parts[0] in {"runs", "sources"}
    )


def evaluate_claim_support(
    payload: Mapping[str, Any], isolated_state: Mapping[str, Any]
) -> tuple[bool | None, tuple[str, ...], dict[str, Any]]:
    reasons: list[str] = []
    claim = payload.get("claim")
    if not isinstance(claim, Mapping):
        return (
            False,
            ("K1_CLAIM_RECORD_INVALID",),
            {
                "disposition": ClaimDisposition.REJECTED.value,
                "supporting_evidence": [],
            },
        )
    claim_type = str(claim.get("claim_type", ""))
    if claim_type not in ALLOWED_CLAIM_TYPES:
        reasons.append("K1_CLAIM_TYPE_INVALID")
    run_id = claim.get("run_id")
    trusted_run_bindings = isolated_state.get("trusted_run_bindings", {})
    run_binding = (
        trusted_run_bindings.get(run_id) if isinstance(trusted_run_bindings, Mapping) else None
    )
    if not isinstance(run_binding, Mapping) or any(
        claim.get(field) != run_binding.get(field) for field in RUN_BINDING_FIELDS
    ):
        reasons.append("K1_CLAIM_TRUSTED_RUN_BINDING_INVALID")
    if not verified_run_record(
        payload.get("verified_run_manifest"), isolated_state, expected_run_id=str(run_id)
    ):
        reasons.append("K1_CLAIM_VERIFIED_RUN_REQUIRED")

    evidence = payload.get("evidence")
    if not isinstance(evidence, (list, tuple)):
        evidence_items: tuple[Any, ...] = ()
        reasons.append("K1_CLAIM_EVIDENCE_SET_INVALID")
    else:
        evidence_items = tuple(evidence)
    supporting: set[str] = set()
    trusted_hashes = isolated_state.get("trusted_artifact_hashes", {})
    if not isinstance(trusted_hashes, Mapping):
        trusted_hashes = {}
        reasons.append("K1_CLAIM_TRUST_REGISTRY_INVALID")
    for item in evidence_items:
        if not isinstance(item, Mapping):
            reasons.append("K1_CLAIM_EVIDENCE_RECORD_INVALID")
            continue
        locator = item.get("locator")
        if item.get("registered") is not True or not _safe_locator(locator):
            reasons.append("K1_CLAIM_EVIDENCE_REFERENCE_INVALID")
        evidence_type = item.get("evidence_type")
        if evidence_type not in EVIDENCE_AUTHORITIES or item.get(
            "authority"
        ) != EVIDENCE_AUTHORITIES.get(evidence_type):
            reasons.append("K1_CLAIM_EVIDENCE_AUTHORITY_INVALID")
        body = item.get("artifact_body")
        artifact_hash = item.get("artifact_hash")
        hash_bound = bool(
            isinstance(body, Mapping)
            and artifact_hash == sha256_json(body)
            and artifact_hash == trusted_hashes.get(str(locator))
            and item.get("registry_hash")
            == sha256_json({"locator": str(locator), "artifact_hash": artifact_hash})
        )
        if not hash_bound:
            reasons.append("K1_CLAIM_EVIDENCE_BINDING_INVALID")
        bound_fields = (
            *SEMANTIC_FIELDS,
            "evidence_type",
            *RUN_BINDING_FIELDS,
            "revision_id",
            "prior_revision_hash",
            "superseded",
        )
        semantics_bound = isinstance(body, Mapping) and all(
            item.get(field) == body.get(field) for field in bound_fields
        )
        if not semantics_bound:
            reasons.append("K1_CLAIM_SEMANTIC_BINDING_INVALID")
        if item.get("current") is not True:
            reasons.append("K1_CLAIM_STALE_EVIDENCE")
        if item.get("superseded") is not False:
            reasons.append("K1_CLAIM_SUPERSEDED_EVIDENCE")
        if item.get("run_id") != run_id:
            reasons.append("K1_CLAIM_RUN_BINDING_INVALID")
        if item.get("contradicts"):
            reasons.append("K1_CLAIM_CONTRADICTION")
        evidence_strength = body.get("strength") if isinstance(body, Mapping) else None
        required_strength = "STRONG" if claim_type in {"CAUSAL", "CONCLUSION"} else "MODERATE"
        exact = bool(
            hash_bound
            and semantics_bound
            and body.get("bounded_proposition") == claim.get("proposition")
            and body.get("scope") == claim.get("scope")
            and body.get("modality") == claim.get("modality")
            and evidence_strength in STRENGTH_RANK
            and claim.get("strength") in STRENGTH_RANK
            and STRENGTH_RANK[evidence_strength] >= STRENGTH_RANK[claim.get("strength")]
            and STRENGTH_RANK[evidence_strength] >= STRENGTH_RANK[required_strength]
            and isinstance(run_binding, Mapping)
            and all(body.get(field) == run_binding.get(field) for field in RUN_BINDING_FIELDS)
            and item.get("current") is True
            and item.get("run_id") == run_id
            and not item.get("contradicts")
        )
        if exact:
            supporting.add(str(item.get("evidence_id", "")))
    if not supporting:
        reasons.append("K1_CLAIM_EXACT_SUPPORT_MISSING")
    if claim_type == "CAUSAL":
        identification = claim.get("causal_identification")
        causal_support = bool(
            isinstance(identification, Mapping)
            and identification.get("design")
            in {"RANDOMIZED", "VALID_INSTRUMENT", "NATURAL_EXPERIMENT"}
            and isinstance(identification.get("analysis_hash"), str)
            and len(identification["analysis_hash"]) == 64
            and all(
                character in "0123456789abcdef" for character in identification["analysis_hash"]
            )
            and all(
                isinstance(item, Mapping)
                and isinstance(item.get("artifact_body"), Mapping)
                and item["artifact_body"].get("modality") == "causal"
                for item in evidence_items
            )
        )
        if not causal_support:
            reasons.append("K1_CLAIM_CAUSAL_IDENTIFICATION_INADEQUATE")
    if payload.get("narrative_override"):
        reasons.append("K1_CLAIM_NARRATIVE_BYPASS_REJECTED")
    semantic_review = payload.get("semantic_review")
    if not reasons and isinstance(semantic_review, Mapping):
        relation = semantic_review.get("relation")
        if relation == "ABSTAIN":
            return (
                None,
                ("K1_CLAIM_SEMANTIC_REVIEW_ABSTAINED",),
                {
                    "disposition": ClaimDisposition.ABSTAINED.value,
                    "supporting_evidence": sorted(supporting),
                },
            )
        if relation not in {None, "SUPPORTS_EXACT"}:
            reasons.append("K1_CLAIM_SEMANTIC_REVIEW_NOT_EXACT")
    disposition = ClaimDisposition.SUPPORTED if not reasons else ClaimDisposition.REJECTED
    return (
        not reasons,
        tuple(sorted(set(reasons))),
        {
            "disposition": disposition.value,
            "supporting_evidence": sorted(supporting),
        },
    )


__all__ = ["ClaimDisposition", "evaluate_claim_support"]
