"""Competition RC1 readmission against the unchanged eight public hard gates."""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import math
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from experiments.shadow_prototypes import COMPONENT_IDS
from experiments.shadow_prototypes.common.interface import ShadowContext, sha256_json, thaw
from experiments.shadow_prototypes.common.public_cases import (
    load_public_cases,
    public_isolated_state,
)
from experiments.shadow_prototypes.common.r1_interface import (
    R1CaseInput,
    boundary_json,
    sha256_boundary_json,
)

from .competition_gate import GATE_IDS, K1, W1
from .runner_r1 import run_case_r1

DECISION_ID = "DECISION-COMPETITION-RC1-ARCHITECTURE-003F-R1"
OLD_DECISION_HASH = "2ed22c0e6ba08159077ae891bfb310947fa007e84dd38fdde2af54beeef25b5d"
ARCHITECTURE_ORDER = (K1, W1)
REVISION_IDS = {K1: "ARCH-K1-R1", W1: "ARCH-W1-R1"}
FORBIDDEN_IMPORT_ROOTS = {"aiohttp", "httpx", "requests", "socket", "subprocess", "urllib"}


def _raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_hash(root: Path, architecture_id: str) -> str:
    folder = "arch_k1" if architecture_id == K1 else "arch_w1"
    digest = hashlib.sha256()
    for path in sorted((root / "experiments/shadow_prototypes" / folder).glob("*r1.py")):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _base(cases: list[Any], component_id: str, case_class: str = "valid control") -> Any:
    return next(
        case
        for case in cases
        if case.component_id == component_id and case.case_class == case_class
    )


def _payload(
    cases: list[Any], component_id: str, case_class: str = "valid control"
) -> dict[str, Any]:
    return copy.deepcopy(thaw(_base(cases, component_id, case_class).payload))


def _context(
    output_root: Path,
    architecture_id: str,
    case_id: str,
    *,
    stage: Any = "PUBLIC_VALIDATION",
    enabled_components: Any = COMPONENT_IDS,
) -> ShadowContext:
    return ShadowContext(
        run_id=f"003F-R1-{architecture_id}-{case_id}",
        architecture_id=architecture_id,
        stage=stage,
        output_dir=output_root / architecture_id / case_id,
        timeout_seconds=30,
        operation_budget=100,
        enabled_components=enabled_components,
    )


def _observation(
    root: Path,
    output_root: Path,
    architecture_id: str,
    case_id: str,
    component_id: str,
    payload: Mapping[str, Any],
    expected: str,
    *,
    isolated_state: Any | None = None,
    context: Any = ...,
    stage: Any = "PUBLIC_VALIDATION",
    enabled_components: Any = COMPONENT_IDS,
) -> dict[str, Any]:
    unhandled = False
    result = None
    unchanged = False
    try:
        case = R1CaseInput(
            case_id=case_id,
            component_id=component_id,
            payload=payload,
            input_hash=sha256_boundary_json(payload),
            case_class=f"competition-r1:{case_id}",
        )
        actual_context = (
            _context(
                output_root,
                architecture_id,
                case_id,
                stage=stage,
                enabled_components=enabled_components,
            )
            if context is ...
            else context
        )
        result, unchanged = run_case_r1(
            root,
            architecture_id,
            case,
            public_isolated_state() if isolated_state is None else isolated_state,
            actual_context,
            persist=False,
        )
    except Exception as exc:  # noqa: BLE001 - an uncaught public boundary error fails the Gate
        unhandled = True
        outcome = f"UNHANDLED_{type(exc).__name__}"
        reasons = ["R1_UNHANDLED_PUBLIC_EXCEPTION"]
        output_hash = None
    else:
        outcome = result.decision.outcome
        reasons = list(result.decision.reason_codes)
        output_hash = result.result_hash
    candidate_exception = any(code == "R1_CANDIDATE_EXCEPTION_FAIL_CLOSED" for code in reasons)
    passed = bool(
        not unhandled
        and not candidate_exception
        and unchanged
        and outcome == expected
        and (expected != "BLOCK" or reasons)
    )
    return {
        "case_id": case_id,
        "expected": expected,
        "actual": outcome,
        "reason_codes": sorted(set(reasons)),
        "input_unchanged": unchanged,
        "unhandled_exception": unhandled,
        "output_hash": output_hash,
        "pass": passed,
    }


