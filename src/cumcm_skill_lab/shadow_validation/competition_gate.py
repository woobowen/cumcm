"""Frozen public-only competition architecture gate for the R3 fast track."""

from __future__ import annotations

import ast
import hashlib
import json
import math
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any

from experiments.shadow_prototypes import COMPONENT_IDS
from experiments.shadow_prototypes.arch_k1.kernel import evaluate_composed_evidence_package
from experiments.shadow_prototypes.common.interface import (
    ShadowCaseInput,
    ShadowContext,
    sha256_json,
    thaw,
)
from experiments.shadow_prototypes.common.public_cases import (
    load_public_cases,
    public_isolated_state,
)

from .runner import run_case

K1 = "ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL"
W1 = "ARCH-W1-WORKFLOW-ONLY-GUARDS"
ARCHITECTURE_ORDER = (K1, W1)
GATE_IDS = (
    "G1_MALFORMED_INPUT_FAIL_CLOSED",
    "G2_DONE_IS_NOT_ACCEPTED",
    "G3_CLAIM_EVIDENCE_EXACT_SUPPORT",
    "G4_REPRODUCIBILITY_MANIFEST",
    "G5_LEAKAGE_SAFE_COMPARISON",
    "G6_INPUT_AND_STATE_ISOLATION",
    "G7_SECURITY_AND_PROVENANCE",
    "G8_END_TO_END_COMPONENT_COMPOSITION",
)
FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp",
    "httpx",
    "requests",
    "socket",
    "subprocess",
    "urllib",
}


def _raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _case(
    cases: list[ShadowCaseInput], component_id: str, case_class: str = "valid control"
) -> ShadowCaseInput:
    return next(
        item
        for item in cases
        if item.component_id == component_id and item.case_class == case_class
    )


def _payload(case: ShadowCaseInput) -> dict[str, Any]:
    return thaw(case.payload)


def _run(
    root: Path,
    architecture_id: str,
    case: ShadowCaseInput,
    output_root: Path,
    *,
    state: Any | None = None,
    stage: Any = "PUBLIC_VALIDATION",
    enabled_components: Any = COMPONENT_IDS,
) -> tuple[Any, bool]:
    context = ShadowContext(
        run_id=f"003F-{architecture_id}-{case.case_id}",
        architecture_id=architecture_id,
        stage=stage,
        output_dir=output_root / architecture_id / case.case_id,
        timeout_seconds=30,
        operation_budget=100,
        enabled_components=enabled_components,
    )
    return run_case(
        root,
        architecture_id,
        case,
        public_isolated_state() if state is None else state,
        context,
        persist=False,
    )


def _run_payload(
    root: Path,
    architecture_id: str,
    base_case: ShadowCaseInput,
    probe_id: str,
    payload: dict[str, Any],
    output_root: Path,
    *,
    state: Any | None = None,
) -> tuple[Any, bool]:
    case = replace(
        base_case,
        case_id=f"{base_case.case_id}-{probe_id.lower()}",
        payload=payload,
        input_hash=sha256_json(payload),
        case_class=f"competition probe:{probe_id}",
    )
    return _run(root, architecture_id, case, output_root, state=state)


def _gate(status: bool, evidence: list[str], reasons: list[str] | None = None) -> dict[str, Any]:
    return {
        "status": "PASS" if status else "FAIL",
        "evidence": sorted(set(evidence)),
        "reason_codes": sorted(set(reasons or ([] if status else ["GATE_REQUIREMENT_FAILED"]))),
    }


def _require_rejections(
    root: Path,
    architecture_id: str,
    base_case: ShadowCaseInput,
    probes: list[tuple[str, dict[str, Any]]],
    output_root: Path,
) -> tuple[list[str], list[str]]:
    evidence: list[str] = []
    failures: list[str] = []
    for probe_id, payload in probes:
        try:
            result, unchanged = _run_payload(
                root, architecture_id, base_case, probe_id, payload, output_root
            )
        except Exception as exc:  # noqa: BLE001 - uncaught candidate behavior is Gate evidence
            failures.append(f"{probe_id}:UNCAUGHT_{type(exc).__name__}")
            continue
        evidence.append(
            f"{probe_id}:{result.decision.outcome}:{','.join(result.decision.reason_codes)}"
        )
        if result.decision.outcome != "BLOCK":
            failures.append(f"{probe_id}:NOT_REJECTED")
        if not result.decision.reason_codes:
            failures.append(f"{probe_id}:NO_STABLE_REASON_CODE")
        if not unchanged:
            failures.append(f"{probe_id}:INPUT_MUTATED")
    return evidence, failures


