"""Build isolated author bundles and validate clean-room component specifications."""

from __future__ import annotations

from copy import deepcopy
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from cumcm_skill_lab.adjudication.models import (
    file_sha256,
    read_json,
    read_yaml,
    sha256_json,
    write_json,
)

from .models import COMPONENT_IDS, RESULT_ROOT

SPEC_ROOT = Path("specifications/components")
PROVENANCE_PATH = Path("specifications/clean_room_provenance.yaml")
INPUT_ROOT = RESULT_ROOT / "component_spec_inputs"
COMPONENT_CONTRACT = Path("contracts/component_specification.schema.json")
PROVENANCE_CONTRACT = Path("contracts/clean_room_provenance.schema.json")
SOURCE_DECISION = Path("evals/results/phase-002d-r1/automated_decisions/component_readiness.json")
RAW_OUTPUT_ROOT = RESULT_ROOT / "subagent_outputs"
RAW_OUTPUT_FILES = {
    "accepted-versus-done-workflow-state": "state_component_spec_author.json",
    "claim-evidence-support-gate": "claim_evidence_spec_author.json",
    "hash-bound-reproducibility-manifest": "reproducibility_spec_author.json",
    "leakage-safe-model-comparison-gate": "leakage_comparison_spec_author.json",
}

REQUIREMENTS = {
    "accepted-versus-done-workflow-state": [
        "Distinguish task created, execution started, command completed, artifact produced, "
        "automatic validation passed, automatic adjudication accepted, final evidence frozen, "
        "stale and rejected.",
        "Enforce done != accepted, artifact exists != validated, validated != automatically "
        "accepted and automatically accepted != formally integrated.",
        "TEAM_COMPLIANCE_REVIEW never advances technical state; a supported challenge creates "
        "STALE, a finding, a test and re-adjudication.",
        "Use the existing project state and ledgers; never create another controller or FINAL "
        "authority.",
    ],
    "claim-evidence-support-gate": [
        "Define claim/evidence types, support, contradiction, supersession, source authority, "
        "Run/formula/table/figure binding and support strength.",
        "Distinguish evidence existence from support for the exact bounded claim.",
        "Reject stale, hash-mismatched, contradicted, overstated or unsupported causal claims.",
        "Only a scope-bounded supported claim may enter the evidence package.",
    ],
    "hash-bound-reproducibility-manifest": [
        "Bind inputs, raw manifest, commit/tree, config, seed, environment, dependencies, command, "
        "times, exit, solver/model, outputs, metrics, failure, supersession and reproduction "
        "command.",
        "Define mutation, stale, replay, partial output, failed/superseded runs and environment "
        "mismatch.",
        "Never store credentials, private keys, passwords, browser state, hidden reasoning or "
        "unnecessary private paths.",
        "Failed and partial runs remain explicit and never become successful reproducibility "
        "evidence.",
    ],
    "leakage-safe-model-comparison-gate": [
        "Define objective, train/validation/test, time/group splits, target/future leakage, "
        "baseline, frozen candidate set/metric, tie break, failed runs, seeds, robustness, "
        "ablation and access ledger.",
        "The test set never participates in generation, feature/hyperparameter/threshold tuning, "
        "architecture selection, early stopping or result filtering.",
        "Premature test access invalidates the run and dependent decisions and requires a new "
        "sealed test set.",
        "Final test evaluation is one-time and retains failed runs and all access evidence.",
    ],
}


def _source_paths(component_id: str) -> tuple[str, ...]:
    return (
        f"research/upstream_candidates/component_cards/{component_id}.yaml",
        "evals/results/phase-002d-r1/input_freeze_manifest.json",
        "evals/results/phase-002d-r1/evidence_scopes/evidence_scope_summary.json",
        "rules/phase002d_r2_workflow_rules.yaml",
        "WORKFLOW.md",
        COMPONENT_CONTRACT.as_posix(),
        PROVENANCE_CONTRACT.as_posix(),
    )