def _gate(observations: list[dict[str, Any]]) -> dict[str, Any]:
    failures = [item for item in observations if not item["pass"]]
    body = {
        "status": "PASS" if not failures else "FAIL",
        "case_count": len(observations),
        "failing_case_ids": [item["case_id"] for item in failures],
        "reason_codes": sorted(
            {reason for item in failures for reason in item.get("reason_codes", ())}
        ),
        "input_immutability": all(item["input_unchanged"] for item in observations),
        "unhandled_exceptions": sum(bool(item["unhandled_exception"]) for item in observations),
        "cases": observations,
    }
    return {**body, "output_hash": sha256_json(body)}


def _with(payload: Mapping[str, Any], mutate: Any) -> dict[str, Any]:
    candidate = copy.deepcopy(dict(payload))
    mutate(candidate)
    return candidate


def _g1(root: Path, output_root: Path, architecture_id: str, cases: list[Any]) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    primary_fields = {
        "accepted-versus-done-workflow-state": "evidenced_stages",
        "claim-evidence-support-gate": "claim",
        "hash-bound-reproducibility-manifest": "manifest",
        "leakage-safe-model-comparison-gate": "splits",
    }
    for component_id, field in primary_fields.items():
        valid = _payload(cases, component_id)
        for suffix, probe in (
            ("EMPTY_OBJECT", {}),
            ("NULL_FIELD", {**valid, field: None}),
            ("WRONG_TYPE", {**valid, field: 17}),
        ):
            observations.append(
                _observation(
                    root,
                    output_root,
                    architecture_id,
                    f"G1-{component_id}-{suffix}",
                    component_id,
                    probe,
                    "BLOCK",
                )
            )
    comparison = _payload(cases, "leakage-safe-model-comparison-gate")
    numerical: list[tuple[str, dict[str, Any]]] = [
        ("EMPTY_CANDIDATE_SET", {**comparison, "validation_scores": {}}),
        ("EMPTY_SPLITS", {**comparison, "splits": []}),
        ("MISSING_SPLITS", _with(comparison, lambda item: item.pop("splits"))),
        (
            "MALFORMED_NESTED_SPLIT",
            {**comparison, "splits": {"train": [{}], "validation": ["v"], "test": ["t"]}},
        ),
        ("NAN_SCORE", {**comparison, "validation_scores": {"a": math.nan, "b": 0.7}}),
        ("POSITIVE_INF_SCORE", {**comparison, "validation_scores": {"a": math.inf, "b": 0.7}}),
        ("NEGATIVE_INF_SCORE", {**comparison, "validation_scores": {"a": -math.inf, "b": 0.7}}),
        ("BOOL_SCORE", {**comparison, "validation_scores": {"a": True, "b": 0.7}}),
        ("NUMERIC_STRING_SCORE", {**comparison, "validation_scores": {"a": "0.8", "b": 0.7}}),
        ("EMPTY_TIE_POLICY", {**comparison, "ordered_tie_keys": []}),
        ("MISSING_METRIC", _with(comparison, lambda item: item.pop("metric_direction"))),
        ("MALFORMED_ATTEMPT_LEDGER", {**comparison, "attempts": [{"bad": []}]}),
    ]
    for suffix, probe in numerical:
        observations.append(
            _observation(
                root,
                output_root,
                architecture_id,
                f"G1-{suffix}",
                "leakage-safe-model-comparison-gate",
                probe,
                "BLOCK",
            )
        )
    workflow = _payload(cases, "accepted-versus-done-workflow-state")
    for suffix, kwargs in (
        ("MALFORMED_CONTEXT_STAGE", {"stage": []}),
        ("MALFORMED_ENABLED_COMPONENTS", {"enabled_components": None}),
        ("NULL_CONTEXT", {"context": None}),
        ("WRONG_TYPE_CONTEXT", {"context": {"stage": "PUBLIC_VALIDATION"}}),
    ):
        observations.append(
            _observation(
                root,
                output_root,
                architecture_id,
                f"G1-{suffix}",
                "accepted-versus-done-workflow-state",
                workflow,
                "BLOCK",
                **kwargs,
            )
        )
    return _gate(observations)