def _public_component_cases(
    root: Path,
    architecture_id: str,
    cases: list[ShadowCaseInput],
    output_root: Path,
    component_id: str,
    required_markers: tuple[str, ...],
) -> tuple[list[str], list[str]]:
    evidence: list[str] = []
    failures: list[str] = []
    for case_class in ("valid control", "missing evidence", "stale mutation", "gaming attempt"):
        case = _case(cases, component_id, case_class)
        try:
            result, unchanged = _run(root, architecture_id, case, output_root)
        except Exception as exc:  # noqa: BLE001 - uncaught candidate behavior is Gate evidence
            failures.append(f"{case.case_id}:UNCAUGHT_{type(exc).__name__}")
            continue
        expected = "PASS" if case_class == "valid control" else "BLOCK"
        evidence.append(
            f"{case.case_id}:{result.decision.outcome}:{','.join(result.decision.reason_codes)}"
        )
        if result.decision.outcome != expected:
            failures.append(f"{case.case_id}:EXPECTED_{expected}")
        if not unchanged:
            failures.append(f"{case.case_id}:INPUT_MUTATED")
    for marker in required_markers:
        if not any(marker in item for item in evidence):
            failures.append(f"GATE_SUBREQUIREMENT_MISSING:{marker}")
    return evidence, failures


def _malformed_gate(
    root: Path,
    architecture_id: str,
    cases: list[ShadowCaseInput],
    output_root: Path,
) -> dict[str, Any]:
    evidence: list[str] = []
    failures: list[str] = []
    for component_id in COMPONENT_IDS:
        base = _case(cases, component_id)
        valid = _payload(base)
        primary_field = {
            "accepted-versus-done-workflow-state": "evidenced_stages",
            "claim-evidence-support-gate": "claim",
            "hash-bound-reproducibility-manifest": "manifest",
            "leakage-safe-model-comparison-gate": "splits",
        }[component_id]
        probes = [
            (f"{component_id}:EMPTY_OBJECT", {}),
            (f"{component_id}:NULL_FIELD", {**valid, primary_field: None}),
            (f"{component_id}:WRONG_TYPE", {**valid, primary_field: 17}),
        ]
        probe_evidence, probe_failures = _require_rejections(
            root, architecture_id, base, probes, output_root
        )
        evidence.extend(probe_evidence)
        failures.extend(probe_failures)
    comparison = _case(cases, "leakage-safe-model-comparison-gate")
    valid_comparison = _payload(comparison)
    numerical = [
        ("EMPTY_SPLITS", {**valid_comparison, "splits": []}),
        ("NAN_SCORE", {**valid_comparison, "validation_scores": {"a": math.nan}}),
        ("POSITIVE_INF_SCORE", {**valid_comparison, "validation_scores": {"a": math.inf}}),
        ("NEGATIVE_INF_SCORE", {**valid_comparison, "validation_scores": {"a": -math.inf}}),
        ("EMPTY_CANDIDATE_SET", {**valid_comparison, "validation_scores": {}}),
    ]
    probe_evidence, probe_failures = _require_rejections(
        root, architecture_id, comparison, numerical, output_root
    )
    evidence.extend(probe_evidence)
    failures.extend(probe_failures)
    context_case = _case(cases, "accepted-versus-done-workflow-state")
    for probe_id, kwargs in (
        ("MALFORMED_CONTEXT_STAGE", {"stage": []}),
        ("MALFORMED_ENABLED_COMPONENTS", {"enabled_components": None}),
    ):
        try:
            result, _ = _run(root, architecture_id, context_case, output_root, **kwargs)
        except Exception as exc:  # noqa: BLE001 - this is the fail-closed counterexample
            failures.append(f"{probe_id}:UNCAUGHT_{type(exc).__name__}")
        else:
            evidence.append(
                f"{probe_id}:{result.decision.outcome}:{','.join(result.decision.reason_codes)}"
            )
            if result.decision.outcome != "BLOCK":
                failures.append(f"{probe_id}:NOT_REJECTED")
    return _gate(not failures, evidence, failures)


