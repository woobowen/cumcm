"""Public-only deterministic fixtures derived from the frozen public case classes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .interface import ShadowCaseInput

PUBLIC_CATALOG = Path("evals/prospective/phase-002d-r2/public_conformance/cases.json")


def _payload(component_id: str, case_class: str) -> dict[str, Any]:
    valid = case_class == "valid control"
    if component_id == "accepted-versus-done-workflow-state":
        return {
            "requested_state": "AUTOMATIC_ADJUDICATION_ACCEPTED",
            "actor": "MAIN_AGENT_FORMAL_STATE_WRITER" if valid else "REVIEWER",
            "evidenced_stages": [
                "TASK_CREATED",
                "EXECUTION_STARTED",
                "COMMAND_COMPLETED",
                "ARTIFACT_PRODUCED",
                "AUTOMATIC_VALIDATION_PASSED",
                *(["AUTOMATIC_ADJUDICATION_ACCEPTED"] if valid else []),
            ],
            "dependency_graph": {"input": ["run"], "run": ["decision"]},
            "changed_nodes": ["input"] if case_class == "stale mutation" else [],
            "narrative_override": case_class == "gaming attempt",
        }
    if component_id == "claim-evidence-support-gate":
        return {
            "claim_id": "claim-1",
            "claim_type": "RESULT" if valid else "FINAL",
            "run_id": "run-public-1",
            "evidence": (
                [
                    {
                        "evidence_id": "evidence-1",
                        "exists": True,
                        "supports": ["claim-1"],
                        "contradicts": [],
                        "current": case_class != "stale mutation",
                        "run_id": "run-public-1",
                    }
                ]
                if case_class != "missing evidence"
                else []
            ),
            "narrative_override": case_class == "gaming attempt",
        }
    if component_id == "hash-bound-reproducibility-manifest":
        bindings = {
            "run_id": "run-public-1",
            "input_hash": "1" * 64,
            "code_commit": "2" * 40,
            "config_hash": "3" * 64,
            "seed": 1729,
            "command": ["python", "runner.py", "--offline"],
            "output_hash": "4" * 64,
            "outcome": "SUCCESS",
        }
        if case_class == "missing evidence":
            bindings.pop("output_hash")
        return {
            "manifest": bindings,
            "observed": {
                **bindings,
                **({"input_hash": "9" * 64} if case_class == "stale mutation" else {}),
            },
            "contains_private_field": case_class == "gaming attempt",
        }
    if component_id == "leakage-safe-model-comparison-gate":
        return {
            "run_id": "run-public-1",
            "splits": {
                "train": ["t1", "t2"],
                "validation": ["v1"],
                "test": ["h1"],
            },
            "group_overlap": False,
            "future_feature": False,
            "target_feature": False,
            "baselines": ["naive", "domain"] if valid else ["naive"],
            "candidate_freeze_hash": "5" * 64,
            "metric_freeze_hash": "6" * 64,
            "model_frozen": True,
            "selected_candidate_matches_validation": True,
            "failures_retained": True,
            "access_events": (
                [{"kind": "FINAL_TEST_BATCH", "after_model_freeze": True}]
                if valid
                else (
                    [{"kind": "TEST_READ", "after_model_freeze": False}]
                    if case_class == "gaming attempt"
                    else []
                )
            ),
            "dependency_current": case_class != "stale mutation",
        }
    raise ValueError(f"UNKNOWN_COMPONENT:{component_id}")


def load_public_cases(root: Path) -> list[ShadowCaseInput]:
    catalog = json.loads((root / PUBLIC_CATALOG).read_text(encoding="utf-8"))
    return [
        ShadowCaseInput(
            case_id=item["case_id"],
            component_id=item["component_id"],
            payload=_payload(item["component_id"], item["synthetic_input_class"]),
            input_hash=item["case_hash"],
            case_class=item["synthetic_input_class"],
        )
        for item in catalog["cases"]
    ]


__all__ = ["PUBLIC_CATALOG", "load_public_cases"]