def _g2(root: Path, output_root: Path, architecture_id: str, cases: list[Any]) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    component_id = "accepted-versus-done-workflow-state"
    for case_class, expected in (
        ("valid control", "PASS"),
        ("missing evidence", "BLOCK"),
        ("stale mutation", "BLOCK"),
        ("gaming attempt", "BLOCK"),
    ):
        observations.append(
            _observation(
                root,
                output_root,
                architecture_id,
                f"G2-{case_class.replace(' ', '-').upper()}",
                component_id,
                _payload(cases, component_id, case_class),
                expected,
            )
        )
    valid = _payload(cases, component_id)
    records = valid["evidence_records"]
    for suffix, length in (("COMMAND_DONE_ONLY", 3), ("ARTIFACT_EXISTS_ONLY", 4)):
        stages = valid["evidenced_stages"][:length]
        probe = {
            **valid,
            "evidenced_stages": stages,
            "evidence_records": {key: records[key] for key in stages},
        }
        observations.append(
            _observation(
                root, output_root, architecture_id, f"G2-{suffix}", component_id, probe, "BLOCK"
            )
        )
    return _gate(observations)


def _g3(root: Path, output_root: Path, architecture_id: str, cases: list[Any]) -> dict[str, Any]:
    component_id = "claim-evidence-support-gate"
    observations = [
        _observation(
            root,
            output_root,
            architecture_id,
            "G3-VALID",
            component_id,
            _payload(cases, component_id),
            "PASS",
        )
    ]
    for case_class in ("missing evidence", "stale mutation", "gaming attempt"):
        observations.append(
            _observation(
                root,
                output_root,
                architecture_id,
                f"G3-{case_class.replace(' ', '-').upper()}",
                component_id,
                _payload(cases, component_id, case_class),
                "BLOCK",
            )
        )
    valid = _payload(cases, component_id)
    probes = [
        (
            "UNBOUND_VERIFIED_RUN_DECISION",
            _with(valid, lambda item: item["verified_run_manifest"].update(decision_id="attacker")),
        ),
        (
            "MANIFEST_HASH_MISMATCH",
            _with(valid, lambda item: item["verified_run_manifest"].update(artifact_hash="f" * 64)),
        ),
        ("CLAIM_OLD_RUN", _with(valid, lambda item: item["claim"].update(run_id="old-run"))),
        ("SUPERSEDED_RUN", _with(valid, lambda item: item["evidence"][0].update(superseded=True))),
        ("OTHER_OUTPUT", _with(valid, lambda item: item["claim"].update(output_hash="e" * 64))),
        (
            "CONTRADICTION",
            _with(valid, lambda item: item["evidence"][0].update(contradicts=["claim-1"])),
        ),
        ("STALE_EVIDENCE", _with(valid, lambda item: item["evidence"][0].update(current=False))),
        ("OVERBROAD_CLAIM", _with(valid, lambda item: item["claim"].update(scope="ALL_PROBLEMS"))),
        (
            "UNSUPPORTED_CLAIM",
            _with(valid, lambda item: item["claim"].update(proposition="Unsupported conclusion")),
        ),
    ]
    for suffix, probe in probes:
        observations.append(
            _observation(
                root, output_root, architecture_id, f"G3-{suffix}", component_id, probe, "BLOCK"
            )
        )
    return _gate(observations)