def build_component_author_bundles(root: Path) -> dict[str, dict[str, Any]]:
    decision = read_json(root / SOURCE_DECISION)
    by_component = {
        item["mechanism_id"]: item for item in decision["automated_decision"]["component_results"]
    }
    bundles: dict[str, dict[str, Any]] = {}
    for component_id in COMPONENT_IDS:
        input_dir = root / INPUT_ROOT / component_id
        excerpt_body = {
            "schema_version": "1.0.0",
            "decision_id": decision["automated_decision"]["decision_id"],
            "decision": by_component[component_id]["decision"],
            "accepted_scope": by_component[component_id]["accepted_scope"],
            "component_result": by_component[component_id],
            "source_decision_file_hash": file_sha256(root / SOURCE_DECISION),
        }
        excerpt = {**excerpt_body, "excerpt_hash": sha256_json(excerpt_body)}
        write_json(input_dir / "decision.json", excerpt)
        allowed = _source_paths(component_id)
        body: dict[str, Any] = {
            "schema_version": "1.0.0",
            "bundle_id": f"PHASE-002D-R2-SPEC-AUTHOR-{component_id.upper()}",
            "role": f"{component_id}-spec-author",
            "component_id": component_id,
            "round": "FIRST_ROUND",
            "independent": True,
            "read_only": True,
            "peer_outputs_visible": False,
            "expected_conclusion_visible": False,
            "decision_excerpt_path": (INPUT_ROOT / component_id / "decision.json").as_posix(),
            "decision_excerpt_hash": excerpt["excerpt_hash"],
            "allowed_file_references": list(allowed),
            "source_hashes": {path: file_sha256(root / path) for path in allowed},
            "component_requirements": REQUIREMENTS[component_id],
            "output_contract": COMPONENT_CONTRACT.as_posix(),
            "output_instruction": (
                "Return exactly one JSON object that validates as a SPECIFICATION_DRAFT. "
                "Use a 64-zero placeholder for specification_hash and provenance_hash; the main "
                "agent will compute canonical hashes without changing material recommendations."
            ),
            "prohibitions": [
                "no file writes, commits, pushes or formal-state changes",
                "no peer outputs or expected main-agent conclusion",
                "no web, MCP, nested Codex, API key or third-party repository access",
                "no copied third-party code, schema, prompt, state machine, template or long text",
                "no implementation, architecture selection, performance claim or majority vote",
                "no fabricated evidence; abstain explicitly if the frozen inputs are insufficient",
            ],
        }
        bundle = {**body, "bundle_hash": sha256_json(body)}
        write_json(input_dir / "bundle.json", bundle)
        bundles[component_id] = bundle
    return bundles


def validate_component_author_bundles(root: Path) -> list[str]:
    errors: list[str] = []
    for component_id in COMPONENT_IDS:
        input_dir = root / INPUT_ROOT / component_id
        for name in ("decision.json", "bundle.json"):
            if not (input_dir / name).is_file():
                errors.append(f"COMPONENT_AUTHOR_INPUT_MISSING:{component_id}:{name}")
        if errors:
            continue
        decision = read_json(input_dir / "decision.json")
        decision_body = dict(decision)
        decision_hash = decision_body.pop("excerpt_hash", None)
        if sha256_json(decision_body) != decision_hash:
            errors.append(f"COMPONENT_DECISION_EXCERPT_HASH_MISMATCH:{component_id}")
        bundle = read_json(input_dir / "bundle.json")
        bundle_body = dict(bundle)
        bundle_hash = bundle_body.pop("bundle_hash", None)
        if sha256_json(bundle_body) != bundle_hash:
            errors.append(f"COMPONENT_AUTHOR_BUNDLE_HASH_MISMATCH:{component_id}")
        if bundle.get("peer_outputs_visible") is not False or bundle.get("read_only") is not True:
            errors.append(f"COMPONENT_AUTHOR_ISOLATION_INVALID:{component_id}")
        for relative, expected in bundle.get("source_hashes", {}).items():
            path = root / relative
            if not path.is_file() or file_sha256(path) != expected:
                errors.append(f"COMPONENT_AUTHOR_SOURCE_DRIFT:{component_id}:{relative}")
    return sorted(set(errors))


def _schema_errors(schema: dict[str, Any], value: Any, prefix: str) -> list[str]:
    return [
        f"{prefix}:{'/'.join(str(part) for part in item.absolute_path)}:{item.message}"
        for item in Draft202012Validator(schema).iter_errors(value)
    ]


def seal_component_draft(root: Path, draft: dict[str, Any], component_id: str) -> dict[str, Any]:
    """Normalize only draft status and canonical hashes; preserve all authored content."""
    if component_id not in COMPONENT_IDS or draft.get("component_id") != component_id:
        raise ValueError("COMPONENT_DRAFT_ID_MISMATCH")
    if draft.get("status") != "SPECIFICATION_DRAFT":
        raise ValueError("COMPONENT_DRAFT_STATUS_INVALID")
    if draft.get("accepted_scope") != "SPECIFICATION_ONLY":
        raise ValueError("COMPONENT_DRAFT_SCOPE_INVALID")
    schema = read_json(root / COMPONENT_CONTRACT)
    errors = _schema_errors(schema, draft, f"COMPONENT_DRAFT_SCHEMA:{component_id}")
    if errors:
        raise ValueError(";".join(errors))
    value = deepcopy(draft)
    provenance = dict(value["clean_room_provenance"])
    provenance.pop("provenance_hash", None)
    value["clean_room_provenance"]["provenance_hash"] = sha256_json(provenance)
    value["status"] = "SPECIFICATION_FROZEN"
    value.pop("specification_hash", None)
    value["specification_hash"] = sha256_json(value)
    return value


