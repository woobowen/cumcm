"""Competition-R1 boundary validators for the workflow-only W1 architecture.

This revision deliberately remains a stateless adapter around the existing W1
checklists.  It adds strict boundary validation and trusted-ledger checks, but
does not own persistence or a formal state transition.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from numbers import Real
from pathlib import Path
from typing import Any

from experiments.shadow_prototypes import COMPONENT_IDS
from experiments.shadow_prototypes.common.interface import (
    ShadowCaseInput,
    ShadowContext,
    ShadowDecision,
    ShadowEvidence,
    ShadowRunResult,
    build_result,
    deep_freeze,
    sha256_json,
)
from experiments.shadow_prototypes.common.r1_interface import R1CaseInput

from .guards import (
    claim_checklist,
    comparison_checklist,
    reproducibility_checklist,
    workflow_checklist,
)

ARCHITECTURE_ID = "ARCH-W1-WORKFLOW-ONLY-GUARDS"
REVISION_ID = "ARCH-W1-R1"
ALLOWED_SHADOW_STAGES = frozenset({"PUBLIC_VALIDATION"})
TERMINAL_ATTEMPT_OUTCOMES = frozenset({"SUCCESS", "FAILED", "PARTIAL", "SUPERSEDED", "STALE"})
NON_SUCCESS_ATTEMPT_OUTCOMES = TERMINAL_ATTEMPT_OUTCOMES - {"SUCCESS"}
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")
URI_WITH_CREDENTIALS = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://[^/@\s]+:[^/@\s]+@")
ENV_REFERENCE = re.compile(r"(?:\$\{?|%)([A-Za-z_][A-Za-z0-9_-]*)(?:\}|%)?")
SENSITIVE_KEYS = frozenset(
    {
        "api_key",
        "access_token",
        "bearer_token",
        "refresh_token",
        "private_key",
        "password",
        "passwd",
        "credential",
        "credentials",
        "secret",
        "client_secret",
        "browser_state",
        "hidden_reasoning",
        "raw_trace",
        "private_path",
    }
)
FORBIDDEN_STATE_AUTHORITY_KEYS = frozenset(
    {
        "additional_state_authority",
        "formal_state_authority",
        "formal_state_path",
        "formal_state_writer",
        "project_state_writer",
        "second_state_truth",
        "second_truth",
        "state_authority",
        "writer",
    }
)


def _normalized_key(value: Any) -> str:
    camel_split = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", str(value))
    return re.sub(r"[^a-z0-9]+", "_", camel_split.casefold()).strip("_")


def _valid_hash(value: Any) -> bool:
    return isinstance(value, str) and bool(HEX_64.fullmatch(value))


def _strict_real(value: Any) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(float(value))


def _sensitive_string(value: str) -> bool:
    if value.startswith(("/", "~", "\\\\")) or WINDOWS_ABSOLUTE.match(value):
        return True
    if URI_WITH_CREDENTIALS.match(value) or "credential=" in value.casefold():
        return True
    return any(_normalized_key(match) in SENSITIVE_KEYS for match in ENV_REFERENCE.findall(value))


def _contains_sensitive_value(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _normalized_key(key) in SENSITIVE_KEYS or _contains_sensitive_value(item):
                return True
        return False
    if isinstance(value, (list, tuple)):
        return any(_contains_sensitive_value(item) for item in value)
    return isinstance(value, str) and _sensitive_string(value)


def _state_boundary_reasons(isolated_state: Any) -> list[str]:
    if not isinstance(isolated_state, Mapping):
        return ["W1_R1_ISOLATED_STATE_INVALID"]
    reasons: list[str] = []
    if isolated_state.get("truth_source") != "state/project_state.json":
        reasons.append("W1_R1_SINGLE_STATE_TRUTH_REQUIRED")
    if isolated_state.get("formal_state_writes_allowed") is not False:
        reasons.append("W1_R1_FORMAL_STATE_WRITE_PROHIBITED")
    normalized = {_normalized_key(key) for key in isolated_state}
    if normalized & FORBIDDEN_STATE_AUTHORITY_KEYS:
        reasons.append("W1_R1_EXTRA_STATE_AUTHORITY_REJECTED")
    return reasons


def _context_reasons(run_context: Any) -> list[str]:
    if not isinstance(run_context, ShadowContext):
        return ["W1_R1_CONTEXT_INVALID"]
    reasons: list[str] = []
    if not isinstance(run_context.run_id, str) or not run_context.run_id:
        reasons.append("W1_R1_CONTEXT_RUN_ID_INVALID")
    if run_context.architecture_id != ARCHITECTURE_ID:
        reasons.append("W1_R1_CONTEXT_ARCHITECTURE_MISMATCH")
    if not isinstance(run_context.stage, str) or run_context.stage not in ALLOWED_SHADOW_STAGES:
        reasons.append("W1_R1_CONTEXT_STAGE_PROHIBITED")
    if not isinstance(run_context.output_dir, Path):
        reasons.append("W1_R1_CONTEXT_OUTPUT_DIR_INVALID")
    else:
        prohibited_parts = {".agents", "state", "benchmark" + "-" + "vault"}
        if prohibited_parts & set(run_context.output_dir.parts):
            reasons.append("W1_R1_CONTEXT_OUTPUT_TARGET_PROHIBITED")
    if (
        not isinstance(run_context.timeout_seconds, int)
        or isinstance(run_context.timeout_seconds, bool)
        or run_context.timeout_seconds <= 0
    ):
        reasons.append("W1_R1_CONTEXT_TIMEOUT_INVALID")
    if (
        not isinstance(run_context.operation_budget, int)
        or isinstance(run_context.operation_budget, bool)
        or run_context.operation_budget <= 0
    ):
        reasons.append("W1_R1_CONTEXT_OPERATION_BUDGET_INVALID")
    enabled = run_context.enabled_components
    if (
        not isinstance(enabled, tuple)
        or any(not isinstance(item, str) for item in enabled)
        or len(enabled) != len(set(enabled))
        or not set(enabled).issubset(COMPONENT_IDS)
    ):
        reasons.append("W1_R1_CONTEXT_ENABLED_COMPONENTS_INVALID")
    return reasons


def _safe_context(run_context: Any) -> ShadowContext:
    if isinstance(run_context, ShadowContext):
        run_id = run_context.run_id if isinstance(run_context.run_id, str) else "W1-R1-BLOCKED"
        output_dir = (
            run_context.output_dir if isinstance(run_context.output_dir, Path) else Path(".")
        )
    else:
        run_id = "W1-R1-BLOCKED"
        output_dir = Path(".")
    return ShadowContext(
        run_id=run_id or "W1-R1-BLOCKED",
        architecture_id=ARCHITECTURE_ID,
        stage="PUBLIC_VALIDATION",
        output_dir=output_dir,
        timeout_seconds=1,
        operation_budget=1,
        enabled_components=(),
    )


def _workflow_boundary_reasons(payload: Any) -> list[str]:
    if not isinstance(payload, Mapping):
        return ["W1_R1_WORKFLOW_PAYLOAD_INVALID"]
    reasons: list[str] = []
    evidenced = payload.get("evidenced_stages")
    if not isinstance(evidenced, (list, tuple)) or any(
        not isinstance(item, str) for item in evidenced
    ):
        reasons.append("W1_R1_WORKFLOW_STAGE_LEDGER_INVALID")
    if not isinstance(payload.get("requested_state"), str):
        reasons.append("W1_R1_WORKFLOW_REQUESTED_STATE_INVALID")
    if not isinstance(payload.get("evidence_records"), Mapping):
        reasons.append("W1_R1_WORKFLOW_EVIDENCE_RECORDS_INVALID")
    if not isinstance(payload.get("dependency_graph"), Mapping):
        reasons.append("W1_R1_WORKFLOW_DEPENDENCY_GRAPH_INVALID")
    changed = payload.get("changed_nodes")
    if not isinstance(changed, (list, tuple)) or any(not isinstance(item, str) for item in changed):
        reasons.append("W1_R1_WORKFLOW_CHANGED_NODES_INVALID")
    return reasons


def _legacy_expected_decision_id(run_id: str) -> str:
    return f"manifest-decision:{run_id}"


def _verified_decision_reasons(
    manifest: Any,
    isolated_state: Mapping[str, Any],
    *,
    claim: Mapping[str, Any] | None = None,
) -> list[str]:
    if not isinstance(manifest, Mapping):
        return ["W1_R1_VERIFIED_RUN_DECISION_INVALID"]
    reasons: list[str] = []
    run_id = manifest.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        return ["W1_R1_VERIFIED_RUN_DECISION_INVALID"]
    trusted_records = isolated_state.get("trusted_verified_run_decisions", {})
    trusted_record = trusted_records.get(run_id) if isinstance(trusted_records, Mapping) else None
    expected_decision_id = (
        trusted_record.get("decision_id")
        if isinstance(trusted_record, Mapping)
        else _legacy_expected_decision_id(run_id)
    )
    if manifest.get("decision_id") != expected_decision_id:
        reasons.append("W1_R1_UNBOUND_VERIFIED_RUN_DECISION")
    if manifest.get("status") != "PASS" or manifest.get("current") is not True:
        reasons.append("W1_R1_VERIFIED_RUN_NOT_CURRENT_SUCCESS")
    if manifest.get("audited") is not True:
        reasons.append("W1_R1_VERIFIED_RUN_NOT_AUDITED")
    trusted_hashes = isolated_state.get("trusted_manifest_hashes", {})
    if (
        not isinstance(trusted_hashes, Mapping)
        or not _valid_hash(manifest.get("artifact_hash"))
        or manifest.get("artifact_hash") != trusted_hashes.get(run_id)
    ):
        reasons.append("W1_R1_VERIFIED_RUN_MANIFEST_HASH_MISMATCH")
    if isinstance(trusted_record, Mapping):
        decision_body = {
            key: value for key, value in trusted_record.items() if key != "decision_hash"
        }
        if not _valid_hash(trusted_record.get("decision_hash")) or trusted_record.get(
            "decision_hash"
        ) != sha256_json(decision_body):
            reasons.append("W1_R1_TRUSTED_DECISION_HASH_INVALID")
        exact_fields = (
            "run_id",
            "decision_id",
            "run_manifest_hash",
            "input_hash",
            "code_hash",
            "configuration_hash",
            "output_hash",
            "decision_hash",
            "current",
            "status",
            "evidence_artifact_ids",
        )

        def normalized_field(record: Mapping[str, Any], field: str) -> Any:
            value = record.get(field)
            return (
                tuple(value)
                if field == "evidence_artifact_ids" and isinstance(value, (list, tuple))
                else value
            )

        if any(
            normalized_field(manifest, field) != normalized_field(trusted_record, field)
            for field in exact_fields
        ):
            reasons.append("W1_R1_VERIFIED_RUN_EXACT_BINDING_MISMATCH")
        if claim is not None and any(
            claim.get(claim_field) != trusted_record.get(record_field)
            for claim_field, record_field in (
                ("run_id", "run_id"),
                ("input_hash", "input_hash"),
                ("code_commit", "code_hash"),
                ("output_hash", "output_hash"),
            )
        ):
            reasons.append("W1_R1_CLAIM_VERIFIED_RUN_BINDING_MISMATCH")
    elif claim is not None:
        binding_registry = isolated_state.get("trusted_run_bindings", {})
        binding = binding_registry.get(run_id) if isinstance(binding_registry, Mapping) else None
        if not isinstance(binding, Mapping) or any(
            claim.get(field) != binding.get(field)
            for field in ("run_id", "input_hash", "code_commit", "output_hash", "lineage")
        ):
            reasons.append("W1_R1_CLAIM_VERIFIED_RUN_BINDING_MISMATCH")
    return reasons


def _claim_boundary_reasons(payload: Any, isolated_state: Mapping[str, Any]) -> list[str]:
    if not isinstance(payload, Mapping):
        return ["W1_R1_CLAIM_PAYLOAD_INVALID"]
    claim = payload.get("claim")
    manifest = payload.get("verified_run_manifest")
    evidence = payload.get("evidence")
    reasons: list[str] = []
    if not isinstance(claim, Mapping):
        reasons.append("W1_R1_CLAIM_RECORD_INVALID")
    if not isinstance(evidence, (list, tuple)) or any(
        not isinstance(item, Mapping) for item in evidence
    ):
        reasons.append("W1_R1_CLAIM_EVIDENCE_LEDGER_INVALID")
    reasons.extend(
        _verified_decision_reasons(
            manifest,
            isolated_state,
            claim=claim if isinstance(claim, Mapping) else None,
        )
    )
    return reasons


def _trusted_freeze_values(isolated_state: Mapping[str, Any]) -> set[str]:
    values: set[str] = set()
    for key in ("trusted_candidate_freeze_hash", "trusted_metric_freeze_hash"):
        value = isolated_state.get(key)
        if _valid_hash(value):
            values.add(value)
    registry = isolated_state.get("trusted_freeze_hashes", {})
    if isinstance(registry, Mapping):
        values.update(value for value in registry.values() if _valid_hash(value))
    elif isinstance(registry, (list, tuple, set, frozenset)):
        values.update(value for value in registry if _valid_hash(value))
    return values


def _unknown_freeze_reasons(
    value: Any, isolated_state: Mapping[str, Any], path: str = ""
) -> list[str]:
    reasons: list[str] = []
    if isinstance(value, Mapping):
        trusted = _trusted_freeze_values(isolated_state)
        for key, item in value.items():
            normalized = _normalized_key(key)
            child_path = f"{path}.{normalized}" if path else normalized
            if normalized.endswith("freeze_hash") and (
                not _valid_hash(item) or item not in trusted
            ):
                reasons.append(f"W1_R1_UNTRUSTED_FREEZE_HASH:{child_path}")
            reasons.extend(_unknown_freeze_reasons(item, isolated_state, child_path))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            reasons.extend(_unknown_freeze_reasons(item, isolated_state, f"{path}[{index}]"))
    return reasons


def _manifest_stale(payload: Mapping[str, Any]) -> bool:
    manifest = payload.get("manifest")
    capture = payload.get("trusted_capture")
    if not isinstance(manifest, Mapping) or not isinstance(capture, Mapping):
        return False
    bindings = {
        "input_hash": sha256_json(capture.get("input_content")),
        "code_commit": capture.get("code_commit"),
        "config_hash": sha256_json(capture.get("config_content")),
        "output_hash": sha256_json(capture.get("output_content")),
    }
    return any(manifest.get(field) != value for field, value in bindings.items())


def _reproducibility_boundary_reasons(payload: Any, isolated_state: Mapping[str, Any]) -> list[str]:
    if not isinstance(payload, Mapping):
        return ["W1_R1_MANIFEST_PAYLOAD_INVALID"]
    reasons: list[str] = []
    manifest = payload.get("manifest")
    capture = payload.get("trusted_capture")
    if not isinstance(manifest, Mapping):
        reasons.append("W1_R1_MANIFEST_RECORD_INVALID")
    else:
        if not isinstance(manifest.get("seed"), int) or isinstance(manifest.get("seed"), bool):
            reasons.append("W1_R1_MANIFEST_SEED_INVALID")
        command = manifest.get("command")
        if (
            not isinstance(command, (list, tuple))
            or not command
            or any(not isinstance(item, str) or not item for item in command)
        ):
            reasons.append("W1_R1_MANIFEST_ARGV_INVALID")
        if manifest.get("current") is not True:
            reasons.append("W1_R1_MANIFEST_NOT_CURRENT")
        if manifest.get("outcome") not in TERMINAL_ATTEMPT_OUTCOMES:
            reasons.append("W1_R1_MANIFEST_OUTCOME_INVALID")
    if not isinstance(capture, Mapping):
        reasons.append("W1_R1_TRUSTED_CAPTURE_INVALID")
    if _contains_sensitive_value(payload):
        reasons.append("W1_R1_MANIFEST_SENSITIVE_VALUE_REJECTED")
    reasons.extend(_unknown_freeze_reasons(payload, isolated_state))
    if _manifest_stale(payload):
        reasons.append("W1_R1_MANIFEST_STALE")
    return reasons


def _sequence_of_strings(value: Any, *, nonempty: bool = False) -> bool:
    return bool(
        isinstance(value, (list, tuple))
        and (value or not nonempty)
        and all(isinstance(item, str) and item for item in value)
    )


def _comparison_boundary_reasons(payload: Any, isolated_state: Mapping[str, Any]) -> list[str]:
    if not isinstance(payload, Mapping):
        return ["W1_R1_COMPARISON_PAYLOAD_INVALID"]
    reasons: list[str] = []
    splits = payload.get("splits")
    if not isinstance(splits, Mapping) or set(splits) != {"train", "validation", "test"}:
        reasons.append("W1_R1_COMPARISON_SPLITS_INVALID")
    else:
        split_values = [splits[name] for name in ("train", "validation", "test")]
        if any(not _sequence_of_strings(value, nonempty=True) for value in split_values):
            reasons.append("W1_R1_COMPARISON_SPLITS_INVALID")
        else:
            sets = [set(value) for value in split_values]
            if any(left & right for index, left in enumerate(sets) for right in sets[index + 1 :]):
                reasons.append("W1_R1_COMPARISON_SPLITS_INVALID")
    for field, expected in (
        ("group_overlap", False),
        ("time_order_valid", True),
        ("future_feature", False),
        ("target_feature", False),
        ("model_frozen", True),
        ("selected_candidate_matches_validation", True),
        ("failures_retained", True),
        ("dependency_current", True),
    ):
        if payload.get(field) is not expected:
            reasons.append(f"W1_R1_COMPARISON_FLAG_INVALID:{field}")
    for field in (
        "test_used_for_candidate_generation",
        "test_used_for_feature_selection",
        "test_used_for_threshold_selection",
    ):
        if payload.get(field, False) is not False:
            reasons.append(f"W1_R1_COMPARISON_TEST_LEAKAGE:{field}")
    if payload.get("transform_fit_scope") != "train":
        reasons.append("W1_R1_COMPARISON_TRANSFORM_SCOPE_INVALID")
    baselines = payload.get("baselines")
    if not _sequence_of_strings(baselines) or set(baselines) != {"naive", "domain"}:
        reasons.append("W1_R1_COMPARISON_BASELINE_INVALID")
    for field, trusted_key in (
        ("candidate_freeze_hash", "trusted_candidate_freeze_hash"),
        ("metric_freeze_hash", "trusted_metric_freeze_hash"),
    ):
        value = payload.get(field)
        if not _valid_hash(value) or value != isolated_state.get(trusted_key):
            reasons.append(f"W1_R1_COMPARISON_UNTRUSTED_FREEZE:{field}")
    if tuple(payload.get("freeze_order", ())) != (
        "split",
        "candidates",
        "metric",
        "attempts",
        "model",
        "test",
    ):
        reasons.append("W1_R1_COMPARISON_FREEZE_ORDER_INVALID")
    seeds = payload.get("frozen_seeds")
    trusted_seeds = isolated_state.get("trusted_seeds")
    if (
        not isinstance(seeds, (list, tuple))
        or not seeds
        or any(not isinstance(seed, int) or isinstance(seed, bool) for seed in seeds)
        or len(seeds) != len(set(seeds))
        or list(seeds) != list(trusted_seeds or ())
    ):
        reasons.append("W1_R1_COMPARISON_SEEDS_INVALID")
        valid_seeds: tuple[int, ...] = ()
    else:
        valid_seeds = tuple(seeds)
    trusted_candidates_raw = isolated_state.get("trusted_candidates")
    trusted_candidates = (
        tuple(trusted_candidates_raw)
        if _sequence_of_strings(trusted_candidates_raw, nonempty=True)
        else ()
    )
    scores = payload.get("validation_scores")
    numeric_scores: dict[str, float] = {}
    if not isinstance(scores, Mapping) or not scores:
        reasons.append("W1_R1_COMPARISON_SCORES_INVALID")
    else:
        for candidate, score in scores.items():
            if not isinstance(candidate, str) or not candidate or not _strict_real(score):
                reasons.append("W1_R1_COMPARISON_SCORE_TYPE_INVALID")
                continue
            numeric_scores[candidate] = float(score)
        if set(scores) != set(trusted_candidates):
            reasons.append("W1_R1_COMPARISON_CANDIDATE_SET_NOT_FROZEN")
    attempts = payload.get("attempts")
    successful_pairs: set[tuple[str, int]] = set()
    observed_pairs: list[tuple[str, int]] = []
    if not isinstance(attempts, (list, tuple)) or not attempts:
        reasons.append("W1_R1_COMPARISON_ATTEMPT_LEDGER_INVALID")
    else:
        for attempt in attempts:
            if not isinstance(attempt, Mapping):
                reasons.append("W1_R1_COMPARISON_ATTEMPT_LEDGER_INVALID")
                continue
            candidate = attempt.get("candidate_id")
            seed = attempt.get("seed")
            run_id = attempt.get("run_id")
            outcome = attempt.get("outcome")
            terminal = attempt.get("terminal")
            retry = attempt.get("retry")
            infrastructure_failure = attempt.get("infrastructure_failure")
            failure_class = attempt.get("failure_class")
            fields_valid = bool(
                isinstance(candidate, str)
                and candidate in trusted_candidates
                and isinstance(seed, int)
                and not isinstance(seed, bool)
                and seed in valid_seeds
                and isinstance(run_id, str)
                and run_id == f"{candidate}-{seed}"
                and outcome in TERMINAL_ATTEMPT_OUTCOMES
                and terminal is True
                and isinstance(retry, bool)
                and isinstance(infrastructure_failure, bool)
                and isinstance(failure_class, str)
                and failure_class
            )
            if not fields_valid:
                reasons.append("W1_R1_COMPARISON_ATTEMPT_LEDGER_INVALID")
                continue
            pair = (candidate, seed)
            observed_pairs.append(pair)
            if retry:
                authorized = set(isolated_state.get("trusted_retry_run_ids", ()))
                if run_id not in authorized or not attempt.get("predecessor_run_id"):
                    reasons.append("W1_R1_COMPARISON_RETRY_NOT_AUTHORIZED")
            if outcome == "SUCCESS":
                if infrastructure_failure or failure_class != "NONE":
                    reasons.append("W1_R1_COMPARISON_SUCCESS_ATTEMPT_INVALID")
                successful_pairs.add(pair)
            else:
                if candidate in numeric_scores:
                    reasons.append("W1_R1_COMPARISON_FAILED_ATTEMPT_SCORED")
    expected_pairs = {(candidate, seed) for candidate in trusted_candidates for seed in valid_seeds}
    if set(observed_pairs) != expected_pairs or len(observed_pairs) != len(expected_pairs):
        reasons.append("W1_R1_COMPARISON_ATTEMPT_MATRIX_INVALID")
    if successful_pairs != expected_pairs:
        reasons.append("W1_R1_COMPARISON_SUCCESS_MATRIX_INCOMPLETE")
    manifests = payload.get("verified_run_manifests")
    if not isinstance(manifests, (list, tuple)) or not manifests:
        reasons.append("W1_R1_COMPARISON_VERIFIED_RUNS_INVALID")
    else:
        manifest_ids: list[str] = []
        for manifest in manifests:
            if isinstance(manifest, Mapping) and isinstance(manifest.get("run_id"), str):
                manifest_ids.append(manifest["run_id"])
            reasons.extend(_verified_decision_reasons(manifest, isolated_state))
        expected_ids = {f"{candidate}-{seed}" for candidate, seed in expected_pairs}
        if set(manifest_ids) != expected_ids or len(manifest_ids) != len(expected_ids):
            reasons.append("W1_R1_COMPARISON_VERIFIED_RUN_BIJECTION_INVALID")
    policy = isolated_state.get("comparison_policy")
    direction = payload.get("metric_direction")
    tolerance = payload.get("tie_tolerance")
    tie_keys = payload.get("ordered_tie_keys")
    if (
        not isinstance(policy, Mapping)
        or direction != policy.get("metric_direction")
        or tolerance != policy.get("tie_tolerance")
        or tuple(tie_keys or ()) != tuple(policy.get("ordered_tie_keys", ()))
        or direction not in {"MAXIMIZE", "MINIMIZE"}
        or not _strict_real(tolerance)
        or float(tolerance) < 0
        or tuple(tie_keys or ()) != ("candidate_id",)
    ):
        reasons.append("W1_R1_COMPARISON_POLICY_INVALID")
    elif numeric_scores and set(numeric_scores) == set(trusted_candidates):
        optimum = (
            max(numeric_scores.values())
            if direction == "MAXIMIZE"
            else min(numeric_scores.values())
        )
        tied = sorted(
            candidate
            for candidate, score in numeric_scores.items()
            if abs(score - optimum) <= float(tolerance)
        )
        if not tied or payload.get("selected_candidate_id") != tied[0]:
            reasons.append("W1_R1_COMPARISON_SELECTION_MISMATCH")
    events = payload.get("access_events")
    if not isinstance(events, (list, tuple)) or len(events) != 1:
        reasons.append("W1_R1_COMPARISON_TEST_ACCESS_COUNT_INVALID")
    elif not isinstance(events[0], Mapping):
        reasons.append("W1_R1_COMPARISON_ACCESS_EVENT_INVALID")
    return reasons


def workflow_checklist_r1(
    payload: Any, isolated_state: Any
) -> tuple[bool, tuple[str, ...], dict[str, Any]]:
    reasons = _state_boundary_reasons(isolated_state)
    reasons.extend(_workflow_boundary_reasons(payload))
    diagnostics: dict[str, Any] = {}
    if not reasons:
        passed, guard_reasons, diagnostics = workflow_checklist(payload, isolated_state)
        reasons.extend(guard_reasons)
        if not passed and not guard_reasons:
            reasons.append("W1_R1_WORKFLOW_REJECTED")
    return not reasons, tuple(sorted(set(reasons))), diagnostics


def claim_checklist_r1(
    payload: Any, isolated_state: Any
) -> tuple[bool, tuple[str, ...], dict[str, Any]]:
    reasons = _state_boundary_reasons(isolated_state)
    if isinstance(isolated_state, Mapping):
        reasons.extend(_claim_boundary_reasons(payload, isolated_state))
    diagnostics: dict[str, Any] = {"supporting_evidence": []}
    if not reasons:
        passed, guard_reasons, diagnostics = claim_checklist(payload, isolated_state)
        reasons.extend(guard_reasons)
        if not passed and not guard_reasons:
            reasons.append("W1_R1_CLAIM_REJECTED")
    return not reasons, tuple(sorted(set(reasons))), diagnostics


def reproducibility_checklist_r1(
    payload: Any, isolated_state: Any
) -> tuple[bool, tuple[str, ...], dict[str, Any]]:
    reasons = _state_boundary_reasons(isolated_state)
    if isinstance(isolated_state, Mapping):
        reasons.extend(_reproducibility_boundary_reasons(payload, isolated_state))
    diagnostics: dict[str, Any] = {}
    if not reasons:
        passed, guard_reasons, diagnostics = reproducibility_checklist(payload, isolated_state)
        reasons.extend(guard_reasons)
        if not passed and not guard_reasons:
            reasons.append("W1_R1_MANIFEST_REJECTED")
    return not reasons, tuple(sorted(set(reasons))), diagnostics


def comparison_checklist_r1(
    payload: Any, isolated_state: Any
) -> tuple[bool, tuple[str, ...], dict[str, Any]]:
    reasons = _state_boundary_reasons(isolated_state)
    if isinstance(isolated_state, Mapping):
        reasons.extend(_comparison_boundary_reasons(payload, isolated_state))
    diagnostics: dict[str, Any] = {}
    if not reasons:
        passed, guard_reasons, diagnostics = comparison_checklist(payload, isolated_state)
        reasons.extend(guard_reasons)
        if not passed and not guard_reasons:
            reasons.append("W1_R1_COMPARISON_REJECTED")
    return not reasons, tuple(sorted(set(reasons))), diagnostics


R1_GUARDS = {
    "accepted-versus-done-workflow-state": workflow_checklist_r1,
    "claim-evidence-support-gate": claim_checklist_r1,
    "hash-bound-reproducibility-manifest": reproducibility_checklist_r1,
    "leakage-safe-model-comparison-gate": comparison_checklist_r1,
}


class WorkflowGuardRevisionR1:
    """Fail-closed W1 revision that emits proposals only."""

    architecture_id = ARCHITECTURE_ID
    revision_id = REVISION_ID

    def evaluate_case(
        self,
        case_input: Any,
        isolated_state: Any,
        run_context: Any,
    ) -> ShadowRunResult:
        context = _safe_context(run_context)
        if not isinstance(case_input, (ShadowCaseInput, R1CaseInput)):
            payload: dict[str, Any] = {}
            case_input = ShadowCaseInput(
                case_id="W1-R1-MALFORMED-CASE",
                component_id="accepted-versus-done-workflow-state",
                payload=payload,
                input_hash=sha256_json(payload),
                case_class="malformed boundary",
            )
            reasons = ["W1_R1_CASE_INPUT_INVALID"]
        else:
            reasons = []
            if (
                not isinstance(case_input.case_id, str)
                or not case_input.case_id
                or not isinstance(case_input.component_id, str)
                or not isinstance(case_input.payload, Mapping)
                or not _valid_hash(case_input.input_hash)
            ):
                reasons.append("W1_R1_CASE_INPUT_INVALID")
        reasons.extend(_context_reasons(run_context))
        reasons.extend(_state_boundary_reasons(isolated_state))
        diagnostics: dict[str, Any] = {}
        component_id = case_input.component_id
        if component_id not in COMPONENT_IDS:
            reasons.append("W1_R1_UNKNOWN_COMPONENT")
        elif not reasons and component_id not in run_context.enabled_components:
            decision = ShadowDecision(
                "ABSTAIN",
                ("W1_R1_COMPONENT_DISABLED_BY_FROZEN_ABLATION",),
                {component_id: "DISABLED"},
            )
            return self._result(context, case_input, decision, {})
        elif not reasons:
            try:
                guard_state = deep_freeze(isolated_state)
                passed, guard_reasons, diagnostics = R1_GUARDS[component_id](
                    case_input.payload, guard_state
                )
            except Exception as exc:  # noqa: BLE001 - candidate boundary must retain failure
                passed = False
                guard_reasons = ("W1_R1_MALFORMED_INPUT_FAIL_CLOSED",)
                diagnostics = {"sanitized_exception_type": type(exc).__name__}
            reasons.extend(guard_reasons)
            if passed and reasons:
                reasons.append("W1_R1_INCONSISTENT_GUARD_RESULT")
        outcome = "PASS" if not reasons else "BLOCK"
        decision = ShadowDecision(
            outcome,
            tuple(sorted(set(reasons))) if reasons else ("W1_R1_ALL_WORKFLOW_CHECKS_PASS",),
            {component_id: outcome},
        )
        return self._result(context, case_input, decision, diagnostics)

    def _result(
        self,
        context: ShadowContext,
        case_input: ShadowCaseInput | R1CaseInput,
        decision: ShadowDecision,
        diagnostics: Mapping[str, Any],
    ) -> ShadowRunResult:
        evidence = ShadowEvidence(
            evidence_id=f"{context.run_id}:w1-r1-workflow-checklist",
            evidence_type="SHADOW_CHECKLIST_RESULT",
            run_id=context.run_id,
            current=True,
            supports=(case_input.component_id,) if decision.outcome == "PASS" else (),
            contradicts=(case_input.component_id,) if decision.outcome == "BLOCK" else (),
            payload={"reason_codes": list(decision.reason_codes), "revision_id": REVISION_ID},
        )
        return build_result(
            context=context,
            case_input=case_input,
            decision=decision,
            evidence=(evidence,),
            diagnostics={
                **diagnostics,
                "revision_id": REVISION_ID,
                "implementation_kind": "STATELESS_WORKFLOW_CHECKLIST_R1",
                "accepted": False,
                "final": False,
                "formal_state_writes": 0,
                "state_truth_sources": 1,
                "formal_skill_count": 1,
                "hidden_vault_accesses": 0,
                "third_party_executions": 0,
            },
            terminal_status="COMPLETED" if decision.outcome != "BLOCK" else "FAILED_RETAINED",
        )


__all__ = [
    "ARCHITECTURE_ID",
    "REVISION_ID",
    "WorkflowGuardRevisionR1",
    "claim_checklist_r1",
    "comparison_checklist_r1",
    "reproducibility_checklist_r1",
    "workflow_checklist_r1",
]