def _g4(root: Path, output_root: Path, architecture_id: str, cases: list[Any]) -> dict[str, Any]:
    component_id = "hash-bound-reproducibility-manifest"
    observations = [
        _observation(
            root,
            output_root,
            architecture_id,
            "G4-VALID",
            component_id,
            _payload(cases, component_id),
            "PASS",
        )
    ]
    for case_class in ("missing evidence", "stale mutation", "gaming attempt"):
        observations.append(
            _observation(
                root,
                output_root,
                architecture_id,
                f"G4-{case_class.replace(' ', '-').upper()}",
                component_id,
                _payload(cases, component_id, case_class),
                "BLOCK",
            )
        )
    valid = _payload(cases, component_id)
    sensitive = (
        ("PRIVATE_KEY", {"private_key": "synthetic"}),
        ("PRIVATE_DASH_KEY", {"private-key": "synthetic"}),
        ("PRIVATE_UPPER_KEY", {"PRIVATE_KEY": "synthetic"}),
        ("REFRESH_TOKEN", {"refresh_token": "synthetic"}),
        ("BEARER_TOKEN", {"bearer-token": "synthetic"}),
        ("ACCESS_TOKEN", {"accessToken": "synthetic"}),
        ("PASSWORD", {"password": "synthetic"}),
        ("SECRET", {"client_secret": "synthetic"}),
        ("UNC_PATH", {"scratch": "\\\\server\\private\\run"}),
        ("WINDOWS_PATH", {"scratch": "C:\\private\\run"}),
        ("POSIX_PATH", {"scratch": "/private/run"}),
        ("HOME_PATH", {"scratch": "~/private/run"}),
        ("CREDENTIAL_URL", {"source": "https://user:pass@example.invalid/data"}),
        ("ENV_SECRET", {"environment": {"API_KEY": "synthetic"}}),
        ("NESTED_SECRET", {"nested": {"credentials": {"refresh-token": "synthetic"}}}),
        ("LIST_SECRET", {"items": [{"password": "synthetic"}]}),
        ("UNKNOWN_FREEZE_HASH", {"freeze_hash": "unknown"}),
        ("ARBITRARY_FREEZE_HASH", {"freeze_hash": "a" * 64}),
    )
    for suffix, extra in sensitive:
        observations.append(
            _observation(
                root,
                output_root,
                architecture_id,
                f"G4-{suffix}",
                component_id,
                {**valid, **extra},
                "BLOCK",
            )
        )
    for outcome in ("FAILED", "PARTIAL", "SUPERSEDED", "STALE"):
        probe = _with(
            valid,
            lambda item, value=outcome: (
                item["manifest"].update(outcome=value),
                item["trusted_capture"].update(outcome=value),
            ),
        )
        observations.append(
            _observation(
                root,
                output_root,
                architecture_id,
                f"G4-OUTCOME-{outcome}",
                component_id,
                probe,
                "BLOCK",
            )
        )
    return _gate(observations)


def _g5(root: Path, output_root: Path, architecture_id: str, cases: list[Any]) -> dict[str, Any]:
    component_id = "leakage-safe-model-comparison-gate"
    observations = [
        _observation(
            root,
            output_root,
            architecture_id,
            "G5-VALID",
            component_id,
            _payload(cases, component_id),
            "PASS",
        )
    ]
    for case_class in ("missing evidence", "stale mutation", "gaming attempt"):
        observations.append(
            _observation(
                root,
                output_root,
                architecture_id,
                f"G5-{case_class.replace(' ', '-').upper()}",
                component_id,
                _payload(cases, component_id, case_class),
                "BLOCK",
            )
        )
    valid = _payload(cases, component_id)
    probes: list[tuple[str, dict[str, Any]]] = [
        ("NUMERIC_STRING_SCORE", {**valid, "validation_scores": {"a": "0.8", "b": 0.7}}),
        ("BOOL_SCORE", {**valid, "validation_scores": {"a": True, "b": 0.7}}),
        ("NAN_SCORE", {**valid, "validation_scores": {"a": math.nan, "b": 0.7}}),
        ("INF_SCORE", {**valid, "validation_scores": {"a": math.inf, "b": 0.7}}),
        (
            "UNTRUSTED_FREEZE_HASH",
            {**valid, "candidate_freeze_hash": "a" * 64, "metric_freeze_hash": "b" * 64},
        ),
        ("CANDIDATE_SET_NOT_FROZEN", {**valid, "validation_scores": {"a": 0.8}}),
        ("METRIC_NOT_FROZEN", {**valid, "metric_freeze_hash": "c" * 64}),
        ("BASELINE_MISSING", {**valid, "baselines": ["naive"]}),
        ("TEST_FEATURE_SELECTION", {**valid, "test_used_for_feature_selection": True}),
        ("TEST_THRESHOLD_SELECTION", {**valid, "test_used_for_threshold_selection": True}),
        ("FUTURE_LEAKAGE", {**valid, "future_feature": True}),
        ("GROUP_LEAKAGE", {**valid, "group_overlap": True}),
        ("TARGET_LEAKAGE", {**valid, "target_feature": True}),
        ("TIME_LEAKAGE", {**valid, "time_order_valid": False}),
        (
            "UNAUTHORIZED_TEST_ACCESS",
            _with(valid, lambda item: item["access_events"][0].update(run_id="attacker")),
        ),
        (
            "MULTIPLE_TEST_ACCESS",
            _with(
                valid,
                lambda item: item["access_events"].append(copy.deepcopy(item["access_events"][0])),
            ),
        ),
        (
            "RETRY_UNTIL_SUCCESS",
            _with(
                valid,
                lambda item: item["attempts"].append(
                    {
                        **item["attempts"][0],
                        "run_id": "retry",
                        "retry": True,
                        "infrastructure_failure": False,
                    }
                ),
            ),
        ),
        ("SELECTION_MISMATCH", {**valid, "selected_candidate_id": "b"}),
    ]
    for outcome in ("FAILED", "PARTIAL", "SUPERSEDED"):
        probes.append(
            (
                f"{outcome}_ATTEMPT_SCORED",
                _with(
                    valid,
                    lambda item, value=outcome: item["attempts"][0].update(
                        outcome=value, failure_class="MODEL_FAILURE"
                    ),
                ),
            )
        )
    for suffix, probe in probes:
        observations.append(
            _observation(
                root, output_root, architecture_id, f"G5-{suffix}", component_id, probe, "BLOCK"
            )
        )
    return _gate(observations)


