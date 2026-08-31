"""Build deterministic, role-specific Phase 002B evidence bundles."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..models import (
    canonical_json,
    check_or_write,
    file_sha256,
    read_json,
    read_yaml,
    sha256_json,
    write_json,
)
from .completeness import completeness_errors
from .role_views import (
    ROLE_EVIDENCE_SECTIONS,
    ROLE_ORDER,
    ROLE_SCOPES,
    ROLE_SLUGS,
    runtime_output_schema,
    select_findings,
    select_test_evidence,
)
from .size_budget import enforce_size_budget

RESULT_ROOT = Path("evals/results/phase-002b")
CACHE_ROOT = Path(".cache/adjudication-002b/bundles")

SOURCE_PATHS = {
    "eligibility": "evals/results/phase-002a/eligibility/classification.json",
    "coverage": "evals/results/phase-002a/structured_coverage/coverage.json",
    "oracles": "evals/results/phase-002a/oracle_correctness/oracles.json",
    "process": "evals/results/phase-002a/process_evidence/process.json",
    "recovery": "evals/results/phase-002a/recovery_gap_evidence/recovery.json",
    "findings": "evals/results/phase-002a/adversarial/findings.json",
    "test_evidence": "evals/results/phase-002a/adversarial/test_evidence.json",
    "input_freeze": "evals/results/phase-002b/input_freeze_manifest.json",
}

ROLE_OUTPUT_PATHS = {
    "CORRECTNESS_JUDGE": "evals/results/phase-002b/judge_outputs/correctness.json",
    "SCIENTIFIC_VALIDITY_JUDGE": "evals/results/phase-002b/judge_outputs/scientific_validity.json",
    "ENGINEERING_REPRODUCIBILITY_JUDGE": (
        "evals/results/phase-002b/judge_outputs/engineering_reproducibility.json"
    ),
    "BLIND_DISSENT_JUDGE": "evals/results/phase-002b/dissent_outputs/blind_dissent.json",
    "EVIDENCE_META_ADJUDICATOR": "evals/results/phase-002b/meta_outputs/meta_adjudication.json",
}


def _sources(root: Path) -> dict[str, Any]:
    return {name: read_json(root / path) for name, path in SOURCE_PATHS.items()}


def _dependencies(root: Path, role: str) -> dict[str, Any]:
    if role in ROLE_ORDER[:4]:
        required: tuple[str, ...] = ()
    elif role == "EVIDENCE_META_ADJUDICATOR":
        required = ROLE_ORDER[:4]
    else:
        required = ROLE_ORDER[:5]
    records: list[dict[str, Any]] = []
    for dependency_role in required:
        relative = ROLE_OUTPUT_PATHS[dependency_role]
        path = root / relative
        records.append(
            {
                "role": dependency_role,
                "path": relative,
                "status": "AVAILABLE" if path.is_file() else "PENDING",
                "sha256": file_sha256(path) if path.is_file() else None,
                "content": read_json(path) if path.is_file() else None,
            }
        )
    if role == "DECISION_AUDITOR":
        decision_dir = root / RESULT_ROOT / "automated_decisions"
        decision_paths = sorted(decision_dir.glob("*.json")) if decision_dir.is_dir() else []
        records.append(
            {
                "role": "AUTOMATED_DECISIONS",
                "status": "AVAILABLE" if len(decision_paths) == 3 else "PENDING",
                "paths": [str(path.relative_to(root)) for path in decision_paths],
                "sha256": {
                    str(path.relative_to(root)): file_sha256(path) for path in decision_paths
                },
                "content": [read_json(path) for path in decision_paths],
            }
        )
    return {
        "required": list(required),
        "ready": all(item["status"] == "AVAILABLE" for item in records),
        "records": records,
    }


def _hard_gates(config: dict, findings: list[dict], freeze: dict) -> dict:
    blocker_refs = [item["finding_id"] for item in findings if item["severity"] == "BLOCKER"]
    return {
        "policy_hash": freeze["policy_hash"],
        "hard_gates": [
            {"gate": gate, "status": "MUST_EVALUATE", "evidence_refs": blocker_refs}
            for gate in config["hard_gates"]
        ],
        "non_compensable": True,
        "majority_vote_cannot_pass_gate": True,
    }


def _eligible_view(role: str, sources: dict[str, Any]) -> dict:
    sections = ROLE_EVIDENCE_SECTIONS[role]
    return {
        "role": role,
        "evidence_sections": list(sections),
        "comparative_summary": sources["eligibility"]["summary"],
        "sections": {name: sources[name] for name in sections},
        "source_content_hashes": {name: sources[name].get("content_hash") for name in sections},
    }


def _excluded_view(sources: dict[str, Any], config: dict) -> dict:
    return {
        "recovery_policy": config["recovery_policy"],
        "evidence_record_policy": sources["recovery"]["policy"],
        "recovery_records": sources["recovery"]["records"],
        "failed_attempts": sources["eligibility"]["failed_attempts"],
        "excluded_unblinded_dissent": sources["input_freeze"]["excluded_unblinded_dissent"],
        "prohibited_uses": [
            "comparative ranking",
            "candidate selection",
            "correctness substitution",
            "formal blind dissent substitution",
        ],
    }


def _role_task(role: str, dependencies: dict[str, Any]) -> dict:
    prohibitions = [
        "do not infer candidate identity",
        "do not use majority vote or social proof",
        "do not use a human technical gate",
        "do not rank recovery-affected evidence",
        "do not treat structured coverage as correctness",
        "do not fabricate or infer missing runs",
        "do not change frozen thresholds or policy",
        "do not start or select Phase 003",
    ]
    return {
        "role": role,
        "scope": ROLE_SCOPES[role],
        "mandatory_files": [
            "bundle_index.json",
            "policy_summary.json",
            "eligible_evidence.json",
            "excluded_evidence.json",
            "hard_gates.json",
            "findings.json",
            "test_evidence.json",
            "output_schema.json",
        ],
        "dependencies_ready": dependencies["ready"],
        "prohibitions": prohibitions,
        "evidence_reference_rule": (
            "Every technical assertion must cite an evidence ID, test ID, finding ID, or frozen "
            "numeric field present in this bundle."
        ),
        "output_rule": "Return JSON only and satisfy output_schema.json exactly.",
    }


def build_role(root: Path, role: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if role not in ROLE_ORDER:
        raise ValueError(f"UNSUPPORTED_ROLE:{role}")
    sources = _sources(root)
    config = read_yaml(root / "adjudication/configs/phase-002a.yaml")
    policy = read_yaml(root / "adjudication/policies/phase-002a.yaml")
    freeze = sources["input_freeze"]
    selected_findings = select_findings(role, sources["findings"]["findings"])
    selected_evidence = select_test_evidence(
        selected_findings, sources["test_evidence"]["evidence"]
    )
    dependencies = _dependencies(root, role)
    slug = ROLE_SLUGS[role]
    index = {
        "schema_version": "1.0.0",
        "bundle_id": f"PHASE-002B-{role}",
        "role": role,
        "slug": slug,
        "subject_commit": freeze["subject_commit"],
        "input_freeze_hash": freeze["freeze_hash"],
        "policy_hash": freeze["policy_hash"],
        "evidence_hash": freeze["evidence_hash"],
        "model": config["model"],
        "reasoning_setting": config["reasoning_setting"],
        "identity_blind": True,
        "peer_outputs_visible": role in ROLE_ORDER[4:],
        "dependency_status": {item["role"]: item["status"] for item in dependencies["records"]},
    }
    files: dict[str, Any] = {
        "policy_summary.json": {
            "policy_id": policy["policy_id"],
            "policy_version": policy["version"],
            "policy_hash": policy["policy_hash"],
            "evidence_hierarchy": policy["evidence_hierarchy"],
            "decision_order": policy["decision_order"],
            "hard_gates": policy["hard_gates"],
            "balanced_case_minimum": policy["balanced_case_minimum"],
            "minimum_repeats": policy["minimum_repeats"],
            "decision_statuses": policy["decision_statuses"],
            "recovery_policy": config["recovery_policy"],
            "accepted_scope_limit": "SPECIFICATION_ONLY",
            "phase_transition_policy": config["phase_transition_policy"],
        },
        "eligible_evidence.json": _eligible_view(role, sources),
        "excluded_evidence.json": _excluded_view(sources, config),
        "hard_gates.json": _hard_gates(config, selected_findings, freeze),
        "findings.json": {
            "selection_rule": "ALL_BLOCKERS_PLUS_ROLE_RELEVANT_FINDINGS",
            "findings": selected_findings,
        },
        "test_evidence.json": {"evidence": selected_evidence},
        "dependencies.json": dependencies,
        "role_task.json": _role_task(role, dependencies),
    }
    payload_hash = sha256_json(files)
    index["payload_hash"] = payload_hash
    index["bundle_hash"] = payload_hash
    files["bundle_index.json"] = index
    files["output_schema.json"] = runtime_output_schema(
        role,
        bundle_hash=payload_hash,
        policy_hash=freeze["policy_hash"],
        evidence_hash=freeze["evidence_hash"],
    )
    all_blockers = {
        item["finding_id"]
        for item in sources["findings"]["findings"]
        if item["severity"] == "BLOCKER"
    }
    errors = completeness_errors(files, all_blockers)
    measurement = enforce_size_budget(files)
    if errors:
        raise ValueError("BUNDLE_INCOMPLETE:" + ",".join(errors))
    file_records = {
        name: {
            "sha256": sha256_json(value),
            "normalized_bytes": len(canonical_json(value).encode()),
        }
        for name, value in sorted(files.items())
    }
    manifest = {
        "schema_version": "1.0.0",
        "bundle_id": index["bundle_id"],
        "role": role,
        "slug": slug,
        "payload_hash": payload_hash,
        "bundle_hash": sha256_json(files),
        "input_freeze_hash": freeze["freeze_hash"],
        "policy_hash": freeze["policy_hash"],
        "evidence_hash": freeze["evidence_hash"],
        "output_schema_hash": sha256_json(files["output_schema.json"]),
        "dependencies_ready": dependencies["ready"],
        "blocker_ids": sorted(all_blockers),
        "recovery_excluded_count": len(sources["recovery"]["records"]),
        "measurement": measurement,
        "files": file_records,
    }
    manifest["manifest_hash"] = sha256_json(manifest)
    return files, manifest


def build_all(root: Path, *, check: bool) -> dict[str, Any]:
    errors: list[str] = []
    manifests: dict[str, dict[str, Any]] = {}
    for role in ROLE_ORDER:
        files, manifest = build_role(root, role)
        slug = ROLE_SLUGS[role]
        manifest_path = root / RESULT_ROOT / "bundle_manifests" / f"{slug}.json"
        errors.extend(check_or_write(manifest_path, manifest, check=check))
        cache_dir = root / CACHE_ROOT / slug
        for name, value in files.items():
            path = cache_dir / name
            if check:
                if not path.is_file():
                    errors.append(f"MISSING:{path}")
                elif read_json(path) != value:
                    errors.append(f"MISMATCH:{path}")
            else:
                write_json(path, value)
        manifests[role] = manifest
    return {
        "status": "PASS" if not errors else "FAIL",
        "roles": len(manifests),
        "bundle_hashes": {role: item["bundle_hash"] for role, item in manifests.items()},
        "errors": errors,
    }