def seal_component_outputs(root: Path) -> dict[str, str]:
    """Seal schema-valid raw author outputs without changing material recommendations."""
    records: list[dict[str, Any]] = []
    hashes: dict[str, str] = {}
    for component_id in COMPONENT_IDS:
        raw_path = root / RAW_OUTPUT_ROOT / RAW_OUTPUT_FILES[component_id]
        sealed = seal_component_draft(root, read_json(raw_path), component_id)
        write_json(root / SPEC_ROOT / f"{component_id}.yaml", sealed)
        records.append(sealed["clean_room_provenance"])
        hashes[component_id] = sealed["specification_hash"]
    registry_body = {"schema_version": "1.0.0", "records": records}
    registry = {**registry_body, "registry_hash": sha256_json(registry_body)}
    write_json(root / PROVENANCE_PATH, registry)
    return hashes


def _hash_errors(spec: dict[str, Any], component_id: str) -> list[str]:
    errors: list[str] = []
    provenance = dict(spec.get("clean_room_provenance", {}))
    provenance_hash = provenance.pop("provenance_hash", None)
    if sha256_json(provenance) != provenance_hash:
        errors.append(f"PROVENANCE_HASH_MISMATCH:{component_id}")
    body = dict(spec)
    specification_hash = body.pop("specification_hash", None)
    if sha256_json(body) != specification_hash:
        errors.append(f"COMPONENT_SPECIFICATION_HASH_MISMATCH:{component_id}")
    return errors


def _overlap_errors(root: Path, spec: dict[str, Any], component_id: str) -> list[str]:
    provenance = spec.get("clean_room_provenance", {})
    auditable = {key: value for key, value in spec.items() if key != "clean_room_provenance"}
    spec_text = str(auditable).lower()
    source_text = (
        (root / f"research/upstream_candidates/component_cards/{component_id}.yaml")
        .read_text(encoding="utf-8")
        .lower()
    )
    ratio = SequenceMatcher(None, spec_text, source_text).ratio()
    errors: list[str] = []
    if ratio > 0.55:
        errors.append(f"CLEAN_ROOM_SIMILARITY_WARNING:{component_id}:{ratio:.3f}")
    if provenance.get("allowed_reuse_mode") != "REFERENCE_ABSTRACT_MECHANISM":
        errors.append(f"CLEAN_ROOM_REUSE_MODE_INVALID:{component_id}")
    return errors


def validate_component_specifications(root: Path) -> dict[str, Any]:
    errors = validate_component_author_bundles(root)
    schema = read_json(root / COMPONENT_CONTRACT)
    provenance_schema = read_json(root / PROVENANCE_CONTRACT)
    specs: dict[str, dict[str, Any]] = {}
    for component_id in COMPONENT_IDS:
        path = root / SPEC_ROOT / f"{component_id}.yaml"
        if not path.is_file():
            errors.append(f"COMPONENT_SPECIFICATION_MISSING:{component_id}")
            continue
        spec = read_yaml(path)
        specs[component_id] = spec
        errors.extend(_schema_errors(schema, spec, f"COMPONENT_SCHEMA:{component_id}"))
        if spec.get("component_id") != component_id:
            errors.append(f"COMPONENT_ID_MISMATCH:{component_id}")
        if spec.get("status") != "SPECIFICATION_FROZEN":
            errors.append(f"COMPONENT_NOT_FROZEN:{component_id}")
        errors.extend(_hash_errors(spec, component_id))
        errors.extend(_overlap_errors(root, spec, component_id))
    provenance_path = root / PROVENANCE_PATH
    if not provenance_path.is_file():
        errors.append("CLEAN_ROOM_PROVENANCE_REGISTRY_MISSING")
    else:
        registry = read_yaml(provenance_path)
        errors.extend(_schema_errors(provenance_schema, registry, "PROVENANCE_SCHEMA"))
        registry_body = dict(registry)
        registry_hash = registry_body.pop("registry_hash", None)
        if sha256_json(registry_body) != registry_hash:
            errors.append("PROVENANCE_REGISTRY_HASH_MISMATCH")
        by_id = {item.get("component_id"): item for item in registry.get("records", [])}
        if set(by_id) != set(COMPONENT_IDS):
            errors.append("PROVENANCE_COMPONENT_SET_MISMATCH")
        for component_id, spec in specs.items():
            if by_id.get(component_id) != spec.get("clean_room_provenance"):
                errors.append(f"PROVENANCE_REGISTRY_SPEC_MISMATCH:{component_id}")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "component_count": len(specs),
        "component_ids": sorted(specs),
        "accepted_scope": "SPECIFICATION_ONLY",
    }


__all__ = [
    "COMPONENT_CONTRACT",
    "INPUT_ROOT",
    "build_component_author_bundles",
    "seal_component_draft",
    "seal_component_outputs",
    "validate_component_author_bundles",
    "validate_component_specifications",
]
