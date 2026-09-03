"""Stateless workflow checklists implementing the four frozen component contracts."""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Mapping
from pathlib import PurePosixPath
from typing import Any

from experiments.shadow_prototypes.common.interface import canonical_json, sha256_json

WORKFLOW_STAGES = (
    "TASK_CREATED",
    "EXECUTION_STARTED",
    "COMMAND_COMPLETED",
    "ARTIFACT_PRODUCED",
    "AUTOMATIC_VALIDATION_PASSED",
    "AUTOMATIC_ADJUDICATION_ACCEPTED",
    "FINAL_EVIDENCE_FROZEN",
    "FORMALLY_INTEGRATED",
)
REPRODUCIBILITY_FIELDS = frozenset(
    {
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
)
RUN_BINDING_FIELDS = ("run_id", "input_hash", "code_commit", "output_hash", "lineage")
STRENGTH_RANK = {"NONE": 0, "WEAK": 1, "MODERATE": 2, "STRONG": 3}
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
PRIVATE_KEYS = frozenset(
    {
        "api_key",
        "access_token",
        "password",
        "credential",
        "secret",
        "browser_state",
        "hidden_reasoning",
        "raw_trace",
        "private_path",
    }
)


def _valid_hash(value: Any, *, commit: bool = False) -> bool:
    return bool((HEX_40 if commit else HEX_64).fullmatch(str(value)))


def _state_boundary(isolated_state: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if isolated_state.get("truth_source") != "state/project_state.json":
        reasons.append("W1_SINGLE_STATE_TRUTH_REQUIRED")
    if isolated_state.get("formal_state_writes_allowed") is not False:
        reasons.append("W1_FORMAL_STATE_WRITE_BOUNDARY_INVALID")
    return reasons


def _contains_private_value(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key).lower() in PRIVATE_KEYS or _contains_private_value(item)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_private_value(item) for item in value)
    return isinstance(value, str) and (value.startswith(("/", "~")) or "credential=" in value)


def _gate_record_valid(component_id: str, value: Any, isolated_state: Mapping[str, Any]) -> bool:
    if not isinstance(value, Mapping):
        return False
    body = {
        key: value.get(key)
        for key in (
            "component_id",
            "decision_id",
            "run_id",
            "authority",
            "outcome",
            "current",
            "audited",
        )
    }
    trusted_hashes = isolated_state.get("trusted_gate_hashes", {})
    trusted_runs = set(isolated_state.get("trusted_run_ids", ()))
    return (
        value.get("component_id") == component_id
        and bool(value.get("decision_id"))
        and value.get("run_id") in trusted_runs
        and value.get("authority") == "existing-native-component-ledger"
        and value.get("outcome") == "PASS"
        and value.get("current") is True
        and value.get("audited") is True
        and value.get("artifact_hash") == sha256_json(body)
        and isinstance(trusted_hashes, Mapping)
        and value.get("artifact_hash") == trusted_hashes.get(component_id)
    )


def _verified_manifest_valid(
    value: Any, isolated_state: Mapping[str, Any], *, run_id: str | None = None
) -> bool:
    trusted_runs = set(isolated_state.get("trusted_run_ids", ()))
    trusted_hashes = isolated_state.get("trusted_manifest_hashes", {})
    return bool(
        isinstance(value, Mapping)
        and (run_id is None or value.get("run_id") == run_id)
        and value.get("run_id") in trusted_runs
        and value.get("decision_id")
        and value.get("authority") == "existing-native-run-ledger"
        and value.get("status") == "PASS"
        and value.get("current") is True
        and value.get("audited") is True
        and _valid_hash(value.get("artifact_hash"))
        and isinstance(trusted_hashes, Mapping)
        and value.get("artifact_hash") == trusted_hashes.get(value.get("run_id"))
    )


def workflow_checklist(
    payload: Mapping[str, Any], isolated_state: Mapping[str, Any]
) -> tuple[bool, tuple[str, ...], dict[str, Any]]:
    reasons = _state_boundary(isolated_state)
    evidenced = tuple(str(item) for item in payload.get("evidenced_stages", ()))
    requested = str(payload.get("requested_state", ""))
    if payload.get("state_truth_path") != "state/project_state.json":
        reasons.append("W1_WORKFLOW_STATE_TRUTH_MISMATCH")
    if requested not in WORKFLOW_STAGES:
        reasons.append("W1_WORKFLOW_UNKNOWN_STATE")
        expected_prefix: tuple[str, ...] = ()
    else:
        requested_index = WORKFLOW_STAGES.index(requested)
        expected_prefix = WORKFLOW_STAGES[: requested_index + 1]
        if evidenced != expected_prefix:
            reasons.append("W1_WORKFLOW_STAGE_EVIDENCE_INCOMPLETE")
    records = payload.get("evidence_records", {})
    trusted_stage_hashes = isolated_state.get("trusted_stage_hashes", {})
    trusted_runs = set(isolated_state.get("trusted_run_ids", ()))
    if not isinstance(records, Mapping):
        reasons.append("W1_WORKFLOW_EVIDENCE_REGISTRY_INVALID")
    else:
        for stage in expected_prefix:
            record = records.get(stage)
            if not isinstance(record, Mapping):
                reasons.append("W1_WORKFLOW_STAGE_RECORD_MISSING")
                continue
            if record.get("registered") is not True or record.get("current") is not True:
                reasons.append("W1_WORKFLOW_STAGE_RECORD_NOT_CURRENT")
            artifact_body = record.get("artifact_body")
            artifact_hash = record.get("artifact_hash")
            if (
                record.get("authority") != "existing-state-transition-ledger"
                or not isinstance(artifact_body, Mapping)
                or artifact_body.get("stage") != stage
                or artifact_body.get("run_id") not in trusted_runs
                or not _valid_hash(artifact_hash)
                or artifact_hash != sha256_json(artifact_body)
                or not isinstance(trusted_stage_hashes, Mapping)
                or artifact_hash != trusted_stage_hashes.get(stage)
            ):
                reasons.append("W1_WORKFLOW_STAGE_HASH_INVALID")
            if stage == "AUTOMATIC_ADJUDICATION_ACCEPTED" and record.get("audited") is not True:
                reasons.append("W1_WORKFLOW_ACCEPTANCE_NOT_AUDITED")
    if payload.get("actor") != "MAIN_AGENT_FORMAL_STATE_WRITER":
        reasons.append("W1_WORKFLOW_UNAUTHORIZED_WRITER")
    changed = {str(item) for item in payload.get("changed_nodes", ())}
    graph = payload.get("dependency_graph", {})
    if not isinstance(graph, Mapping) or any(
        not isinstance(dependents, (list, tuple)) for dependents in graph.values()
    ):
        reasons.append("W1_WORKFLOW_DEPENDENCY_GRAPH_INVALID")
    stale: set[str] = set(changed)
    frontier = list(changed)
    while frontier:
        node = frontier.pop()
        dependents = graph.get(node, ()) if isinstance(graph, Mapping) else ()
        if not isinstance(dependents, (list, tuple)):
            reasons.append("W1_WORKFLOW_DEPENDENCY_GRAPH_INVALID")
            continue
        for dependent in dependents:
            dependent = str(dependent)
            if dependent not in stale:
                stale.add(dependent)
                frontier.append(dependent)
    if stale:
        reasons.append("W1_WORKFLOW_STALE_DEPENDENCY")
    if payload.get("narrative_override"):
        reasons.append("W1_WORKFLOW_NARRATIVE_BYPASS_REJECTED")
    challenge = payload.get("team_challenge", {})
    if isinstance(challenge, Mapping) and challenge.get("supported") is True:
        reasons.append("W1_WORKFLOW_SUPPORTED_CHALLENGE_STALE")
        target = challenge.get("target")
        if not isinstance(target, str) or not target:
            reasons.append("W1_WORKFLOW_CHALLENGE_TARGET_MISSING")
        else:
            challenge_frontier = [target]
            while challenge_frontier:
                node = challenge_frontier.pop()
                if node in stale:
                    continue
                stale.add(node)
                dependents = graph.get(node, ()) if isinstance(graph, Mapping) else ()
                if not isinstance(dependents, (list, tuple)):
                    reasons.append("W1_WORKFLOW_DEPENDENCY_GRAPH_INVALID")
                    continue
                challenge_frontier.extend(str(item) for item in dependents)
    upstream = payload.get("upstream_gates", {})
    if not isinstance(upstream, Mapping) or any(
        not _gate_record_valid(component, upstream.get(component), isolated_state)
        for component in (
            "claim-evidence-support-gate",
            "leakage-safe-model-comparison-gate",
        )
    ):
        reasons.append("W1_WORKFLOW_REQUIRED_GATE_NOT_PASS")
    return not reasons, tuple(sorted(set(reasons))), {"stale_nodes": sorted(stale)}


def claim_checklist(
    payload: Mapping[str, Any], isolated_state: Mapping[str, Any]
) -> tuple[bool, tuple[str, ...], dict[str, Any]]:
    reasons = _state_boundary(isolated_state)
    claim = payload.get("claim", {})
    if not isinstance(claim, Mapping):
        return False, ("W1_CLAIM_RECORD_INVALID",), {"supporting_evidence": []}
    run_id = str(claim.get("run_id", ""))
    manifest = payload.get("verified_run_manifest", {})
    if not _verified_manifest_valid(manifest, isolated_state, run_id=run_id):
        reasons.append("W1_CLAIM_VERIFIED_RUN_MANIFEST_REQUIRED")
    evidence_raw = payload.get("evidence")
    if not isinstance(evidence_raw, (list, tuple)):
        evidence: tuple[Any, ...] = ()
        reasons.append("W1_CLAIM_EVIDENCE_SET_INVALID")
    else:
        evidence = tuple(evidence_raw)
    trusted_run_bindings = isolated_state.get("trusted_run_bindings", {})
    run_binding = (
        trusted_run_bindings.get(run_id) if isinstance(trusted_run_bindings, Mapping) else None
    )
    if not isinstance(run_binding, Mapping) or any(
        claim.get(field) != run_binding.get(field) for field in RUN_BINDING_FIELDS
    ):
        reasons.append("W1_CLAIM_RUN_BINDING_MISMATCH")
    supporting = []
    for item in evidence:
        if not isinstance(item, Mapping):
            reasons.append("W1_CLAIM_EVIDENCE_RECORD_INVALID")
            continue
        if not item.get("registered") or not item.get("locator"):
            reasons.append("W1_CLAIM_EVIDENCE_NOT_REGISTERED")
            continue
        locator = PurePosixPath(str(item.get("locator")))
        if (
            not locator.parts
            or locator.is_absolute()
            or ".." in locator.parts
            or locator.parts[0]
            not in {
                "runs",
                "sources",
            }
        ):
            reasons.append("W1_CLAIM_EVIDENCE_LOCATOR_UNSAFE")
        if item.get("authority") != "existing-native-run-ledger":
            reasons.append("W1_CLAIM_EVIDENCE_AUTHORITY_INVALID")
        artifact_hash = item.get("artifact_hash")
        artifact_body = item.get("artifact_body")
        trusted_artifact_hashes = isolated_state.get("trusted_artifact_hashes", {})
        if (
            not isinstance(artifact_body, Mapping)
            or not _valid_hash(artifact_hash)
            or artifact_hash != sha256_json(artifact_body)
            or not isinstance(trusted_artifact_hashes, Mapping)
            or artifact_hash != trusted_artifact_hashes.get(str(item.get("locator")))
        ):
            reasons.append("W1_CLAIM_EVIDENCE_HASH_INVALID")
        expected_registry_hash = sha256_json(
            {"locator": str(item.get("locator")), "artifact_hash": artifact_hash}
        )
        if item.get("registry_hash") != expected_registry_hash:
            reasons.append("W1_CLAIM_EVIDENCE_REGISTRY_MISMATCH")
        if item.get("contradicts"):
            reasons.append("W1_CLAIM_CONTRADICTED")
        if item.get("current") is not True:
            reasons.append("W1_CLAIM_STALE_EVIDENCE")
        if item.get("run_id") != run_id:
            reasons.append("W1_CLAIM_RUN_BINDING_MISMATCH")
        semantic_fields = (
            "bounded_proposition",
            "scope",
            "modality",
            "strength",
            "evidence_type",
            *RUN_BINDING_FIELDS,
            "revision_id",
            "prior_revision_hash",
            "superseded",
        )
        semantics_bound = isinstance(artifact_body, Mapping) and not any(
            item.get(field) != artifact_body.get(field) for field in semantic_fields
        )
        if not semantics_bound:
            reasons.append("W1_CLAIM_EVIDENCE_SEMANTIC_BINDING_MISMATCH")
        exact = semantics_bound and all(
            artifact_body.get(field) == claim.get(field) for field in ("scope", "modality")
        )
        exact = exact and artifact_body.get("bounded_proposition") == claim.get("proposition")
        strength = artifact_body.get("strength") if isinstance(artifact_body, Mapping) else None
        claim_strength = claim.get("strength")
        adequate = bool(
            strength in STRENGTH_RANK
            and claim_strength in STRENGTH_RANK
            and STRENGTH_RANK[strength] >= STRENGTH_RANK[claim_strength]
            and STRENGTH_RANK[strength] >= STRENGTH_RANK["MODERATE"]
        )
        run_bound = isinstance(run_binding, Mapping) and all(
            artifact_body.get(field) == run_binding.get(field) for field in RUN_BINDING_FIELDS
        )
        if exact and adequate and run_bound and item.get("superseded") is False:
            supporting.append(str(item.get("evidence_id", "")))
    if not supporting:
        reasons.append("W1_CLAIM_EXACT_SUPPORT_MISSING")
    if claim.get("claim_type") == "FINAL":
        reasons.append("W1_CLAIM_FORMAL_FINAL_PROHIBITED")
    if claim.get("claim_type") == "CAUSAL":
        identification = claim.get("causal_identification")
        if not isinstance(identification, Mapping) or not (
            identification.get("design") in {"RANDOMIZED", "VALID_INSTRUMENT", "NATURAL_EXPERIMENT"}
            and _valid_hash(identification.get("analysis_hash"))
            and all(
                isinstance(item.get("artifact_body"), Mapping)
                and item["artifact_body"].get("modality") == "causal"
                for item in evidence
                if isinstance(item, Mapping)
            )
        ):
            reasons.append("W1_CLAIM_CAUSAL_SUPPORT_INADEQUATE")
    if payload.get("narrative_override"):
        reasons.append("W1_CLAIM_NARRATIVE_BYPASS_REJECTED")
    return not reasons, tuple(sorted(set(reasons))), {"supporting_evidence": sorted(supporting)}


def reproducibility_checklist(
    payload: Mapping[str, Any], isolated_state: Mapping[str, Any]
) -> tuple[bool, tuple[str, ...], dict[str, Any]]:
    reasons = _state_boundary(isolated_state)
    manifest = payload.get("manifest", {})
    capture = payload.get("trusted_capture", {})
    trusted_runs = set(isolated_state.get("trusted_run_ids", ()))
    if not isinstance(manifest, Mapping) or not set(manifest) >= REPRODUCIBILITY_FIELDS:
        reasons.append("W1_MANIFEST_REQUIRED_BINDING_MISSING")
    elif not (
        _valid_hash(manifest.get("input_hash"))
        and _valid_hash(manifest.get("code_commit"), commit=True)
        and _valid_hash(manifest.get("config_hash"))
        and _valid_hash(manifest.get("environment_hash"))
        and _valid_hash(manifest.get("dependency_hash"))
        and _valid_hash(manifest.get("output_hash"))
    ):
        reasons.append("W1_MANIFEST_HASH_FORMAT_INVALID")
    if not isinstance(manifest, Mapping) or manifest.get("run_id") not in trusted_runs:
        reasons.append("W1_MANIFEST_REGISTERED_RUN_REQUIRED")
    if not isinstance(capture, Mapping):
        reasons.append("W1_MANIFEST_TRUSTED_CAPTURE_MISSING")
    elif isinstance(manifest, Mapping):
        computed = {
            "run_id": capture.get("run_id"),
            "revision_id": capture.get("revision_id"),
            "prior_manifest_hash": capture.get("prior_manifest_hash"),
            "current": capture.get("current"),
            "authority": capture.get("authority"),
            "input_hash": sha256_json(capture.get("input_content")),
            "code_commit": capture.get("code_commit"),
            "config_hash": sha256_json(capture.get("config_content")),
            "seed": capture.get("seed"),
            "command": capture.get("command"),
            "cwd": capture.get("cwd"),
            "environment_hash": sha256_json(capture.get("environment")),
            "dependency_hash": sha256_json(capture.get("dependencies")),
            "output_hash": sha256_json(capture.get("output_content")),
            "outcome": capture.get("outcome"),
        }
        if canonical_json(manifest) != canonical_json(computed):
            reasons.append("W1_MANIFEST_BINDING_MISMATCH")
        trusted_manifests = isolated_state.get("trusted_repro_manifest_hashes", {})
        trusted_captures = isolated_state.get("trusted_capture_hashes", {})
        if not isinstance(trusted_manifests, Mapping) or sha256_json(
            manifest
        ) != trusted_manifests.get(manifest.get("run_id")):
            reasons.append("W1_MANIFEST_UNTRUSTED_REVISION")
        if not isinstance(trusted_captures, Mapping) or sha256_json(
            capture
        ) != trusted_captures.get(manifest.get("run_id")):
            reasons.append("W1_MANIFEST_UNTRUSTED_CAPTURE")
    command = manifest.get("command") if isinstance(manifest, Mapping) else None
    cwd = manifest.get("cwd") if isinstance(manifest, Mapping) else None
    if (
        not isinstance(command, (list, tuple))
        or not command
        or not all(isinstance(item, str) and item for item in command)
    ):
        reasons.append("W1_MANIFEST_ARGV_REQUIRED")
    if not isinstance(cwd, str) or cwd.startswith(("/", "~")) or ".." in cwd.split("/"):
        reasons.append("W1_MANIFEST_CWD_UNSAFE")
    if _contains_private_value(payload):
        reasons.append("W1_MANIFEST_PRIVATE_FIELD_REJECTED")
    outcome = manifest.get("outcome") if isinstance(manifest, Mapping) else None
    if outcome != "SUCCESS":
        reasons.append(f"W1_MANIFEST_OUTCOME_NOT_SUCCESS:{outcome}")
    return (
        not reasons,
        tuple(sorted(set(reasons))),
        {
            "canonical_manifest_hash": sha256_json(manifest)
            if isinstance(manifest, Mapping)
            else None
        },
    )


def comparison_checklist(
    payload: Mapping[str, Any], isolated_state: Mapping[str, Any]
) -> tuple[bool, tuple[str, ...], dict[str, Any]]:
    reasons = _state_boundary(isolated_state)
    splits = payload.get("splits")
    if not isinstance(splits, Mapping):
        split_sets = [set(), set(), set()]
        reasons.append("W1_COMPARISON_SPLIT_INVALID")
    else:
        try:
            split_values = [splits.get(name) for name in ("train", "validation", "test")]
            if any(
                not isinstance(value, (list, tuple))
                or not value
                or any(not isinstance(item, str) or not item for item in value)
                for value in split_values
            ):
                raise TypeError
            split_sets = [set(value) for value in split_values]
        except (TypeError, ValueError):
            split_sets = [set(), set(), set()]
            reasons.append("W1_COMPARISON_SPLIT_INVALID")
    if not all(split_sets) or any(
        left & right for index, left in enumerate(split_sets) for right in split_sets[index + 1 :]
    ):
        reasons.append("W1_COMPARISON_SPLIT_INVALID")
    if payload.get("group_overlap"):
        reasons.append("W1_COMPARISON_GROUP_LEAKAGE")
    if payload.get("time_order_valid") is not True:
        reasons.append("W1_COMPARISON_TIME_LEAKAGE")
    if payload.get("future_feature") or payload.get("target_feature"):
        reasons.append("W1_COMPARISON_FEATURE_LEAKAGE")
    if payload.get("transform_fit_scope") != "train":
        reasons.append("W1_COMPARISON_TRANSFORM_LEAKAGE")
    if set(payload.get("baselines", ())) != {"naive", "domain"}:
        reasons.append("W1_COMPARISON_BASELINE_MISSING")
    for field in ("candidate_freeze_hash", "metric_freeze_hash"):
        if not _valid_hash(payload.get(field)):
            reasons.append(f"W1_COMPARISON_FREEZE_INVALID:{field}")
    if tuple(payload.get("freeze_order", ())) != (
        "split",
        "candidates",
        "metric",
        "attempts",
        "model",
        "test",
    ):
        reasons.append("W1_COMPARISON_FREEZE_ORDER_INVALID")
    if payload.get("dependency_current") is not True:
        reasons.append("W1_COMPARISON_STALE_DEPENDENCY")
    if payload.get("selected_candidate_matches_validation") is not True:
        reasons.append("W1_COMPARISON_SELECTION_MISMATCH")
    if payload.get("failures_retained") is not True:
        reasons.append("W1_COMPARISON_FAILURE_OMITTED")
    attempts = payload.get("attempts", ())
    seeds = set(payload.get("frozen_seeds", ()))
    candidate_seed_pairs: Counter[tuple[str, Any]] = Counter()
    if not isinstance(attempts, (list, tuple)) or not attempts:
        reasons.append("W1_COMPARISON_ATTEMPT_LEDGER_MISSING")
    else:
        for attempt in attempts:
            if not isinstance(attempt, Mapping):
                reasons.append("W1_COMPARISON_ATTEMPT_INVALID")
                continue
            if attempt.get("seed") not in seeds or attempt.get("terminal") is not True:
                reasons.append("W1_COMPARISON_UNSCHEDULED_OR_NONTERMINAL_ATTEMPT")
            candidate_seed_pairs[(str(attempt.get("candidate_id")), attempt.get("seed"))] += 1
            if attempt.get("retry") and attempt.get("infrastructure_failure") is not True:
                reasons.append("W1_COMPARISON_UNAUTHORIZED_RETRY")
    scores = payload.get("validation_scores")
    numeric_scores: dict[str, float] = {}
    scores_valid = isinstance(scores, Mapping) and bool(scores)
    if not scores_valid:
        reasons.append("W1_COMPARISON_VALIDATION_SCORES_MISSING")
        reasons.append("W1_COMPARISON_NO_VALID_CANDIDATE")
    else:
        for candidate, raw_score in scores.items():
            if not isinstance(candidate, str) or not candidate:
                reasons.append("W1_COMPARISON_CANDIDATE_INVALID")
                scores_valid = False
                continue
            try:
                score = float(raw_score)
            except (TypeError, ValueError, OverflowError):
                reasons.append("W1_COMPARISON_SCORE_INVALID")
                scores_valid = False
                continue
            if isinstance(raw_score, bool) or not math.isfinite(score):
                reasons.append("W1_COMPARISON_NONFINITE_SELECTION_METRIC")
                scores_valid = False
                continue
            numeric_scores[candidate] = score
        if not numeric_scores:
            reasons.append("W1_COMPARISON_NO_VALID_CANDIDATE")
        frozen_policy = isolated_state.get("comparison_policy", {})
        observed_policy = {
            "metric_direction": payload.get("metric_direction"),
            "tie_tolerance": payload.get("tie_tolerance"),
            "ordered_tie_keys": list(payload.get("ordered_tie_keys", ())),
        }
        normalized_frozen_policy = (
            {
                "metric_direction": frozen_policy.get("metric_direction"),
                "tie_tolerance": frozen_policy.get("tie_tolerance"),
                "ordered_tie_keys": list(frozen_policy.get("ordered_tie_keys", ())),
            }
            if isinstance(frozen_policy, Mapping)
            else {}
        )
        if observed_policy != normalized_frozen_policy:
            reasons.append("W1_COMPARISON_POLICY_NOT_FROZEN")
        direction = (
            frozen_policy.get("metric_direction") if isinstance(frozen_policy, Mapping) else None
        )
        tolerance = (
            frozen_policy.get("tie_tolerance") if isinstance(frozen_policy, Mapping) else None
        )
        tie_keys = (
            frozen_policy.get("ordered_tie_keys") if isinstance(frozen_policy, Mapping) else None
        )
        if (
            direction not in {"MAXIMIZE", "MINIMIZE"}
            or not isinstance(tolerance, (int, float))
            or isinstance(tolerance, bool)
            or not math.isfinite(float(tolerance))
            or tolerance < 0
            or list(tie_keys or ()) != ["candidate_id"]
        ):
            reasons.append("W1_COMPARISON_POLICY_INVALID")
            winner = ""
        elif not scores_valid:
            winner = ""
        else:
            optimum = (
                max(numeric_scores.values())
                if direction == "MAXIMIZE"
                else min(numeric_scores.values())
            )
            tied = [
                candidate
                for candidate, score in numeric_scores.items()
                if abs(score - optimum) <= float(tolerance)
            ]
            if not tied:
                reasons.append("W1_COMPARISON_EMPTY_TIE_SET")
                winner = ""
            else:
                winner = sorted(tied)[0]
        if not winner or payload.get("selected_candidate_id") != winner:
            reasons.append("W1_COMPARISON_SELECTION_MISMATCH")
        required_pairs = Counter(
            {(candidate, seed): 1 for candidate in numeric_scores for seed in seeds}
        )
        if candidate_seed_pairs != required_pairs:
            reasons.append("W1_COMPARISON_CANDIDATE_SEED_MATRIX_INCOMPLETE")
    manifests = payload.get("verified_run_manifests", ())
    manifest_run_ids = (
        Counter(str(item.get("run_id")) for item in manifests if isinstance(item, Mapping))
        if isinstance(manifests, (list, tuple))
        else Counter()
    )
    expected_run_ids = (
        Counter({f"{candidate}-{seed}": 1 for candidate in numeric_scores for seed in seeds})
        if numeric_scores
        else Counter()
    )
    if (
        not isinstance(manifests, (list, tuple))
        or not manifests
        or any(not _verified_manifest_valid(item, isolated_state) for item in manifests)
        or manifest_run_ids != expected_run_ids
    ):
        reasons.append("W1_COMPARISON_VERIFIED_RUNS_REQUIRED")
    events_raw = payload.get("access_events")
    if not isinstance(events_raw, (list, tuple)):
        reasons.append("W1_COMPARISON_ACCESS_LEDGER_INVALID")
        events: tuple[Any, ...] = ()
    else:
        events = tuple(events_raw)
    prior_hash = "0" * 64
    valid_events: list[Mapping[str, Any]] = []
    for event in events:
        if not isinstance(event, Mapping):
            reasons.append("W1_COMPARISON_ACCESS_EVENT_INVALID")
            continue
        body = {
            key: event.get(key)
            for key in (
                "ordinal",
                "kind",
                "after_model_freeze",
                "prior_hash",
                "run_id",
                "model_freeze_hash",
                "pretest_decision_hash",
                "test_set_id",
            )
        }
        if event.get("prior_hash") != prior_hash or event.get("event_hash") != sha256_json(body):
            reasons.append("W1_COMPARISON_ACCESS_CHAIN_BROKEN")
        if (
            event.get("run_id") != payload.get("run_id")
            or event.get("model_freeze_hash") != isolated_state.get("trusted_model_freeze_hash")
            or event.get("pretest_decision_hash")
            != isolated_state.get("trusted_pretest_decision_hash")
            or event.get("test_set_id") != isolated_state.get("trusted_test_set_id")
        ):
            reasons.append("W1_COMPARISON_ACCESS_EVENT_BINDING_INVALID")
        prior_hash = str(event.get("event_hash", ""))
        valid_events.append(event)
    premature = [
        event
        for event in valid_events
        if event.get("kind") != "FINAL_TEST_BATCH" or event.get("after_model_freeze") is not True
    ]
    final_batches = [event for event in valid_events if event.get("kind") == "FINAL_TEST_BATCH"]
    if premature:
        reasons.append("W1_COMPARISON_PREMATURE_TEST_ACCESS")
    if payload.get("model_frozen") is not True or len(final_batches) != 1:
        reasons.append("W1_COMPARISON_FINAL_TEST_COUNT_INVALID")
    trusted_heads = isolated_state.get("trusted_access_heads", {})
    if not isinstance(trusted_heads, Mapping) or prior_hash != trusted_heads.get(
        payload.get("run_id")
    ):
        reasons.append("W1_COMPARISON_ACCESS_HEAD_NOT_TRUSTED")
    if payload.get("test_set_id") in set(isolated_state.get("exposed_test_set_ids", ())):
        reasons.append("W1_COMPARISON_EXPOSED_TEST_SET_REJECTED")
    return (
        not reasons,
        tuple(sorted(set(reasons))),
        {
            "premature_access_count": len(premature),
            "final_test_access_count": len(final_batches),
        },
    )


__all__ = [
    "claim_checklist",
    "comparison_checklist",
    "reproducibility_checklist",
    "workflow_checklist",
]