def _g6(root: Path, output_root: Path, architecture_id: str, cases: list[Any]) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    for component_id in COMPONENT_IDS:
        observations.append(
            _observation(
                root,
                output_root,
                architecture_id,
                f"G6-VALID-{component_id}",
                component_id,
                _payload(cases, component_id),
                "PASS",
            )
        )
    workflow = _payload(cases, "accepted-versus-done-workflow-state")
    for stage in ("PRODUCTION", "FORMAL"):
        observations.append(
            _observation(
                root,
                output_root,
                architecture_id,
                f"G6-{stage}-STAGE",
                "accepted-versus-done-workflow-state",
                workflow,
                "BLOCK",
                stage=stage,
            )
        )
    base_state = public_isolated_state()
    states = (
        ("SECOND_TRUTH", {**base_state, "truth_source": "shadow/second-state.json"}),
        ("FORMAL_WRITE", {**base_state, "formal_state_writes_allowed": True}),
        ("EXTRA_AUTHORITY", {**base_state, "state_authority": "attacker"}),
        ("UNKNOWN_WRITER", {**base_state, "writer": "attacker"}),
        ("MISSING_ISOLATED_BINDING", {}),
        ("FORMAL_STATE_PATH", {**base_state, "formal_state_path": "state/project_state.json"}),
    )
    for suffix, state in states:
        observations.append(
            _observation(
                root,
                output_root,
                architecture_id,
                f"G6-{suffix}",
                "accepted-versus-done-workflow-state",
                workflow,
                "BLOCK",
                isolated_state=state,
            )
        )
    return _gate(observations)


def _g7(root: Path, architecture_id: str) -> dict[str, Any]:
    folder = "arch_k1" if architecture_id == K1 else "arch_w1"
    observations: list[dict[str, Any]] = []
    paths = sorted((root / "experiments/shadow_prototypes" / folder).glob("*r1.py"))
    reasons: list[str] = []
    source_hashes: dict[str, str] = {}
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        forbidden = sorted(imports & FORBIDDEN_IMPORT_ROOTS)
        if forbidden:
            reasons.append("R1_FORBIDDEN_IMPORT")
        source = path.read_text(encoding="utf-8")
        if "benchmark-vault" in source or "http://" in source:
            reasons.append("R1_FORBIDDEN_SOURCE_MARKER")
        source_hashes[path.name] = _raw_sha256(path)
    if not paths:
        reasons.append("R1_REVISION_SOURCE_ABSENT")
    observations.append(
        {
            "case_id": "G7-STATIC-REVISION-SOURCES",
            "expected": "PASS",
            "actual": "PASS" if not reasons else "BLOCK",
            "reason_codes": sorted(set(reasons)),
            "input_unchanged": True,
            "unhandled_exception": False,
            "output_hash": sha256_json(source_hashes),
            "pass": not reasons,
        }
    )
    skill_files = sorted((root / ".agents/skills").glob("*/SKILL.md"))
    skill_ok = len(skill_files) == 1 and skill_files[0].parent.name == "cumcm-modeling-evidence"
    observations.append(
        {
            "case_id": "G7-FORMAL-SKILL-COUNT",
            "expected": "PASS",
            "actual": "PASS" if skill_ok else "BLOCK",
            "reason_codes": [] if skill_ok else ["R1_FORMAL_SKILL_COUNT_INVALID"],
            "input_unchanged": True,
            "unhandled_exception": False,
            "output_hash": sha256_json([path.as_posix() for path in skill_files]),
            "pass": skill_ok,
        }
    )
    return _gate(observations)