def _workflow_gate(
    root: Path,
    architecture_id: str,
    cases: list[ShadowCaseInput],
    output_root: Path,
) -> dict[str, Any]:
    evidence, failures = _public_component_cases(
        root,
        architecture_id,
        cases,
        output_root,
        "accepted-versus-done-workflow-state",
        ("STALE", "EVIDENCE"),
    )
    base = _case(cases, "accepted-versus-done-workflow-state")
    valid = _payload(base)
    stages = list(valid["evidenced_stages"])
    records = valid["evidence_records"]
    probes = [
        (
            "COMMAND_DONE_ONLY",
            {
                **valid,
                "evidenced_stages": stages[:3],
                "evidence_records": {key: records[key] for key in stages[:3]},
            },
        ),
        (
            "ARTIFACT_EXISTS_ONLY",
            {
                **valid,
                "evidenced_stages": stages[:4],
                "evidence_records": {key: records[key] for key in stages[:4]},
            },
        ),
        ("CHALLENGE_REQUIRES_STALE", {**valid, "team_challenge": {"supported": True}}),
    ]
    probe_evidence, probe_failures = _require_rejections(
        root, architecture_id, base, probes, output_root
    )
    evidence.extend(probe_evidence)
    failures.extend(probe_failures)
    return _gate(not failures, evidence, failures)


def _claim_gate(
    root: Path,
    architecture_id: str,
    cases: list[ShadowCaseInput],
    output_root: Path,
) -> dict[str, Any]:
    evidence, failures = _public_component_cases(
        root,
        architecture_id,
        cases,
        output_root,
        "claim-evidence-support-gate",
        ("EXACT_SUPPORT", "STALE"),
    )
    base = _case(cases, "claim-evidence-support-gate")
    valid = _payload(base)
    contradicted = _payload(base)
    contradicted["evidence"][0]["contradicts"] = [valid["claim"]["claim_id"]]
    manifest_tamper = _payload(base)
    manifest_tamper["verified_run_manifest"]["decision_id"] = "attacker-decision"
    probes = [
        ("CONTRADICTION", contradicted),
        ("UNBOUND_VERIFIED_RUN_DECISION", manifest_tamper),
    ]
    probe_evidence, probe_failures = _require_rejections(
        root, architecture_id, base, probes, output_root
    )
    evidence.extend(probe_evidence)
    failures.extend(probe_failures)
    if not any("CONTRADICT" in item for item in evidence):
        failures.append("GATE_SUBREQUIREMENT_MISSING:CONTRADICTION")
    return _gate(not failures, evidence, failures)


def _reproducibility_gate(
    root: Path,
    architecture_id: str,
    cases: list[ShadowCaseInput],
    output_root: Path,
) -> dict[str, Any]:
    evidence, failures = _public_component_cases(
        root,
        architecture_id,
        cases,
        output_root,
        "hash-bound-reproducibility-manifest",
        ("MUTATION", "BINDING"),
    )
    base = _case(cases, "hash-bound-reproducibility-manifest")
    probes: list[tuple[str, dict[str, Any]]] = []
    for outcome in ("FAILED", "PARTIAL", "SUPERSEDED"):
        item = _payload(base)
        item["manifest"]["outcome"] = outcome
        item["trusted_capture"]["outcome"] = outcome
        probes.append((f"RETAIN_{outcome}", item))
    for probe_id, extra in (
        ("PRIVATE_KEY", {"private_key": "synthetic-secret"}),
        ("REFRESH_TOKEN", {"refresh_token": "synthetic-token"}),
        ("UNC_PATH", {"scratch": "\\\\server\\private\\run"}),
    ):
        probes.append((probe_id, {**_payload(base), **extra}))
    probe_evidence, probe_failures = _require_rejections(
        root, architecture_id, base, probes, output_root
    )
    evidence.extend(probe_evidence)
    failures.extend(probe_failures)
    return _gate(not failures, evidence, failures)


