"""Deterministic split, attempt, selection, and test-access kernel."""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Mapping
from typing import Any

from experiments.shadow_prototypes.common.interface import sha256_json

from .reproducibility import verified_run_record

HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _finite_scores(value: Any) -> dict[str, float] | None:
    if not isinstance(value, Mapping) or not value:
        return None
    scores: dict[str, float] = {}
    for key, raw_score in value.items():
        if isinstance(raw_score, bool):
            return None
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(score):
            return None
        scores[str(key)] = score
    return scores


def _selection(scores: Mapping[str, float], policy: Mapping[str, Any]) -> tuple[str | None, bool]:
    direction = policy.get("metric_direction")
    tolerance = policy.get("tie_tolerance")
    tie_keys = list(policy.get("ordered_tie_keys", ()))
    if (
        direction not in {"MAXIMIZE", "MINIMIZE"}
        or not isinstance(tolerance, (int, float))
        or isinstance(tolerance, bool)
        or not math.isfinite(float(tolerance))
        or tolerance < 0
        or tie_keys != ["candidate_id"]
    ):
        return None, False
    optimum = max(scores.values()) if direction == "MAXIMIZE" else min(scores.values())
    tied = sorted(
        candidate for candidate, score in scores.items() if abs(score - optimum) <= float(tolerance)
    )
    return (tied[0] if tied else None), True