def _normalized_composition(cases: list[Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    payloads = {component: _payload(cases, component) for component in COMPONENT_IDS}
    state = copy.deepcopy(public_isolated_state())
    output_hash = payloads["hash-bound-reproducibility-manifest"]["manifest"]["output_hash"]
    input_hash = payloads["hash-bound-reproducibility-manifest"]["manifest"]["input_hash"]
    claim_payload = payloads["claim-evidence-support-gate"]
    claim_payload["claim"]["output_hash"] = output_hash
    claim_payload["claim"]["input_hash"] = input_hash
    evidence = claim_payload["evidence"][0]
    evidence["output_hash"] = output_hash
    evidence["input_hash"] = input_hash
    evidence["artifact_body"]["output_hash"] = output_hash
    evidence["artifact_body"]["input_hash"] = input_hash
    evidence["artifact_hash"] = sha256_json(evidence["artifact_body"])
    evidence["registry_hash"] = sha256_json(
        {"locator": evidence["locator"], "artifact_hash": evidence["artifact_hash"]}
    )
    state["trusted_artifact_hashes"][evidence["locator"]] = evidence["artifact_hash"]
    state["trusted_run_bindings"]["run-public-1"]["output_hash"] = output_hash
    state["trusted_run_bindings"]["run-public-1"]["input_hash"] = input_hash
    return payloads, state


def _compose(architecture_id: str, payloads: Any, state: Any) -> tuple[Any, Any, Any]:
    if architecture_id == K1:
        from experiments.shadow_prototypes.arch_k1.revision_r1 import (
            evaluate_composed_evidence_package_r1,
        )

        return evaluate_composed_evidence_package_r1(payloads, state)
    from experiments.shadow_prototypes.arch_w1.composer_r1 import compose_evidence_package

    return compose_evidence_package(payloads, state)


def _composition_observation(
    architecture_id: str,
    case_id: str,
    payloads: Any,
    state: Any,
    expected: bool,
    contract_required: set[str],
    *,
    require_stale: bool = False,
) -> dict[str, Any]:
    before = boundary_json({"payloads": payloads, "state": state})
    unhandled = False
    reasons: list[str] = []
    try:
        passed, result_reasons, diagnostics = _compose(architecture_id, payloads, state)
        reasons = list(result_reasons)
        package = diagnostics.get("evidence_package", {})
        package_hash = diagnostics.get("evidence_package_hash")
        unchanged = before == boundary_json({"payloads": payloads, "state": state})
        checks = [passed is expected, unchanged]
        if expected:
            checks.extend(
                [
                    isinstance(package, Mapping),
                    not (contract_required - set(package)),
                    set(package) <= contract_required,
                    package_hash == sha256_json(package),
                    all(
                        str(item).startswith("MACHINE_") for item in package.get("approved_by", ())
                    ),
                ]
            )
        if require_stale:
            component_results = diagnostics.get("component_results") or diagnostics.get(
                "evidence_package", {}
            ).get("component_results", {})
            downstream = (
                "leakage-safe-model-comparison-gate",
                "claim-evidence-support-gate",
                "accepted-versus-done-workflow-state",
            )
            checks.append(
                all(component_results.get(item, {}).get("status") == "STALE" for item in downstream)
            )
            checks.append(
                any(
                    result.get("dependency_chain")
                    for result in component_results.values()
                    if isinstance(result, Mapping)
                )
            )
        case_pass = all(checks)
        output_hash = package_hash or sha256_json(diagnostics)
        actual = "PASS" if passed else "BLOCK"
    except Exception as exc:  # noqa: BLE001 - uncaught composition is Gate evidence
        unhandled = True
        unchanged = before == boundary_json({"payloads": payloads, "state": state})
        case_pass = False
        output_hash = None
        actual = f"UNHANDLED_{type(exc).__name__}"
        reasons = ["R1_UNHANDLED_COMPOSITION_EXCEPTION"]
    return {
        "case_id": case_id,
        "expected": "PASS" if expected else "BLOCK",
        "actual": actual,
        "reason_codes": sorted(set(reasons)),
        "input_unchanged": unchanged,
        "unhandled_exception": unhandled,
        "output_hash": output_hash,
        "pass": case_pass,
    }


def _g8(root: Path, architecture_id: str, cases: list[Any]) -> dict[str, Any]:
    contract = json.loads(
        (root / "contracts/modeling_to_paper.schema.json").read_text(encoding="utf-8")
    )
    required = set(contract["required"])
    payloads, state = _normalized_composition(cases)
    original = {component: _payload(cases, component) for component in COMPONENT_IDS}
    missing = {
        key: value for key, value in payloads.items() if key != "claim-evidence-support-gate"
    }
    stale = copy.deepcopy(payloads)
    stale["hash-bound-reproducibility-manifest"] = _payload(
        cases, "hash-bound-reproducibility-manifest", "stale mutation"
    )
    bad_state = {**state, "formal_state_writes_allowed": True}
    observations = [
        _composition_observation(
            architecture_id, "G8-VALID-LINEAGE", payloads, state, True, required
        ),
        _composition_observation(
            architecture_id,
            "G8-OUTPUT-HASH-MISMATCH",
            original,
            public_isolated_state(),
            False,
            required,
        ),
        _composition_observation(
            architecture_id, "G8-MISSING-COMPONENT", missing, state, False, required
        ),
        _composition_observation(
            architecture_id, "G8-UPSTREAM-STALE", stale, state, False, required, require_stale=True
        ),
        _composition_observation(
            architecture_id, "G8-FORMAL-WRITE", payloads, bad_state, False, required
        ),
    ]
    return _gate(observations)


def evaluate_competition_gate_r1(root: Path) -> dict[str, Any]:
    """Evaluate new K1/W1 revisions without changing the frozen Gate policy or old result."""
    policy_path = root / "evals/prospective/phase-003f/minimum_competition_architecture_gate.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    if tuple(policy.get("hard_gates", ())) != GATE_IDS:
        raise ValueError("COMPETITION_R1_GATE_POLICY_MISMATCH")
    if tuple(policy.get("candidate_order", ())) != ARCHITECTURE_ORDER:
        raise ValueError("COMPETITION_R1_CANDIDATE_ORDER_MISMATCH")
    cases = load_public_cases(root)
    architecture_results: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="cumcm-competition-r1-") as directory:
        output_root = Path(directory)
        for architecture_id in ARCHITECTURE_ORDER:
            gates = {
                GATE_IDS[0]: _g1(root, output_root, architecture_id, cases),
                GATE_IDS[1]: _g2(root, output_root, architecture_id, cases),
                GATE_IDS[2]: _g3(root, output_root, architecture_id, cases),
                GATE_IDS[3]: _g4(root, output_root, architecture_id, cases),
                GATE_IDS[4]: _g5(root, output_root, architecture_id, cases),
                GATE_IDS[5]: _g6(root, output_root, architecture_id, cases),
                GATE_IDS[6]: _g7(root, architecture_id),
                GATE_IDS[7]: _g8(root, architecture_id, cases),
            }
            architecture_results[architecture_id] = {
                "revision_id": REVISION_IDS[architecture_id],
                "tree_hash": _tree_hash(root, architecture_id),
                "all_gates_pass": all(gate["status"] == "PASS" for gate in gates.values()),
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
    case_count = sum(
        gate["case_count"]
        for result in architecture_results.values()
        for gate in result["gates"].values()
    )
    body = {
        "schema_version": "1.0.0",
        "decision_id": DECISION_ID,
        "supersedes_decision_id": None,
        "preserves_old_decision_id": "DECISION-COMPETITION-MVP-ARCHITECTURE-003F",
        "preserves_old_decision_hash": OLD_DECISION_HASH,
        "gate_id": policy["gate_id"],
        "policy_file_sha256": _raw_sha256(policy_path),
        "selection_rule": policy["selection_rule"],
        "accepted_scope": "COMPETITION_RC_IMPLEMENTATION_ONLY",
        "architecture_results": architecture_results,
        "selected_architecture": selected,
        "decision": "COMPETITION_RC_IMPLEMENTATION_ONLY"
        if selected
        else "COMPETITION_RC_REPAIR_BLOCKED",
        "deferred_not_passed": [
            "full sealed Stage 1",
            "Stage 2 model-in-loop comparison",
            "full ablation",
            "external validity",
            "production fitness",
            "monetary cost",
        ],
        "case_evaluations": case_count,
        "real_model_starts": 0,
        "hidden_benchmark_accesses": 0,
        "historical_answer_accesses": 0,
        "third_party_executions": 0,
        "majority_vote_used": False,
    }
    return {**body, "decision_hash": sha256_json(body)}


__all__ = ["ARCHITECTURE_ORDER", "DECISION_ID", "evaluate_competition_gate_r1"]