def _comparison_gate(
    root: Path,
    architecture_id: str,
    cases: list[ShadowCaseInput],
    output_root: Path,
) -> dict[str, Any]:
    evidence, failures = _public_component_cases(
        root,
        architecture_id,
        cases,
        output_root,
        "leakage-safe-model-comparison-gate",
        ("PREMATURE_TEST_ACCESS", "STALE", "BASELINE"),
    )
    base = _case(cases, "leakage-safe-model-comparison-gate")
    valid = _payload(base)
    probes = [
        ("FUTURE_LEAKAGE", {**valid, "future_feature": True}),
        ("TARGET_LEAKAGE", {**valid, "target_feature": True}),
        ("GROUP_LEAKAGE", {**valid, "group_overlap": True}),
        ("TIME_LEAKAGE", {**valid, "time_order_valid": False}),
        (
            "NUMERIC_STRING_SCORE",
            {**valid, "validation_scores": {"a": "0.8", "b": "0.7"}},
        ),
        (
            "UNTRUSTED_FREEZE_HASHES",
            {**valid, "candidate_freeze_hash": "a" * 64, "metric_freeze_hash": "b" * 64},
        ),
    ]
    failed_scored = _payload(base)
    failed_scored["attempts"][0]["outcome"] = "FAILED"
    failed_scored["attempts"][0]["failure_class"] = "MODEL_FAILURE"
    probes.append(("FAILED_ATTEMPT_SCORED", failed_scored))
    access_tamper = _payload(base)
    event = access_tamper["access_events"][0]
    event["run_id"] = "unauthorized-run"
    body = {key: value for key, value in event.items() if key != "event_hash"}
    event["event_hash"] = sha256_json(body)
    probes.append(("UNAUTHORIZED_TEST_ACCESS", access_tamper))
    probe_evidence, probe_failures = _require_rejections(
        root, architecture_id, base, probes, output_root
    )
    evidence.extend(probe_evidence)
    failures.extend(probe_failures)
    return _gate(not failures, evidence, failures)


def _isolation_gate(
    root: Path,
    architecture_id: str,
    cases: list[ShadowCaseInput],
    output_root: Path,
) -> dict[str, Any]:
    evidence: list[str] = []
    failures: list[str] = []
    state_path = root / "state/project_state.json"
    state_before = _raw_sha256(state_path)
    for component_id in COMPONENT_IDS:
        case = _case(cases, component_id)
        result, unchanged = _run(root, architecture_id, case, output_root)
        evidence.append(f"{case.case_id}:{result.result_hash}")
        if not unchanged:
            failures.append(f"{case.case_id}:INPUT_MUTATED")
        if result.decision.outcome in {"FINAL", "FORMALLY_INTEGRATED"}:
            failures.append(f"{case.case_id}:FORMAL_OUTCOME_EMITTED")
    if _raw_sha256(state_path) != state_before:
        failures.append("FORMAL_PROJECT_STATE_MUTATED")
    workflow = _case(cases, "accepted-versus-done-workflow-state")
    try:
        production, _ = _run(root, architecture_id, workflow, output_root, stage="PRODUCTION")
    except Exception as exc:  # noqa: BLE001 - uncaught behavior fails isolation
        failures.append(f"PRODUCTION_STAGE:UNCAUGHT_{type(exc).__name__}")
    else:
        evidence.append(
            f"PRODUCTION_STAGE:{production.decision.outcome}:"
            f"{','.join(production.decision.reason_codes)}"
        )
        if production.decision.outcome != "BLOCK":
            failures.append("PRODUCTION_STAGE_NOT_REJECTED")
    if architecture_id == K1:
        component_payloads = {
            component_id: _payload(_case(cases, component_id)) for component_id in COMPONENT_IDS
        }
        base_state = public_isolated_state()
        boundary_probes = (
            ("SECOND_TRUTH", {**base_state, "truth_source": "shadow/second-state.json"}),
            ("FORMAL_WRITE_ALLOWED", {**base_state, "formal_state_writes_allowed": True}),
            ("EXTRA_STATE_AUTHORITY", {**base_state, "second_truth": "attacker"}),
        )
        for probe_id, state in boundary_probes:
            passed, reasons, _ = evaluate_composed_evidence_package(component_payloads, state)
            evidence.append(f"COMPOSER_{probe_id}:{passed}:{','.join(reasons)}")
            if passed:
                failures.append(f"COMPOSER_{probe_id}:STATE_BOUNDARY_BYPASSED")
    return _gate(not failures, evidence, failures)


