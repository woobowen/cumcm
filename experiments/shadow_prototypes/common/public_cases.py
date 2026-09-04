"""Public-only deterministic fixtures derived from the frozen public case classes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .interface import ShadowCaseInput, sha256_json

PUBLIC_CATALOG = Path("evals/prospective/phase-002d-r2/public_conformance/cases.json")
WORKFLOW_PUBLIC_STAGES = (
    "TASK_CREATED",
    "EXECUTION_STARTED",
    "COMMAND_COMPLETED",
    "ARTIFACT_PRODUCED",
    "AUTOMATIC_VALIDATION_PASSED",
    "AUTOMATIC_ADJUDICATION_ACCEPTED",
)
PUBLIC_DEPENDENCY_GRAPH = {"input": ["run"], "run": ["decision"]}
PUBLIC_CLAIM_RUN_BINDING = {
    "run_id": "run-public-1",
    "input_hash": "1" * 64,
    "code_commit": "2" * 40,
    "output_hash": "4" * 64,
    "lineage": ["table:public-result"],
}
PUBLIC_COMPARISON_POLICY = {
    "metric_direction": "MAXIMIZE",
    "tie_tolerance": 0.0,
    "ordered_tie_keys": ["candidate_id"],
}
PUBLIC_MODEL_FREEZE_HASH = "7" * 64
PUBLIC_PRETEST_DECISION_HASH = "8" * 64
PUBLIC_TEST_SET_ID = "sealed-public-placeholder-v1"


def _access_events(*, premature: bool, run_id: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    prior_hash = "0" * 64
    kinds = ["TEST_READ", "FINAL_TEST_BATCH"] if premature else ["FINAL_TEST_BATCH"]
    for ordinal, kind in enumerate(kinds, start=1):
        body = {
            "ordinal": ordinal,
            "kind": kind,
            "after_model_freeze": kind == "FINAL_TEST_BATCH",
            "prior_hash": prior_hash,
            "run_id": run_id,
            "model_freeze_hash": PUBLIC_MODEL_FREEZE_HASH,
            "pretest_decision_hash": PUBLIC_PRETEST_DECISION_HASH,
            "test_set_id": PUBLIC_TEST_SET_ID,
        }
        event = {**body, "event_hash": sha256_json(body)}
        events.append(event)
        prior_hash = event["event_hash"]
    return events


def _gate_record(component_id: str) -> dict[str, Any]:
    body = {
        "component_id": component_id,
        "decision_id": f"decision:{component_id}",
        "run_id": "run-public-1",
        "authority": "existing-native-component-ledger",
        "outcome": "PASS",
        "current": True,
        "audited": True,
    }
    return {**body, "artifact_hash": sha256_json(body)}


def _workflow_payload(case_class: str) -> dict[str, Any]:
    stages = list(WORKFLOW_PUBLIC_STAGES)
    if case_class == "missing evidence":
        stages.pop()
    return {
        "state_truth_path": "state/project_state.json",
        "requested_state": "AUTOMATIC_ADJUDICATION_ACCEPTED",
        "actor": "MAIN_AGENT_FORMAL_STATE_WRITER",
        "evidenced_stages": stages,
        "evidence_records": {
            stage: {
                "registered": True,
                "current": True,
                "authority": "existing-state-transition-ledger",
                "artifact_body": {"stage": stage, "run_id": "run-public-1"},
                "artifact_hash": sha256_json({"stage": stage, "run_id": "run-public-1"}),
                "audited": True,
            }
            for stage in stages
        },
        "dependency_graph": PUBLIC_DEPENDENCY_GRAPH,
        "dependency_graph_hash": sha256_json(PUBLIC_DEPENDENCY_GRAPH),
        "changed_nodes": ["input"] if case_class == "stale mutation" else [],
        "narrative_override": case_class == "gaming attempt",
        "team_challenge": {"supported": False},
        "upstream_gates": {
            component_id: _gate_record(component_id)
            for component_id in (
                "claim-evidence-support-gate",
                "leakage-safe-model-comparison-gate",
            )
        },
    }


def _claim_payload(case_class: str) -> dict[str, Any]:
    proposition = "Run run-public-1 produced the registered public result."
    evidence = []
    if case_class != "missing evidence":
        bounded_proposition = (
            "A different proposition." if case_class == "gaming attempt" else proposition
        )
        artifact_body = {
            "bounded_proposition": bounded_proposition,
            "scope": "PUBLIC_RESULT",
            "modality": "observed",
            "strength": "MODERATE",
            "evidence_type": "RUN",
            **PUBLIC_CLAIM_RUN_BINDING,
            "revision_id": "claim-evidence-revision-1",
            "prior_revision_hash": "0" * 64,
            "superseded": False,
        }
        locator = "runs/run-public-1/result.json"
        artifact_hash = sha256_json(artifact_body)
        evidence.append(
            {
                "evidence_id": "evidence-1",
                "locator": locator,
                "registered": True,
                "authority": "existing-native-run-ledger",
                "artifact_body": artifact_body,
                "artifact_hash": artifact_hash,
                "registry_hash": sha256_json({"locator": locator, "artifact_hash": artifact_hash}),
                "bounded_proposition": bounded_proposition,
                "scope": "PUBLIC_RESULT",
                "modality": "observed",
                "strength": "MODERATE",
                "evidence_type": "RUN",
                "contradicts": [],
                "current": case_class != "stale mutation",
                "run_id": "run-public-1",
                "input_hash": PUBLIC_CLAIM_RUN_BINDING["input_hash"],
                "code_commit": PUBLIC_CLAIM_RUN_BINDING["code_commit"],
                "output_hash": PUBLIC_CLAIM_RUN_BINDING["output_hash"],
                "lineage": PUBLIC_CLAIM_RUN_BINDING["lineage"],
                "revision_id": "claim-evidence-revision-1",
                "prior_revision_hash": "0" * 64,
                "superseded": False,
            }
        )
    return {
        "claim": {
            "claim_id": "claim-1",
            "claim_type": "COMPUTATIONAL_RESULT",
            "proposition": proposition,
            "scope": "PUBLIC_RESULT",
            "modality": "observed",
            "strength": "MODERATE",
            "run_id": "run-public-1",
            "input_hash": PUBLIC_CLAIM_RUN_BINDING["input_hash"],
            "code_commit": PUBLIC_CLAIM_RUN_BINDING["code_commit"],
            "output_hash": PUBLIC_CLAIM_RUN_BINDING["output_hash"],
            "lineage": PUBLIC_CLAIM_RUN_BINDING["lineage"],
        },
        "evidence": evidence,
        "narrative_override": case_class == "gaming attempt",
        "verified_run_manifest": {
            "run_id": "run-public-1",
            "decision_id": "manifest-decision:run-public-1",
            "authority": "existing-native-run-ledger",
            "status": "PASS",
            "current": True,
            "audited": True,
            "artifact_hash": sha256_json({"run_id": "run-public-1", "status": "PASS"}),
        },
    }


def _manifest_payload(case_class: str) -> dict[str, Any]:
    input_content = {"records": [1, 2, 3]}
    config_content = {"mode": "offline"}
    output_content = {"status": "ok"}
    manifest = {
        "run_id": "run-public-1",
        "revision_id": "run-public-1-manifest-v1",
        "prior_manifest_hash": "0" * 64,
        "current": True,
        "authority": "existing-native-run-ledger",
        "input_hash": sha256_json(input_content),
        "code_commit": "2" * 40,
        "config_hash": sha256_json(config_content),
        "seed": 1729,
        "command": ["python", "runner.py", "--offline"],
        "cwd": ".",
        "environment_hash": sha256_json({"python": "3.11"}),
        "dependency_hash": sha256_json({"project": "cumcm-skill-lab"}),
        "output_hash": sha256_json(output_content),
        "outcome": "SUCCESS",
    }
    if case_class == "missing evidence":
        manifest.pop("output_hash")
    payload = {
        "manifest": manifest,
        "trusted_capture": {
            "run_id": "run-public-1",
            "revision_id": "run-public-1-manifest-v1",
            "prior_manifest_hash": "0" * 64,
            "current": True,
            "authority": "existing-native-run-ledger",
            "input_content": (
                {"records": [9]} if case_class == "stale mutation" else input_content
            ),
            "code_commit": "2" * 40,
            "config_content": config_content,
            "seed": 1729,
            "command": ["python", "runner.py", "--offline"],
            "cwd": ".",
            "environment": {"python": "3.11"},
            "dependencies": {"project": "cumcm-skill-lab"},
            "output_content": output_content,
            "outcome": "SUCCESS",
        },
    }
    if case_class == "gaming attempt":
        payload["private_path"] = "/" + "private" + "/credential.txt"
    return payload


def _comparison_payload(case_class: str) -> dict[str, Any]:
    comparison_run_id = f"comparison-{case_class.replace(' ', '-')}"
    attempts = [
        {
            "run_id": f"{candidate}-{seed}",
            "candidate_id": candidate,
            "seed": seed,
            "terminal": True,
            "outcome": "SUCCESS",
            "retry": False,
            "infrastructure_failure": False,
            "predecessor_run_id": None,
            "failure_class": "NONE",
        }
        for candidate in ("a", "b")
        for seed in (1729, 2718)
    ]
    return {
        "run_id": comparison_run_id,
        "splits": {"train": ["t1", "t2"], "validation": ["v1"], "test": ["h1"]},
        "group_overlap": False,
        "time_order_valid": True,
        "future_feature": False,
        "target_feature": False,
        "transform_fit_scope": "train",
        "baselines": ["naive"] if case_class == "missing evidence" else ["naive", "domain"],
        "candidate_freeze_hash": "5" * 64,
        "metric_freeze_hash": "6" * 64,
        **PUBLIC_COMPARISON_POLICY,
        "freeze_order": ["split", "candidates", "metric", "attempts", "model", "test"],
        "frozen_seeds": [1729, 2718],
        "attempts": attempts,
        "validation_scores": {"a": 0.8, "b": 0.7},
        "selected_candidate_id": "a",
        "model_frozen": True,
        "model_freeze_hash": PUBLIC_MODEL_FREEZE_HASH,
        "pretest_decision_hash": PUBLIC_PRETEST_DECISION_HASH,
        "test_set_id": PUBLIC_TEST_SET_ID,
        "selected_candidate_matches_validation": True,
        "failures_retained": True,
        "access_events": _access_events(
            premature=case_class == "gaming attempt", run_id=comparison_run_id
        ),
        "dependency_current": case_class != "stale mutation",
        "verified_run_manifests": [
            {
                "run_id": f"{candidate}-{seed}",
                "decision_id": f"manifest-decision:{candidate}-{seed}",
                "authority": "existing-native-run-ledger",
                "status": "PASS",
                "current": True,
                "audited": True,
                "artifact_hash": sha256_json({"run_id": f"{candidate}-{seed}", "status": "PASS"}),
            }
            for candidate in ("a", "b")
            for seed in (1729, 2718)
        ],
    }


def _payload(component_id: str, case_class: str) -> dict[str, Any]:
    builders = {
        "accepted-versus-done-workflow-state": _workflow_payload,
        "claim-evidence-support-gate": _claim_payload,
        "hash-bound-reproducibility-manifest": _manifest_payload,
        "leakage-safe-model-comparison-gate": _comparison_payload,
    }
    try:
        return builders[component_id](case_class)
    except KeyError as exc:
        raise ValueError(f"UNKNOWN_COMPONENT:{component_id}") from exc


def _build_case(item: dict[str, Any]) -> ShadowCaseInput:
    payload = _payload(item["component_id"], item["synthetic_input_class"])
    return ShadowCaseInput(
        case_id=item["case_id"],
        component_id=item["component_id"],
        payload=payload,
        input_hash=sha256_json(payload),
        case_class=item["synthetic_input_class"],
        source_commitment_hash=item["case_hash"],
    )


def public_isolated_state() -> dict[str, Any]:
    gates = {
        component_id: _gate_record(component_id)
        for component_id in (
            "claim-evidence-support-gate",
            "leakage-safe-model-comparison-gate",
        )
    }
    claim_payload = _claim_payload("valid control")
    repro_payload = _manifest_payload("valid control")
    comparison_payloads = {
        case_class: _comparison_payload(case_class)
        for case_class in ("valid control", "missing evidence", "stale mutation", "gaming attempt")
    }
    comparison_payload = comparison_payloads["valid control"]
    trusted_run_ids = [
        "run-public-1",
        *(f"{candidate}-{seed}" for candidate in ("a", "b") for seed in (1729, 2718)),
    ]
    return {
        "truth_source": "state/project_state.json",
        "formal_state_writes_allowed": False,
        "trusted_run_ids": [
            *trusted_run_ids,
            *(payload["run_id"] for payload in comparison_payloads.values()),
        ],
        "trusted_stage_hashes": {
            stage: sha256_json({"stage": stage, "run_id": "run-public-1"})
            for stage in WORKFLOW_PUBLIC_STAGES
        },
        "trusted_gate_hashes": {
            component_id: record["artifact_hash"] for component_id, record in gates.items()
        },
        "trusted_artifact_hashes": {
            item["locator"]: item["artifact_hash"] for item in claim_payload["evidence"]
        },
        "trusted_run_bindings": {
            "run-public-1": PUBLIC_CLAIM_RUN_BINDING,
        },
        "trusted_manifest_hashes": {
            run_id: sha256_json({"run_id": run_id, "status": "PASS"}) for run_id in trusted_run_ids
        },
        "trusted_dependency_graph": PUBLIC_DEPENDENCY_GRAPH,
        "trusted_dependency_graph_hash": sha256_json(PUBLIC_DEPENDENCY_GRAPH),
        "trusted_repro_manifest_hashes": {"run-public-1": sha256_json(repro_payload["manifest"])},
        "trusted_capture_hashes": {"run-public-1": sha256_json(repro_payload["trusted_capture"])},
        "comparison_policy": PUBLIC_COMPARISON_POLICY,
        "trusted_candidates": ["a", "b"],
        "trusted_seeds": [1729, 2718],
        "trusted_candidate_freeze_hash": "5" * 64,
        "trusted_metric_freeze_hash": "6" * 64,
        "trusted_comparison_design_hash": sha256_json(
            {
                "splits": comparison_payload["splits"],
                "group_overlap": comparison_payload["group_overlap"],
                "time_order_valid": comparison_payload["time_order_valid"],
                "future_feature": comparison_payload["future_feature"],
                "target_feature": comparison_payload["target_feature"],
                "transform_fit_scope": comparison_payload["transform_fit_scope"],
                "baselines": comparison_payload["baselines"],
                "policy": PUBLIC_COMPARISON_POLICY,
            }
        ),
        "trusted_access_genesis": "0" * 64,
        "trusted_access_heads": {
            payload["run_id"]: payload["access_events"][-1]["event_hash"]
            for payload in comparison_payloads.values()
        },
        "trusted_model_freeze_hash": PUBLIC_MODEL_FREEZE_HASH,
        "trusted_pretest_decision_hash": PUBLIC_PRETEST_DECISION_HASH,
        "trusted_test_set_id": PUBLIC_TEST_SET_ID,
        "exposed_test_set_ids": [],
    }


def load_public_cases(root: Path) -> list[ShadowCaseInput]:
    catalog = json.loads((root / PUBLIC_CATALOG).read_text(encoding="utf-8"))
    return [_build_case(item) for item in catalog["cases"]]


__all__ = ["PUBLIC_CATALOG", "load_public_cases", "public_isolated_state"]
