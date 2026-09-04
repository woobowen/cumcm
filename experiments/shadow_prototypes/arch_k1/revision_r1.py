"""Competition RC1 revision of the project-owned K1 evidence kernel.

This module is deliberately additive.  The Phase 002D-R3 K1 implementation is
frozen historical evidence; RC1 uses this revision through a versioned runner.
Every public boundary is fail closed and emits only sanitized diagnostics.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from numbers import Real
from pathlib import Path, PurePosixPath
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

from .claim_support import evaluate_claim_support
from .lifecycle import evaluate_lifecycle
from .model_comparison import evaluate_model_comparison
from .reproducibility import evaluate_reproducibility

ARCHITECTURE_ID = "ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL"
REVISION_ID = "ARCH-K1-R1"
ALLOWED_STAGES = frozenset(
    {
        "PUBLIC_VALIDATION",
        "STAGE1_DETERMINISTIC",
        "STAGE2_MODEL",
        "DETERMINISTIC_ABLATION",
    }
)
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")
CREDENTIAL_URL = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://[^/@\s]+:[^/@\s]+@")
ENV_PATH = re.compile(r"^(?:\$\{?[A-Za-z_][A-Za-z0-9_]*\}?|%[A-Za-z_][A-Za-z0-9_]*%)")

SENSITIVE_KEYS = frozenset(
    {
        "api_key",
        "access_token",
        "bearer_token",
        "browser_state",
        "client_secret",
        "credential",
        "credentials",
        "hidden_reasoning",
        "password",
        "private_key",
        "private_path",
        "raw_trace",
        "refresh_token",
        "secret",
        "token",
    }
)
SENSITIVE_COLLAPSED_KEYS = frozenset(item.replace("_", "") for item in SENSITIVE_KEYS)
NON_SUCCESS_OUTCOMES = frozenset({"FAILED", "PARTIAL", "SUPERSEDED", "STALE"})
ALLOWED_STATE_KEYS = frozenset(
    {
        "truth_source",
        "formal_state_writes_allowed",
        "trusted_run_ids",
        "trusted_stage_hashes",
        "trusted_gate_hashes",
        "trusted_artifact_hashes",
        "trusted_run_bindings",
        "trusted_manifest_hashes",
        "trusted_dependency_graph",
        "trusted_dependency_graph_hash",
        "trusted_challenge_hashes",
        "trusted_disposition_hashes",
        "trusted_repro_manifest_hashes",
        "trusted_capture_hashes",
        "comparison_policy",
        "trusted_candidates",
        "trusted_seeds",
        "trusted_candidate_freeze_hash",
        "trusted_metric_freeze_hash",
        "trusted_comparison_design_hash",
        "trusted_access_genesis",
        "trusted_access_heads",
        "trusted_model_freeze_hash",
        "trusted_pretest_decision_hash",
        "trusted_test_set_id",
        "exposed_test_set_ids",
        # RC1 extensions remain registries inside the one isolated state bundle.
        "trusted_freeze_registry",
        "trusted_verified_run_hashes",
        "trusted_metric_ids",
        "isolated_state_binding_hash",
    }
)


def _safe_hash(value: Any) -> str | None:
    try:
        return sha256_json(value)
    except (TypeError, ValueError, OverflowError):
        return None


def _stable_reasons(reasons: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted({item for item in reasons if isinstance(item, str) and item}))


def _normalized_key(value: Any) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(value).casefold()).strip("_")
    return normalized


def _sensitive_key(value: Any) -> bool:
    normalized = _normalized_key(value)
    collapsed = normalized.replace("_", "")
    return normalized in SENSITIVE_KEYS or collapsed in SENSITIVE_COLLAPSED_KEYS


def _unsafe_path_or_url(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    normalized = value.replace("\\", "/")
    return bool(
        value.startswith(("/", "~", "\\\\"))
        or normalized.startswith("//")
        or WINDOWS_ABSOLUTE.match(value)
        or ENV_PATH.match(value)
        or CREDENTIAL_URL.match(value)
        or ".." in normalized.split("/")
    )


def _sensitive_locations(value: Any, prefix: str = "$") -> tuple[str, ...]:
    """Return locations only; sensitive values never enter diagnostics."""
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            location = f"{prefix}.{key}"
            if _sensitive_key(key):
                found.append(location)
            else:
                found.extend(_sensitive_locations(item, location))
    elif isinstance(value, (list, tuple, set, frozenset)):
        for index, item in enumerate(value):
            found.extend(_sensitive_locations(item, f"{prefix}[{index}]"))
    elif _unsafe_path_or_url(value):
        found.append(prefix)
    return tuple(sorted(set(found)))


def _valid_relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or _unsafe_path_or_url(value):
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts


def _valid_hash(value: Any, *, commit: bool = False) -> bool:
    return bool((HEX40 if commit else HEX64).fullmatch(value) if isinstance(value, str) else False)


def _state_boundary(state: Any) -> tuple[str, ...]:
    if not isinstance(state, Mapping):
        return ("K1_R1_ISOLATED_STATE_MALFORMED",)
    reasons: list[str] = []
    if state.get("truth_source") != "state/project_state.json":
        reasons.append("K1_R1_SINGLE_STATE_TRUTH_REQUIRED")
    if state.get("formal_state_writes_allowed") is not False:
        reasons.append("K1_R1_FORMAL_STATE_WRITE_PROHIBITED")
    if set(state) - ALLOWED_STATE_KEYS:
        reasons.append("K1_R1_EXTRA_STATE_AUTHORITY_REJECTED")
    state_path = state.get("formal_state_path")
    if state_path is not None:
        reasons.append("K1_R1_FORMAL_STATE_PATH_REJECTED")
    binding = state.get("isolated_state_binding_hash")
    if binding is not None:
        body = {key: value for key, value in state.items() if key != "isolated_state_binding_hash"}
        if not _valid_hash(binding) or binding != _safe_hash(body):
            reasons.append("K1_R1_ISOLATED_STATE_BINDING_INVALID")
    return _stable_reasons(reasons)


def _context_boundary(context: Any) -> tuple[str, ...]:
    if not isinstance(context, ShadowContext):
        return ("K1_R1_CONTEXT_MALFORMED",)
    reasons: list[str] = []
    if context.architecture_id != ARCHITECTURE_ID:
        reasons.append("K1_R1_CONTEXT_ARCHITECTURE_MISMATCH")
    if not isinstance(context.stage, str) or context.stage not in ALLOWED_STAGES:
        reasons.append("K1_R1_STAGE_BOUNDARY_REJECTED")
    enabled = context.enabled_components
    if (
        not isinstance(enabled, (list, tuple))
        or any(not isinstance(item, str) for item in enabled)
        or len(set(enabled)) != len(enabled)
        or any(item not in COMPONENT_IDS for item in enabled)
    ):
        reasons.append("K1_R1_ENABLED_COMPONENTS_MALFORMED")
    if not isinstance(context.run_id, str) or not context.run_id:
        reasons.append("K1_R1_CONTEXT_RUN_ID_INVALID")
    if not isinstance(context.output_dir, Path):
        reasons.append("K1_R1_CONTEXT_OUTPUT_DIR_INVALID")
    return _stable_reasons(reasons)


def _fallback_context(context: Any) -> ShadowContext:
    return ShadowContext(
        run_id=(
            context.run_id if isinstance(context, ShadowContext) and context.run_id else "invalid"
        ),
        architecture_id=ARCHITECTURE_ID,
        stage="PUBLIC_VALIDATION",
        output_dir=Path("."),
        timeout_seconds=0,
        operation_budget=0,
        enabled_components=(),
    )


def _fallback_case(case_input: Any) -> Any:
    if all(
        hasattr(case_input, field) for field in ("case_id", "component_id", "payload", "input_hash")
    ):
        return case_input
    return ShadowCaseInput(
        case_id="invalid-case",
        component_id="invalid-component",
        payload={},
        input_hash=sha256_json({}),
    )


def _legacy_verified_run(record: Mapping[str, Any], state: Mapping[str, Any]) -> bool:
    run_id = record.get("run_id")
    registry = state.get("trusted_manifest_hashes")
    try:
        trusted_ids = set(state.get("trusted_run_ids", ()))
    except TypeError:
        return False
    expected_decision = f"manifest-decision:{run_id}"
    body_hash = _safe_hash({"run_id": run_id, "status": record.get("status")})
    return bool(
        isinstance(registry, Mapping)
        and isinstance(run_id, str)
        and run_id in trusted_ids
        and record.get("decision_id") == expected_decision
        and record.get("authority") == "existing-native-run-ledger"
        and record.get("status") == "PASS"
        and record.get("current") is True
        and record.get("audited") is True
        and record.get("artifact_hash") == body_hash
        and record.get("artifact_hash") == registry.get(run_id)
    )


EXACT_RUN_FIELDS = (
    "run_id",
    "run_manifest_hash",
    "input_hash",
    "code_hash",
    "configuration_hash",
    "output_hash",
    "decision_hash",
    "evidence_artifact_ids",
)
EXACT_EXTENSION_FIELDS = frozenset(
    {
        "run_manifest_hash",
        "code_hash",
        "configuration_hash",
        "decision_hash",
        "evidence_artifact_ids",
    }
)


def verified_run_record_r1(
    record: Any,
    state: Any,
    *,
    expected_run_id: str | None = None,
    expected_binding: Mapping[str, Any] | None = None,
) -> bool:
    """Validate legacy fixtures and RC1 exact verified-run records.

    RC1 records bind every result-defining hash and their own canonical record
    hash through a trusted registry.  Legacy support is intentionally narrow
    and also binds the decision identifier, closing the old mutation hole.
    """
    if not isinstance(record, Mapping) or not isinstance(state, Mapping):
        return False
    run_id = record.get("run_id")
    if expected_run_id is not None and run_id != expected_run_id:
        return False
    exact_mode = any(field in record for field in EXACT_RUN_FIELDS[1:]) or isinstance(
        state.get("trusted_verified_run_hashes"), Mapping
    )
    if not exact_mode:
        return _legacy_verified_run(record, state)
    if any(field not in record for field in EXACT_RUN_FIELDS):
        return False
    evidence_ids = record.get("evidence_artifact_ids")
    if (
        not isinstance(run_id, str)
        or not run_id
        or any(not _valid_hash(record.get(field)) for field in EXACT_RUN_FIELDS[1:7])
        or not isinstance(evidence_ids, (list, tuple))
        or not evidence_ids
        or any(not isinstance(item, str) or not item for item in evidence_ids)
        or len(set(evidence_ids)) != len(evidence_ids)
        or record.get("authority") != "existing-native-run-ledger"
        or record.get("status") != "PASS"
        or record.get("current") is not True
        or record.get("current_status", "CURRENT") != "CURRENT"
        or record.get("superseded", False) is not False
        or record.get("audited") is not True
    ):
        return False
    if expected_binding is not None and any(
        record.get(field) != expected_binding.get(field) for field in EXACT_RUN_FIELDS
    ):
        return False
    record_body = {key: value for key, value in record.items() if key != "record_hash"}
    record_hash = _safe_hash(record_body)
    registry = state.get("trusted_verified_run_hashes")
    return bool(
        isinstance(registry, Mapping)
        and record.get("record_hash") == record_hash
        and registry.get(run_id) == record_hash
    )


def evaluate_claim_support_r1(
    payload: Any, state: Any
) -> tuple[bool | None, tuple[str, ...], dict[str, Any]]:
    if not isinstance(payload, Mapping) or not isinstance(state, Mapping):
        return (
            False,
            ("K1_R1_CLAIM_INPUT_MALFORMED",),
            {
                "disposition": "REJECTED",
                "supporting_evidence": [],
            },
        )
    try:
        passed, base_reasons, diagnostics = evaluate_claim_support(payload, state)
    except Exception:  # noqa: BLE001 - untrusted nested input boundary
        passed, base_reasons, diagnostics = False, ("K1_R1_CLAIM_INPUT_MALFORMED",), {}
    reasons = list(base_reasons)
    claim = payload.get("claim")
    record = payload.get("verified_run_manifest")
    if not isinstance(claim, Mapping):
        reasons.append("K1_R1_CLAIM_RECORD_INVALID")
    else:
        run_id = claim.get("run_id")
        run_bindings = state.get("trusted_run_bindings")
        expected = run_bindings.get(run_id) if isinstance(run_bindings, Mapping) else None
        exact_mode = isinstance(state.get("trusted_verified_run_hashes"), Mapping) or bool(
            EXACT_EXTENSION_FIELDS & set(claim)
        )
        if exact_mode:
            if not isinstance(expected, Mapping) or any(
                claim.get(field) != expected.get(field) for field in EXACT_RUN_FIELDS
            ):
                reasons.append("K1_R1_CLAIM_EXACT_RUN_BINDING_INVALID")
            evidence_ids = claim.get("evidence_artifact_ids")
            evidence = payload.get("evidence")
            observed_ids = (
                sorted(
                    str(item.get("evidence_id"))
                    for item in evidence
                    if isinstance(item, Mapping) and item.get("evidence_id")
                )
                if isinstance(evidence, (list, tuple))
                else []
            )
            if not isinstance(evidence_ids, (list, tuple)) or sorted(evidence_ids) != observed_ids:
                reasons.append("K1_R1_CLAIM_EVIDENCE_ARTIFACT_SET_MISMATCH")
        if not verified_run_record_r1(
            record,
            state,
            expected_run_id=str(run_id),
            expected_binding=expected if exact_mode else None,
        ):
            reasons.append("K1_R1_UNBOUND_VERIFIED_RUN_DECISION")
        if isinstance(record, Mapping):
            for field in ("input_hash", "output_hash"):
                if field in record and record.get(field) != claim.get(field):
                    reasons.append(f"K1_R1_CLAIM_{field.upper()}_MISMATCH")
            code_value = claim.get("code_hash", claim.get("code_commit"))
            if "code_hash" in record and record.get("code_hash") != code_value:
                reasons.append("K1_R1_CLAIM_CODE_HASH_MISMATCH")
            if record.get("current") is False or record.get("superseded") is True:
                reasons.append("K1_R1_CLAIM_STALE_OR_SUPERSEDED_RUN")
    reasons = list(_stable_reasons(reasons))
    return (
        passed if not reasons else False,
        tuple(reasons),
        {
            "disposition": "SUPPORTED" if not reasons and passed is True else "REJECTED",
            "supporting_evidence": diagnostics.get("supporting_evidence", []),
            "exact_verified_run_bound": not any("VERIFIED_RUN" in item for item in reasons),
        },
    )


def _validate_file_hashes(value: Any) -> bool:
    return bool(
        isinstance(value, (list, tuple))
        and value
        and all(
            isinstance(item, Mapping)
            and _valid_relative_path(item.get("path"))
            and _valid_hash(item.get("sha256"))
            for item in value
        )
    )


def _validate_freezes(manifest: Mapping[str, Any], state: Mapping[str, Any]) -> bool:
    bindings = manifest.get("freeze_bindings")
    registry = state.get("trusted_freeze_registry")
    if not isinstance(bindings, Mapping) or not bindings or not isinstance(registry, Mapping):
        return False
    return all(
        isinstance(name, str) and bool(name) and _valid_hash(value) and registry.get(name) == value
        for name, value in bindings.items()
    )


def _evaluate_extended_repro(
    manifest: Mapping[str, Any], capture: Any, state: Mapping[str, Any]
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    scalar_required = {
        "run_id",
        "revision_id",
        "prior_manifest_hash",
        "current",
        "authority",
        "input_hash",
        "code_commit",
        "config_hash",
        "seed",
        "command",
        "cwd",
        "environment_hash",
        "dependency_hash",
        "output_hash",
        "outcome",
    }
    if not scalar_required <= set(manifest):
        reasons.append("K1_R1_REPRO_REQUIRED_BINDING_MISSING")
    if any(
        not _valid_hash(manifest.get(field))
        for field in (
            "input_hash",
            "config_hash",
            "environment_hash",
            "dependency_hash",
            "output_hash",
            "prior_manifest_hash",
        )
    ) or not _valid_hash(manifest.get("code_commit"), commit=True):
        reasons.append("K1_R1_REPRO_HASH_FORMAT_INVALID")
    try:
        trusted_run_ids = set(state.get("trusted_run_ids", ()))
    except TypeError:
        trusted_run_ids = set()
    if manifest.get("run_id") not in trusted_run_ids:
        reasons.append("K1_R1_REPRO_REGISTERED_RUN_REQUIRED")
    trusted_manifests = state.get("trusted_repro_manifest_hashes")
    if not isinstance(trusted_manifests, Mapping) or trusted_manifests.get(
        manifest.get("run_id")
    ) != _safe_hash(manifest):
        reasons.append("K1_R1_REPRO_MANIFEST_NOT_TRUSTED")
    if (
        manifest.get("current") is not True
        or manifest.get("authority") != "existing-native-run-ledger"
        or not isinstance(manifest.get("revision_id"), str)
        or not manifest.get("revision_id")
    ):
        reasons.append("K1_R1_REPRO_CURRENT_REVISION_INVALID")
    command = manifest.get("command")
    if (
        not isinstance(command, (list, tuple))
        or not command
        or any(
            not isinstance(item, str) or not item or _unsafe_path_or_url(item) for item in command
        )
        or command[0].casefold() in {"sh", "bash", "zsh", "cmd", "cmd.exe", "powershell", "pwsh"}
        or any(item.casefold() in {"-c", "/c", "-command"} for item in command[1:])
    ):
        reasons.append("K1_R1_REPRO_ARGV_INVALID")
    if not _valid_relative_path(manifest.get("cwd")):
        reasons.append("K1_R1_REPRO_CWD_INVALID")
    seed = manifest.get("seed")
    if isinstance(seed, bool) or not isinstance(seed, Real) or not math.isfinite(float(seed)):
        reasons.append("K1_R1_REPRO_SEED_INVALID")
    if not isinstance(capture, Mapping):
        reasons.append("K1_R1_REPRO_TRUSTED_CAPTURE_MISSING")
    else:
        trusted_captures = state.get("trusted_capture_hashes")
        if not isinstance(trusted_captures, Mapping) or trusted_captures.get(
            manifest.get("run_id")
        ) != _safe_hash(capture):
            reasons.append("K1_R1_REPRO_TRUSTED_CAPTURE_BINDING_INVALID")
        projection = {
            "run_id": capture.get("run_id"),
            "revision_id": capture.get("revision_id"),
            "prior_manifest_hash": capture.get("prior_manifest_hash"),
            "current": capture.get("current"),
            "authority": capture.get("authority"),
            "input_hash": _safe_hash(capture.get("input_content")),
            "code_commit": capture.get("code_commit"),
            "config_hash": _safe_hash(capture.get("config_content")),
            "seed": capture.get("seed"),
            "command": capture.get("command"),
            "cwd": capture.get("cwd"),
            "environment_hash": _safe_hash(capture.get("environment")),
            "dependency_hash": _safe_hash(capture.get("dependencies")),
            "output_hash": _safe_hash(capture.get("output_content")),
            "outcome": capture.get("outcome"),
        }
        if any(manifest.get(field) != value for field, value in projection.items()):
            reasons.append("K1_R1_REPRO_CAPTURE_CONTENT_MISMATCH")
    return not reasons, _stable_reasons(reasons)


def evaluate_reproducibility_r1(
    payload: Any, state: Any
) -> tuple[bool, tuple[str, ...], dict[str, Any]]:
    if not isinstance(payload, Mapping) or not isinstance(state, Mapping):
        return (
            False,
            ("K1_R1_REPRO_INPUT_MALFORMED",),
            {
                "private_fields_redacted": 0,
                "retained_outcome": None,
            },
        )
    sensitive = _sensitive_locations(payload)
    manifest = payload.get("manifest")
    extended = isinstance(manifest, Mapping) and manifest.get("manifest_version") == "k1-repro/v2"
    if extended:
        passed, base_reasons = _evaluate_extended_repro(
            manifest, payload.get("trusted_capture"), state
        )
    else:
        try:
            passed, base_reasons, _ = evaluate_reproducibility(payload, state)
        except Exception:  # noqa: BLE001 - untrusted nested input boundary
            passed, base_reasons = False, ("K1_R1_REPRO_INPUT_MALFORMED",)
    reasons = list(base_reasons)
    if sensitive:
        reasons.append("K1_R1_SENSITIVE_VALUE_REDACTED_AND_REJECTED")
    if "freeze_hash" in payload:
        freeze_hash = payload.get("freeze_hash")
        registry = state.get("trusted_freeze_registry")
        if not _valid_hash(freeze_hash):
            reasons.append("K1_R1_REPRO_FREEZE_HASH_INVALID")
        elif not isinstance(registry, Mapping) or freeze_hash not in registry.values():
            reasons.append("K1_R1_REPRO_FREEZE_HASH_NOT_TRUSTED")
    if isinstance(manifest, Mapping):
        outcome = manifest.get("outcome")
        if outcome in NON_SUCCESS_OUTCOMES:
            reasons.append(f"K1_R1_NON_SUCCESS_RETAINED:{outcome}")
        if extended:
            required = {
                "input_files",
                "code_tree_hash",
                "config_content_hash",
                "seed",
                "command",
                "cwd_policy",
                "environment_allowlist",
                "output_files",
                "outcome",
                "failure",
                "supersession",
                "freeze_bindings",
            }
            if not required <= set(manifest):
                reasons.append("K1_R1_REPRO_REQUIRED_BINDING_MISSING")
            if not _validate_file_hashes(manifest.get("input_files")):
                reasons.append("K1_R1_REPRO_INPUT_FILE_BINDING_INVALID")
            if not _validate_file_hashes(manifest.get("output_files")):
                reasons.append("K1_R1_REPRO_OUTPUT_FILE_BINDING_INVALID")
            if not _valid_hash(manifest.get("code_tree_hash")):
                reasons.append("K1_R1_REPRO_CODE_TREE_BINDING_INVALID")
            if not _valid_hash(manifest.get("config_content_hash")):
                reasons.append("K1_R1_REPRO_CONFIG_BINDING_INVALID")
            if manifest.get("cwd_policy") != "REPOSITORY_RELATIVE_ONLY":
                reasons.append("K1_R1_REPRO_CWD_POLICY_INVALID")
            environment = manifest.get("environment_allowlist")
            if not isinstance(environment, Mapping) or _sensitive_locations(environment):
                reasons.append("K1_R1_REPRO_ENVIRONMENT_ALLOWLIST_INVALID")
            supersession = manifest.get("supersession")
            if not isinstance(supersession, Mapping) or set(supersession) != {
                "superseded",
                "superseded_by",
            }:
                reasons.append("K1_R1_REPRO_SUPERSESSION_INVALID")
            if not _validate_freezes(manifest, state):
                reasons.append("K1_R1_REPRO_FREEZE_REGISTRY_MISMATCH")
        elif "freeze_bindings" in manifest and not _validate_freezes(manifest, state):
            reasons.append("K1_R1_REPRO_FREEZE_REGISTRY_MISMATCH")
    else:
        outcome = None
        reasons.append("K1_R1_REPRO_MANIFEST_INVALID")
    reasons = list(_stable_reasons(reasons))
    return (
        passed and not reasons,
        tuple(reasons),
        {
            "canonical_manifest_hash": _safe_hash(manifest),
            "private_fields_redacted": len(sensitive),
            "retained_outcome": outcome,
            "trusted_freezes_verified": isinstance(manifest, Mapping)
            and "freeze_bindings" in manifest
            and _validate_freezes(manifest, state),
        },
    )


def _strict_scores(value: Any) -> dict[str, float] | None:
    if not isinstance(value, Mapping) or not value:
        return None
    scores: dict[str, float] = {}
    for candidate, raw in value.items():
        if not isinstance(candidate, str) or not candidate or isinstance(raw, bool):
            return None
        if not isinstance(raw, Real) or not math.isfinite(float(raw)):
            return None
        scores[candidate] = float(raw)
    return scores


def _strict_splits(value: Any) -> bool:
    if not isinstance(value, Mapping) or set(value) != {"train", "validation", "test"}:
        return False
    groups: list[set[str]] = []
    for name in ("train", "validation", "test"):
        split = value.get(name)
        if (
            not isinstance(split, (list, tuple))
            or not split
            or any(not isinstance(item, str) or not item for item in split)
            or len(set(split)) != len(split)
        ):
            return False
        groups.append(set(split))
    return not any(
        left & right for index, left in enumerate(groups) for right in groups[index + 1 :]
    )


def _attempt_audit(payload: Mapping[str, Any]) -> tuple[list[str], dict[str, int]]:
    reasons: list[str] = []
    attempts = payload.get("attempts")
    if not isinstance(attempts, (list, tuple)) or not attempts:
        return ["K1_R1_ATTEMPT_LEDGER_MALFORMED"], {
            "reliability_denominator": 0,
            "ranking_attempt_count": 0,
        }
    run_ids: set[str] = set()
    successful: set[str] = set()
    retry_pairs: Counter[tuple[str, Any]] = Counter()
    for attempt in attempts:
        if not isinstance(attempt, Mapping):
            reasons.append("K1_R1_ATTEMPT_LEDGER_MALFORMED")
            continue
        run_id = attempt.get("run_id")
        candidate = attempt.get("candidate_id")
        seed = attempt.get("seed")
        outcome = attempt.get("outcome")
        if (
            not isinstance(run_id, str)
            or not run_id
            or run_id in run_ids
            or not isinstance(candidate, str)
            or not candidate
            or isinstance(seed, bool)
            or not isinstance(seed, int)
            or attempt.get("terminal") is not True
            or outcome not in {"SUCCESS", *NON_SUCCESS_OUTCOMES}
        ):
            reasons.append("K1_R1_ATTEMPT_LEDGER_MALFORMED")
            continue
        run_ids.add(run_id)
        if outcome == "SUCCESS":
            successful.add(run_id)
        if attempt.get("retry") is True:
            retry_pairs[(candidate, seed)] += 1
            if retry_pairs[(candidate, seed)] > 1:
                reasons.append("K1_R1_RETRY_UNTIL_SUCCESS_REJECTED")
    ranked = payload.get("ranked_run_ids")
    if ranked is not None and (
        not isinstance(ranked, (list, tuple))
        or any(not isinstance(run_id, str) for run_id in ranked)
        or not set(ranked) <= successful
    ):
        reasons.append("K1_R1_NON_SUCCESS_ATTEMPT_SCORED")
    return reasons, {
        "reliability_denominator": len(attempts),
        "ranking_attempt_count": len(successful),
    }


def evaluate_model_comparison_r1(
    payload: Any, state: Any
) -> tuple[bool, tuple[str, ...], dict[str, Any]]:
    if not isinstance(payload, Mapping) or not isinstance(state, Mapping):
        return (
            False,
            ("K1_R1_COMPARISON_INPUT_MALFORMED",),
            {
                "selected_candidate": None,
                "reliability_denominator": 0,
            },
        )
    try:
        passed, base_reasons, diagnostics = evaluate_model_comparison(payload, state)
    except Exception:  # noqa: BLE001 - untrusted nested input boundary
        passed, base_reasons, diagnostics = (
            False,
            ("K1_R1_COMPARISON_INPUT_MALFORMED",),
            {},
        )
    reasons = list(base_reasons)
    scores = _strict_scores(payload.get("validation_scores"))
    if scores is None:
        reasons.append("K1_R1_SCORE_TYPE_OR_FINITE_INVALID")
    if not _strict_splits(payload.get("splits")):
        reasons.append("K1_R1_SPLIT_STRUCTURE_INVALID")
    attempt_reasons, attempt_diagnostics = _attempt_audit(payload)
    reasons.extend(attempt_reasons)
    for field, registry_name in (
        ("candidate_freeze_hash", "trusted_candidate_freeze_hash"),
        ("metric_freeze_hash", "trusted_metric_freeze_hash"),
    ):
        if not _valid_hash(payload.get(field)) or payload.get(field) != state.get(registry_name):
            reasons.append(f"K1_R1_UNTRUSTED_FREEZE:{field}")
    if payload.get("test_used_for_candidate_generation") is True:
        reasons.append("K1_R1_TEST_USED_FOR_CANDIDATE_GENERATION")
    if payload.get("test_used_for_feature_selection") is True:
        reasons.append("K1_R1_TEST_USED_FOR_FEATURE_SELECTION")
    if payload.get("test_used_for_threshold_selection") is True:
        reasons.append("K1_R1_TEST_USED_FOR_THRESHOLD_SELECTION")
    trusted_metric_ids = state.get("trusted_metric_ids")
    if trusted_metric_ids is not None and (
        not isinstance(trusted_metric_ids, (list, tuple))
        or payload.get("metric_id") not in trusted_metric_ids
    ):
        reasons.append("K1_R1_METRIC_NOT_FROZEN")
    reasons = list(_stable_reasons(reasons))
    return (
        passed and not reasons,
        tuple(reasons),
        {
            "selected_candidate": diagnostics.get("selected_candidate"),
            "premature_access_count": diagnostics.get("premature_access_count", 0),
            "final_test_access_count": diagnostics.get("final_test_access_count", 0),
            **attempt_diagnostics,
        },
    )


R1_KERNELS = {
    "accepted-versus-done-workflow-state": evaluate_lifecycle,
    "claim-evidence-support-gate": evaluate_claim_support_r1,
    "hash-bound-reproducibility-manifest": evaluate_reproducibility_r1,
    "leakage-safe-model-comparison-gate": evaluate_model_comparison_r1,
}


class DeterministicEvidenceKernelRevisionR1:
    """Strict additive K1 revision selected only by the Competition R1 Gate."""

    architecture_id = ARCHITECTURE_ID
    revision_id = REVISION_ID

    def evaluate_case(
        self,
        case_input: Any,
        isolated_state: Any,
        run_context: Any,
    ) -> ShadowRunResult:
        context_reasons = list(_context_boundary(run_context))
        state_reasons = list(_state_boundary(isolated_state))
        case_reasons: list[str] = []
        if not isinstance(case_input, ShadowCaseInput):
            # R1CaseInput is deliberately duck-typed to avoid a second result
            # contract while still transporting non-finite adversarial values.
            required = ("case_id", "component_id", "payload", "input_hash")
            if not all(hasattr(case_input, field) for field in required):
                case_reasons.append("K1_R1_CASE_INPUT_MALFORMED")
        safe_context = (
            run_context
            if isinstance(run_context, ShadowContext)
            else _fallback_context(run_context)
        )
        safe_case = _fallback_case(case_input)
        component_id = getattr(case_input, "component_id", None)
        payload = getattr(case_input, "payload", None)
        reasons = [*context_reasons, *state_reasons, *case_reasons]
        diagnostics: dict[str, Any] = {}
        passed: bool | None = False
        if not reasons:
            enabled = safe_context.enabled_components
            if component_id not in COMPONENT_IDS:
                reasons.append("K1_R1_UNKNOWN_COMPONENT")
            elif component_id not in enabled:
                decision = ShadowDecision(
                    "ABSTAIN",
                    ("K1_R1_COMPONENT_DISABLED_BY_FROZEN_ABLATION",),
                    {str(component_id): "DISABLED"},
                )
                return self._result(safe_case, safe_context, decision, {})
            elif not isinstance(payload, Mapping):
                reasons.append("K1_R1_COMPONENT_PAYLOAD_MALFORMED")
            else:
                try:
                    passed, component_reasons, diagnostics = R1_KERNELS[str(component_id)](
                        payload, isolated_state
                    )
                    reasons.extend(component_reasons)
                except Exception:  # noqa: BLE001 - final public fail-closed boundary
                    passed = False
                    reasons.append("K1_R1_MALFORMED_INPUT_FAIL_CLOSED")
                    diagnostics = {}
        outcome = (
            "PASS" if passed is True and not reasons else "ABSTAIN" if passed is None else "BLOCK"
        )
        stable = _stable_reasons(reasons) or ("K1_R1_ALL_DETERMINISTIC_CHECKS_PASS",)
        decision = ShadowDecision(outcome, stable, {str(component_id): outcome})
        return self._result(safe_case, safe_context, decision, diagnostics)

    def _result(
        self,
        case_input: ShadowCaseInput,
        context: ShadowContext,
        decision: ShadowDecision,
        diagnostics: Mapping[str, Any],
    ) -> ShadowRunResult:
        evidence = ShadowEvidence(
            evidence_id=f"{context.run_id}:k1-r1",
            evidence_type="COMPETITION_RC1_DETERMINISTIC_PROPOSAL",
            run_id=context.run_id,
            current=True,
            supports=(case_input.component_id,) if decision.outcome == "PASS" else (),
            contradicts=(case_input.component_id,) if decision.outcome == "BLOCK" else (),
            payload={"reason_codes": list(decision.reason_codes), "revision_id": REVISION_ID},
        )
        sanitized = {
            **diagnostics,
            "revision_id": REVISION_ID,
            "accepted": False,
            "final": False,
            "ready_for_paper": False,
            "formal_state_writes": 0,
            "state_truth_sources": 1,
            "hidden_vault_accesses": 0,
            "third_party_executions": 0,
        }
        artifact_hash = _safe_hash(
            {
                "component_id": case_input.component_id,
                "outcome": decision.outcome,
                "reason_codes": list(decision.reason_codes),
                "revision_id": REVISION_ID,
            }
        )
        return build_result(
            context=context,
            case_input=case_input,
            decision=decision,
            evidence=(evidence,),
            artifact_hashes={"component_result": artifact_hash or "0" * 64},
            diagnostics=sanitized,
            terminal_status="COMPLETED" if decision.outcome != "BLOCK" else "FAILED_RETAINED",
        )


def _lineage_binding(
    component_payloads: Mapping[str, Any], state: Mapping[str, Any]
) -> tuple[list[str], dict[str, Any]]:
    reasons: list[str] = []
    repro = component_payloads.get("hash-bound-reproducibility-manifest")
    claim_payload = component_payloads.get("claim-evidence-support-gate")
    manifest = repro.get("manifest") if isinstance(repro, Mapping) else None
    claim = claim_payload.get("claim") if isinstance(claim_payload, Mapping) else None
    verified = (
        claim_payload.get("verified_run_manifest") if isinstance(claim_payload, Mapping) else None
    )
    if not all(isinstance(item, Mapping) for item in (manifest, claim, verified)):
        return ["K1_R1_COMPOSITION_LINEAGE_RECORD_MISSING"], {}
    manifest_hash = _safe_hash(manifest)
    bindings = {
        "run_id": manifest.get("run_id"),
        "run_manifest_hash": manifest_hash,
        "input_hash": manifest.get("input_hash"),
        "code_hash": manifest.get("code_hash", manifest.get("code_commit")),
        "configuration_hash": manifest.get("configuration_hash", manifest.get("config_hash")),
        "output_hash": manifest.get("output_hash"),
        "decision_hash": verified.get("decision_hash", verified.get("artifact_hash")),
        "evidence_artifact_ids": claim.get("evidence_artifact_ids"),
    }
    comparisons = {
        "run_id": claim.get("run_id"),
        "code_hash": claim.get("code_hash", claim.get("code_commit")),
        "output_hash": claim.get("output_hash"),
    }
    if EXACT_EXTENSION_FIELDS & set(claim):
        comparisons["input_hash"] = claim.get("input_hash")
        comparisons["configuration_hash"] = claim.get("configuration_hash")
        comparisons["run_manifest_hash"] = claim.get("run_manifest_hash")
        comparisons["decision_hash"] = claim.get("decision_hash")
    for field, value in comparisons.items():
        if value != bindings.get(field):
            reasons.append(f"K1_R1_COMPOSITION_{field.upper()}_MISMATCH")
    for field in ("run_id", "input_hash", "output_hash"):
        if field in verified and verified.get(field) != bindings.get(field):
            reasons.append(f"K1_R1_COMPOSITION_VERIFIED_{field.upper()}_MISMATCH")
    if "run_manifest_hash" in claim and claim.get("run_manifest_hash") != manifest_hash:
        reasons.append("K1_R1_COMPOSITION_MANIFEST_HASH_MISMATCH")
    trusted_repro = state.get("trusted_repro_manifest_hashes")
    if (
        not isinstance(trusted_repro, Mapping)
        or trusted_repro.get(bindings["run_id"]) != manifest_hash
    ):
        reasons.append("K1_R1_COMPOSITION_MANIFEST_NOT_TRUSTED")
    return reasons, bindings


def _rejection_package(component_results: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": "REJECTED",
        "accepted": False,
        "final": False,
        "ready_for_paper": False,
        "component_results": component_results,
    }


def _handoff_package(
    component_results: Mapping[str, Any],
    lineage: Mapping[str, Any],
    selected_candidate: Any,
) -> dict[str, Any]:
    run_id = lineage.get("run_id")
    return {
        "contract_version": "modeling-to-paper/v1",
        "problem_requirements": [],
        "requirement_traceability": {},
        "data_dictionary": {},
        "data_quality_report": {},
        "assumptions": [],
        "symbols": {},
        "formulas": [],
        "sources": [],
        "selected_models": ([{"candidate_id": selected_candidate}] if selected_candidate else []),
        "final_runs": [
            {
                "run_id": run_id,
                "manifest_hash": lineage.get("run_manifest_hash"),
                "input_hash": lineage.get("input_hash"),
                "code_hash": lineage.get("code_hash"),
                "configuration_hash": lineage.get("configuration_hash"),
                "output_hash": lineage.get("output_hash"),
                "decision_hash": lineage.get("decision_hash"),
            }
        ],
        "final_metrics": {"selected_candidate": selected_candidate},
        "result_tables": [],
        "figure_ready_data": [],
        "validation_results": {"component_results": component_results},
        "robustness_results": {},
        "uncertainty": {},
        "failure_cases": [],
        "limitations": ["COMPETITION_RC1_MACHINE_PROPOSAL; NOT HUMAN APPROVAL"],
        "claim_evidence": {
            "run_id": run_id,
            "evidence_artifact_ids": lineage.get("evidence_artifact_ids") or [],
        },
        "reproduction": {
            "run_id": run_id,
            "manifest_hash": lineage.get("run_manifest_hash"),
        },
        "generated_at": "1970-01-01T00:00:00Z",
        "approved_by": ["MACHINE_TECHNICAL_GATE:K1_R1_COMPOSITION"],
    }


def evaluate_composed_evidence_package_r1(
    component_payloads: Any,
    isolated_state: Any,
    *,
    stage: Any = "PUBLIC_VALIDATION",
    state_binding_hash: Any = None,
    writer: Any = "PROPOSAL_ONLY",
) -> tuple[bool, tuple[str, ...], dict[str, Any]]:
    """Compose Lifecycle -> Manifest -> Claim -> Comparison -> Handoff.

    The composer owns the cross-component lineage check but owns no formal
    state.  Upstream binding changes become transitive STALE statuses with an
    explicit dependency chain; no final candidate or ready handoff is emitted.
    """
    reasons = list(_state_boundary(isolated_state))
    if not isinstance(stage, str) or stage not in ALLOWED_STAGES:
        reasons.append("K1_R1_COMPOSITION_STAGE_BOUNDARY_REJECTED")
    if writer != "PROPOSAL_ONLY":
        reasons.append("K1_R1_COMPOSITION_WRITER_NOT_AUTHORIZED")
    if state_binding_hash is not None and (
        not _valid_hash(state_binding_hash) or state_binding_hash != _safe_hash(isolated_state)
    ):
        reasons.append("K1_R1_COMPOSITION_STATE_BINDING_INVALID")
    if not isinstance(component_payloads, Mapping) or set(component_payloads) != set(COMPONENT_IDS):
        reasons.append("K1_R1_COMPOSITION_INPUT_INVALID")
    if reasons:
        package = _rejection_package({})
        stable = _stable_reasons(reasons)
        return (
            False,
            stable,
            {
                "evidence_package": package,
                "evidence_package_hash": _safe_hash(package),
                "accepted": False,
                "final": False,
                "ready_for_paper": False,
            },
        )

    frozen_payloads = deep_freeze(component_payloads)
    frozen_state = deep_freeze(isolated_state)
    lineage_reasons, lineage = _lineage_binding(frozen_payloads, frozen_state)
    order = (
        "hash-bound-reproducibility-manifest",
        "leakage-safe-model-comparison-gate",
        "claim-evidence-support-gate",
        "accepted-versus-done-workflow-state",
    )
    component_results: dict[str, dict[str, Any]] = {}
    upstream_failed = False
    stale_chain: list[str] = []
    selected_candidate = None
    for component_id in order:
        if upstream_failed:
            stale_chain.append(component_id)
            component_results[component_id] = {
                "status": "STALE",
                "reason_codes": ["K1_R1_COMPOSITION_TRANSITIVE_STALE"],
                "dependency_chain": list(stale_chain),
            }
            reasons.append("K1_R1_COMPOSITION_TRANSITIVE_STALE")
            continue
        try:
            passed, component_reasons, diagnostics = R1_KERNELS[component_id](
                frozen_payloads[component_id], frozen_state
            )
        except Exception:  # noqa: BLE001 - composer fail-closed boundary
            passed = False
            component_reasons = ("K1_R1_COMPOSITION_MALFORMED_INPUT_FAIL_CLOSED",)
            diagnostics = {}
        if component_id == "hash-bound-reproducibility-manifest" and lineage_reasons:
            component_reasons = (*component_reasons, *lineage_reasons)
            passed = False
        stale = any(
            marker in code
            for code in component_reasons
            for marker in ("STALE", "MUTATION", "MISMATCH", "BINDING")
        )
        status = (
            "PASS"
            if passed is True
            else "ABSTAIN"
            if passed is None
            else "STALE"
            if stale
            else "BLOCK"
        )
        component_results[component_id] = {
            "status": status,
            "reason_codes": list(_stable_reasons(component_reasons)),
            "dependency_chain": [component_id],
        }
        if component_id == "leakage-safe-model-comparison-gate":
            selected_candidate = diagnostics.get("selected_candidate")
        if passed is not True:
            reasons.extend(component_reasons or ("K1_R1_COMPOSITION_COMPONENT_FAILED",))
            upstream_failed = True
            stale_chain = [component_id]

    if reasons:
        package = _rejection_package(component_results)
        stable = _stable_reasons(reasons)
        return (
            False,
            stable,
            {
                "evidence_package": package,
                "evidence_package_hash": _safe_hash(package),
                "accepted": False,
                "final": False,
                "ready_for_paper": False,
                "lineage": lineage,
            },
        )
    package = _handoff_package(component_results, lineage, selected_candidate)
    return (
        True,
        (),
        {
            "evidence_package": package,
            "evidence_package_hash": _safe_hash(package),
            "accepted": False,
            "final": False,
            "ready_for_paper": False,
            "proposal_eligible": True,
            "lineage": lineage,
        },
    )


__all__ = [
    "ARCHITECTURE_ID",
    "REVISION_ID",
    "DeterministicEvidenceKernelRevisionR1",
    "evaluate_claim_support_r1",
    "evaluate_composed_evidence_package_r1",
    "evaluate_model_comparison_r1",
    "evaluate_reproducibility_r1",
    "verified_run_record_r1",
]