def _security_gate(root: Path, architecture_id: str) -> dict[str, Any]:
    folder = "arch_k1" if architecture_id == K1 else "arch_w1"
    source_root = root / "experiments" / "shadow_prototypes" / folder
    evidence: list[str] = []
    failures: list[str] = []
    for path in sorted(source_root.glob("*.py")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            failures.append(f"{relative}:SYMLINK")
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        forbidden = imports & FORBIDDEN_IMPORT_ROOTS
        if forbidden:
            failures.append(f"{relative}:FORBIDDEN_IMPORT:{','.join(sorted(forbidden))}")
        for marker in ("benchmark-vault", "http://", "https://"):
            if marker in source:
                failures.append(f"{relative}:FORBIDDEN_SOURCE_MARKER:{marker}")
        evidence.append(f"STATIC_SOURCE:{relative}:{_raw_sha256(path)}")
    skill_files = sorted((root / ".agents" / "skills").glob("*/SKILL.md"))
    if len(skill_files) != 1 or skill_files[0].parent.name != "cumcm-modeling-evidence":
        failures.append(f"FORMAL_SKILL_COUNT:{len(skill_files)}")
    evidence.extend(
        (
            f"FORMAL_SKILL_COUNT:{len(skill_files)}",
            "EXECUTION_SCOPE:LOCAL_STDLIB_PROJECT_CODE_ONLY",
            "PROVENANCE:PROJECT_AUTHORED_SHADOW_PROTOTYPE",
        )
    )
    return _gate(not failures, evidence, failures)


def _composition_gate(
    root: Path,
    architecture_id: str,
    cases: list[ShadowCaseInput],
    output_root: Path,
) -> dict[str, Any]:
    del output_root
    if architecture_id != K1:
        return _gate(False, ["CANDIDATE_COMPOSER:ABSENT"], ["CANDIDATE_COMPOSER_ABSENT"])
    valid_payloads = {
        component_id: _payload(_case(cases, component_id)) for component_id in COMPONENT_IDS
    }
    evidence: list[str] = []
    failures: list[str] = []
    passed, reasons, diagnostics = evaluate_composed_evidence_package(
        valid_payloads, public_isolated_state()
    )
    package = diagnostics.get("evidence_package", {})
    evidence.append(f"VALID_COMPOSITION:{passed}:{','.join(reasons)}")
    if not passed:
        failures.append("VALID_COMPONENT_SET_NOT_COMPOSED")
    repro_output = valid_payloads["hash-bound-reproducibility-manifest"]["manifest"]["output_hash"]
    claim_output = valid_payloads["claim-evidence-support-gate"]["claim"]["output_hash"]
    evidence.append(f"CROSS_COMPONENT_OUTPUT_BINDING:{repro_output}:{claim_output}")
    if passed and repro_output != claim_output:
        failures.append("K1_COMPOSITION_RUN_BINDING_MISMATCH")
    contract = json.loads((root / "contracts/modeling_to_paper.schema.json").read_text())
    missing_fields = sorted(set(contract["required"]) - set(package))
    if missing_fields:
        failures.append("K1_COMPOSITION_STRUCTURED_PACKAGE_CONTRACT_MISMATCH")
        evidence.append(f"PACKAGE_MISSING_FIELDS:{','.join(missing_fields)}")
    if diagnostics.get("evidence_package_hash") != sha256_json(package):
        failures.append("K1_COMPOSITION_PACKAGE_HASH_INVALID")
    failed_payloads = {**valid_payloads, "hash-bound-reproducibility-manifest": {}}
    failed, failed_reasons, failed_diagnostics = evaluate_composed_evidence_package(
        failed_payloads, public_isolated_state()
    )
    evidence.append(f"FAILURE_PROPAGATION:{failed}:{','.join(failed_reasons)}")
    if failed or failed_diagnostics.get("evidence_package", {}).get("status") != "REJECTED":
        failures.append("K1_COMPOSITION_FAILURE_NOT_PROPAGATED")
    stale_payloads = {
        **valid_payloads,
        "hash-bound-reproducibility-manifest": _payload(
            _case(cases, "hash-bound-reproducibility-manifest", "stale mutation")
        ),
    }
    _, stale_reasons, stale_diagnostics = evaluate_composed_evidence_package(
        stale_payloads, public_isolated_state()
    )
    stale_results = stale_diagnostics.get("evidence_package", {}).get("component_results", {})
    downstream = (
        "leakage-safe-model-comparison-gate",
        "claim-evidence-support-gate",
        "accepted-versus-done-workflow-state",
    )
    statuses = [stale_results.get(item, {}).get("status") for item in downstream]
    evidence.append(f"STALE_PROPAGATION:{','.join(str(item) for item in statuses)}")
    if statuses != ["STALE", "STALE", "STALE"]:
        failures.append("K1_COMPOSITION_STALE_PROPAGATION_REQUIRED")
    if not any("STALE" in reason for reason in stale_reasons):
        failures.append("K1_COMPOSITION_STALE_REASON_REQUIRED")
    return _gate(not failures, evidence, failures)


def evaluate_competition_gate(root: Path) -> dict[str, Any]:
    """Evaluate eight noncompensatory gates without hidden data, models, or durable run writes."""
    policy_path = root / "evals/prospective/phase-003f/minimum_competition_architecture_gate.json"
    audit_path = root / "evals/results/phase-003f/read_only_core_gate_audit.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    if tuple(policy.get("hard_gates", ())) != GATE_IDS:
        raise ValueError("COMPETITION_GATE_POLICY_MISMATCH")
    if tuple(policy.get("candidate_order", ())) != ARCHITECTURE_ORDER:
        raise ValueError("COMPETITION_CANDIDATE_ORDER_MISMATCH")
    cases = load_public_cases(root)
    architecture_results: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="cumcm-competition-gate-") as directory:
        output_root = Path(directory)
        for architecture_id in ARCHITECTURE_ORDER:
            gates = {
                GATE_IDS[0]: _malformed_gate(root, architecture_id, cases, output_root),
                GATE_IDS[1]: _workflow_gate(root, architecture_id, cases, output_root),
                GATE_IDS[2]: _claim_gate(root, architecture_id, cases, output_root),
                GATE_IDS[3]: _reproducibility_gate(root, architecture_id, cases, output_root),
                GATE_IDS[4]: _comparison_gate(root, architecture_id, cases, output_root),
                GATE_IDS[5]: _isolation_gate(root, architecture_id, cases, output_root),
                GATE_IDS[6]: _security_gate(root, architecture_id),
                GATE_IDS[7]: _composition_gate(root, architecture_id, cases, output_root),
            }
            architecture_results[architecture_id] = {
                "all_gates_pass": all(item["status"] == "PASS" for item in gates.values()),
                "gates": gates,
            }
    selected = next(
        (
            architecture_id
            for architecture_id in ARCHITECTURE_ORDER
            if architecture_results[architecture_id]["all_gates_pass"]
        ),
        None,
    )
    body = {
        "schema_version": "1.0.0",
        "decision_id": policy["decision_id"],
        "gate_id": policy["gate_id"],
        "policy_file_sha256": _raw_sha256(policy_path),
        "read_only_audit_path": audit_path.relative_to(root).as_posix(),
        "read_only_audit_sha256": _raw_sha256(audit_path),
        "selection_rule": policy["selection_rule"],
        "accepted_scope": policy["accepted_scope"],
        "architecture_results": architecture_results,
        "selected_architecture": selected,
        "decision": (
            "COMPETITION_RC_IMPLEMENTATION_ONLY"
            if selected
            else "FAST_TRACK_IMPLEMENTATION_BLOCKED"
        ),
        "deferred_not_passed": policy["deferred_not_passed"],
        "real_model_starts": 0,
        "hidden_benchmark_accesses": 0,
        "third_party_executions": 0,
        "majority_vote_used": False,
        "prototype_case_evaluations": 118,
        "candidate_composition_evaluations": 6,
    }
    return {**body, "decision_hash": sha256_json(body)}


__all__ = ["ARCHITECTURE_ORDER", "GATE_IDS", "evaluate_competition_gate"]