def evaluate_model_comparison(
    payload: Mapping[str, Any], isolated_state: Mapping[str, Any]
) -> tuple[bool, tuple[str, ...], dict[str, Any]]:
    reasons: list[str] = []
    splits = payload.get("splits")
    if not isinstance(splits, Mapping):
        split_sets = [set(), set(), set()]
        reasons.append("K1_COMPARISON_SPLIT_INVALID")
    else:
        try:
            split_sets = [set(splits.get(name, ())) for name in ("train", "validation", "test")]
        except TypeError:
            split_sets = [set(), set(), set()]
            reasons.append("K1_COMPARISON_SPLIT_INVALID")
    if not all(split_sets) or any(
        left & right for index, left in enumerate(split_sets) for right in split_sets[index + 1 :]
    ):
        reasons.append("K1_COMPARISON_SPLIT_INVALID")
    if payload.get("group_overlap"):
        reasons.append("K1_COMPARISON_GROUP_LEAKAGE")
    if payload.get("time_order_valid") is not True:
        reasons.append("K1_COMPARISON_TIME_LEAKAGE")
    if payload.get("future_feature") or payload.get("target_feature"):
        reasons.append("K1_COMPARISON_FEATURE_LEAKAGE")
    if payload.get("transform_fit_scope") != "train":
        reasons.append("K1_COMPARISON_TRANSFORM_LEAKAGE")
    baselines = payload.get("baselines")
    if not isinstance(baselines, (list, tuple)) or set(baselines) != {"naive", "domain"}:
        reasons.append("K1_COMPARISON_BASELINE_MISSING")
    freeze_bindings = {
        "candidate_freeze_hash": isolated_state.get("trusted_candidate_freeze_hash"),
        "metric_freeze_hash": isolated_state.get("trusted_metric_freeze_hash"),
    }
    for field, trusted in freeze_bindings.items():
        value = payload.get(field)
        if not isinstance(value, str) or not HEX64.fullmatch(value) or value != trusted:
            reasons.append(f"K1_COMPARISON_FREEZE_INVALID:{field}")
    if tuple(payload.get("freeze_order", ())) != (
        "split",
        "candidates",
        "metric",
        "attempts",
        "model",
        "test",
    ):
        reasons.append("K1_COMPARISON_FREEZE_ORDER_INVALID")
    if payload.get("dependency_current") is not True:
        reasons.append("K1_COMPARISON_STALE_DEPENDENCY")
    if payload.get("failures_retained") is not True:
        reasons.append("K1_COMPARISON_FAILURE_NOT_RETAINED")

    policy = isolated_state.get("comparison_policy")
    observed_policy = {
        "metric_direction": payload.get("metric_direction"),
        "tie_tolerance": payload.get("tie_tolerance"),
        "ordered_tie_keys": list(payload.get("ordered_tie_keys", ())),
    }
    normalized_policy = (
        {
            "metric_direction": policy.get("metric_direction"),
            "tie_tolerance": policy.get("tie_tolerance"),
            "ordered_tie_keys": list(policy.get("ordered_tie_keys", ())),
        }
        if isinstance(policy, Mapping)
        else {}
    )
    if observed_policy != normalized_policy:
        reasons.append("K1_COMPARISON_POLICY_NOT_FROZEN")
    comparison_design = {
        "splits": payload.get("splits"),
        "group_overlap": payload.get("group_overlap"),
        "time_order_valid": payload.get("time_order_valid"),
        "future_feature": payload.get("future_feature"),
        "target_feature": payload.get("target_feature"),
        "transform_fit_scope": payload.get("transform_fit_scope"),
        "baselines": payload.get("baselines"),
        "policy": observed_policy,
    }
    if sha256_json(comparison_design) != isolated_state.get("trusted_comparison_design_hash"):
        reasons.append("K1_COMPARISON_DESIGN_BINDING_INVALID")
    scores = _finite_scores(payload.get("validation_scores"))
    if scores is None:
        reasons.append("K1_COMPARISON_SCORE_INVALID")
        scores = {}
    winner, policy_valid = (
        _selection(scores, policy if isinstance(policy, Mapping) else {})
        if scores
        else (None, False)
    )
    if not policy_valid:
        reasons.append("K1_COMPARISON_POLICY_INVALID")
    if winner is None or payload.get("selected_candidate_id") != winner:
        reasons.append("K1_COMPARISON_SELECTION_MISMATCH")
    if payload.get("selected_candidate_matches_validation") is not True:
        reasons.append("K1_COMPARISON_SELECTION_ASSERTION_MISSING")

    trusted_candidates = tuple(str(item) for item in isolated_state.get("trusted_candidates", ()))
    if tuple(sorted(scores)) != tuple(sorted(trusted_candidates)):
        reasons.append("K1_COMPARISON_CANDIDATE_SET_NOT_FROZEN")

    seeds_raw = payload.get("frozen_seeds")
    if not isinstance(seeds_raw, (list, tuple)) or not seeds_raw:
        seeds: set[Any] = set()
        reasons.append("K1_COMPARISON_SEED_FREEZE_INVALID")
    else:
        try:
            seeds = set(seeds_raw)
        except TypeError:
            seeds = set()
            reasons.append("K1_COMPARISON_SEED_FREEZE_INVALID")
    trusted_seeds_raw = isolated_state.get("trusted_seeds", ())
    try:
        trusted_seeds = set(trusted_seeds_raw)
    except TypeError:
        trusted_seeds = set()
    if seeds != trusted_seeds or len(seeds) != len(tuple(trusted_seeds_raw)):
        reasons.append("K1_COMPARISON_SEED_SCHEDULE_NOT_FROZEN")
    required_pairs = Counter({(candidate, seed): 1 for candidate in scores for seed in seeds})
    attempts = payload.get("attempts")
    primary_pairs: Counter[tuple[str, Any]] = Counter()
    attempt_run_ids: Counter[str] = Counter()
    attempts_by_run: dict[str, Mapping[str, Any]] = {}
    valid_attempts: list[Mapping[str, Any]] = []
    if not isinstance(attempts, (list, tuple)) or not attempts:
        reasons.append("K1_COMPARISON_ATTEMPT_LEDGER_INVALID")
    else:
        for attempt in attempts:
            if not isinstance(attempt, Mapping):
                reasons.append("K1_COMPARISON_ATTEMPT_LEDGER_INVALID")
                continue
            pair = (str(attempt.get("candidate_id")), attempt.get("seed"))
            run_id = attempt.get("run_id")
            try:
                if attempt.get("retry") is not True:
                    primary_pairs[pair] += 1
            except TypeError:
                reasons.append("K1_COMPARISON_ATTEMPT_LEDGER_INVALID")
                continue
            if pair not in required_pairs or attempt.get("terminal") is not True:
                reasons.append("K1_COMPARISON_UNSCHEDULED_OR_NONTERMINAL_ATTEMPT")
            if not isinstance(run_id, str) or not run_id:
                reasons.append("K1_COMPARISON_ATTEMPT_RUN_ID_INVALID")
            else:
                attempt_run_ids[run_id] += 1
                attempts_by_run[run_id] = attempt
            valid_attempts.append(attempt)
            if attempt.get("outcome") not in {"SUCCESS", "FAILED", "PARTIAL", "SUPERSEDED"}:
                reasons.append("K1_COMPARISON_ATTEMPT_OUTCOME_INVALID")
            if not attempt.get("failure_class"):
                reasons.append("K1_COMPARISON_FAILURE_CLASS_MISSING")
    for attempt in valid_attempts:
        run_id = attempt.get("run_id")
        if attempt.get("retry") is True:
            predecessor_id = attempt.get("predecessor_run_id")
            predecessor = attempts_by_run.get(str(predecessor_id))
            if (
                attempt.get("infrastructure_failure") is not True
                or not isinstance(predecessor, Mapping)
                or predecessor.get("outcome") != "FAILED"
                or predecessor.get("failure_class") != "INFRASTRUCTURE"
                or predecessor.get("candidate_id") != attempt.get("candidate_id")
                or predecessor.get("seed") != attempt.get("seed")
                or run_id == predecessor_id
            ):
                reasons.append("K1_COMPARISON_UNAUTHORIZED_RETRY")
        elif attempt.get("predecessor_run_id") is not None:
            reasons.append("K1_COMPARISON_UNAUTHORIZED_RETRY")
    if primary_pairs != required_pairs:
        reasons.append("K1_COMPARISON_CANDIDATE_SEED_BIJECTION_INVALID")
    if any(count != 1 for count in attempt_run_ids.values()):
        reasons.append("K1_COMPARISON_ATTEMPT_RUN_ID_DUPLICATE")
    successful_pairs = {
        (str(attempt.get("candidate_id")), attempt.get("seed"))
        for attempt in valid_attempts
        if attempt.get("outcome") == "SUCCESS"
    }
    if any(pair not in successful_pairs for pair in required_pairs):
        reasons.append("K1_COMPARISON_FAILED_ATTEMPT_SCORED")

    manifests = payload.get("verified_run_manifests")
    manifest_ids: Counter[str] = Counter()
    if not isinstance(manifests, (list, tuple)) or not manifests:
        reasons.append("K1_COMPARISON_RUN_MANIFESTS_INVALID")
    else:
        for manifest in manifests:
            if not verified_run_record(manifest, isolated_state):
                reasons.append("K1_COMPARISON_RUN_MANIFESTS_INVALID")
            if isinstance(manifest, Mapping):
                manifest_ids[str(manifest.get("run_id"))] += 1
    expected_ids = Counter({run_id: 1 for run_id in attempt_run_ids})
    if manifest_ids != expected_ids:
        reasons.append("K1_COMPARISON_RUN_MANIFEST_BIJECTION_INVALID")

    events = payload.get("access_events")
    prior_hash = str(isolated_state.get("trusted_access_genesis", ""))
    premature = 0
    final_batches = 0
    if not isinstance(events, (list, tuple)):
        reasons.append("K1_COMPARISON_ACCESS_LEDGER_INVALID")
        events = ()
    for expected_ordinal, event in enumerate(events, start=1):
        if not isinstance(event, Mapping):
            reasons.append("K1_COMPARISON_ACCESS_LEDGER_INVALID")
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
        if (
            event.get("ordinal") != expected_ordinal
            or event.get("prior_hash") != prior_hash
            or event.get("event_hash") != sha256_json(body)
        ):
            reasons.append("K1_COMPARISON_ACCESS_CHAIN_INVALID")
        if (
            event.get("run_id") != payload.get("run_id")
            or event.get("model_freeze_hash") != isolated_state.get("trusted_model_freeze_hash")
            or event.get("pretest_decision_hash")
            != isolated_state.get("trusted_pretest_decision_hash")
            or event.get("test_set_id") != isolated_state.get("trusted_test_set_id")
        ):
            reasons.append("K1_COMPARISON_ACCESS_EVENT_BINDING_INVALID")
        prior_hash = str(event.get("event_hash", ""))
        if event.get("kind") == "FINAL_TEST_BATCH":
            final_batches += 1
            if event.get("after_model_freeze") is not True:
                premature += 1
        else:
            premature += 1
    if premature:
        reasons.append("K1_COMPARISON_PREMATURE_TEST_ACCESS")
    if payload.get("model_frozen") is not True or final_batches != 1:
        reasons.append("K1_COMPARISON_FINAL_TEST_COUNT_INVALID")
    trusted_heads = isolated_state.get("trusted_access_heads", {})
    if not isinstance(trusted_heads, Mapping) or prior_hash != trusted_heads.get(
        payload.get("run_id")
    ):
        reasons.append("K1_COMPARISON_ACCESS_HEAD_NOT_TRUSTED")
    if payload.get("model_freeze_hash") != isolated_state.get("trusted_model_freeze_hash"):
        reasons.append("K1_COMPARISON_MODEL_FREEZE_BINDING_INVALID")
    if payload.get("pretest_decision_hash") != isolated_state.get("trusted_pretest_decision_hash"):
        reasons.append("K1_COMPARISON_PRETEST_DECISION_BINDING_INVALID")
    if payload.get("test_set_id") != isolated_state.get("trusted_test_set_id"):
        reasons.append("K1_COMPARISON_TEST_SET_BINDING_INVALID")
    if payload.get("test_set_id") in set(isolated_state.get("exposed_test_set_ids", ())):
        reasons.append("K1_COMPARISON_EXPOSED_TEST_SET_REJECTED")
    return (
        not reasons,
        tuple(sorted(set(reasons))),
        {
            "selected_candidate": winner,
            "premature_access_count": premature,
            "final_test_access_count": final_batches,
            "attempt_count": sum(attempt_run_ids.values()),
        },
    )


__all__ = ["evaluate_model_comparison"]
