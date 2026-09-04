#!/usr/bin/env python3
"""Check the bounded Competition RC1 decision, implementation and state as one view."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
K1 = "ARCH-K1-THIN-SKILL-DETERMINISTIC-EVIDENCE-KERNEL"
SKILL_VERSION = "0.2.0-competition-rc1"
DEFERRED = {
    "full sealed Stage 1",
    "Stage 2 model comparison",
    "full ablation",
    "external validity",
    "production fitness",
    "monetary cost",
}
OLD_HASHES = {
    "evals/prospective/phase-003f/minimum_competition_architecture_gate.json": (
        "cdb557751b79818208ff27734c1be97501e04fa9775c63d04ac97949664e17a5"
    ),
    "evals/results/phase-003f/architecture_decision.json": (
        "70cd886ad2efb226769bb15a26d041554f12d24c2bf3acc8c87b90f6527156a1"
    ),
    "evals/results/phase-003f/read_only_core_gate_audit.json": (
        "d3e19c1d1e5b95843e581f928eaa52d8b9516f88dfa3f13f0d96210c19e0c54d"
    ),
    "evals/results/phase-003f/competition_rc_acceptance_report.md": (
        "05bffc95fe8476911338098c0a9250eeb9ce6333e52d3620786b357be3c01b40"
    ),
}


def load_json(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def sha256(relative: str) -> str:
    digest = hashlib.sha256()
    with (ROOT / relative).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evaluate() -> dict[str, Any]:
    state = load_json("state/project_state.json")
    decision = load_json("evals/results/phase-003f-r1/architecture_decision.json")
    gate = load_json(
        "evals/results/phase-003f-r1/minimum_competition_architecture_gate_result.json"
    )
    e2e = load_json("evals/results/phase-003f-r1/end_to_end/result.json")
    negative = load_json("evals/results/phase-003f-r1/negative_tests/result.json")
    revision = load_json("evals/results/phase-003f-r1/formal_skill_integration/revision-003.json")
    skill = (ROOT / ".agents/skills/cumcm-modeling-evidence/SKILL.md").read_text(encoding="utf-8")
    plan = (ROOT / "plans/active/PLAN-0002D-R3-shadow-prototype-validation.md").read_text(
        encoding="utf-8"
    )
    workflow = (ROOT / "WORKFLOW.md").read_text(encoding="utf-8")
    checks: dict[str, bool] = {
        "old_artifacts_byte_identical": all(
            sha256(path) == expected for path, expected in OLD_HASHES.items()
        )
        and subprocess.run(
            [
                "git",
                "diff",
                "--quiet",
                "131823092a2e8c33c677419d45ed54b381a9948e",
                "--",
                "evals/results/phase-003f",
                "evals/prospective/phase-003f",
            ],
            cwd=ROOT,
            check=False,
        ).returncode
        == 0,
        "plan_marks_rc1_sprint": "COMPETITION_RC1_REPAIR_AND_INTEGRATION_SPRINT" in plan,
        "plan_defers_full_r3": "DEFERRED_NOT_PASSED" in plan,
        "workflow_routes_development_eval": (
            "FORMAL_SKILL_RC → DEVELOPMENT_EVAL → VALIDATION → HELD_OUT → COMPETITION_CANDIDATE"
            in workflow
        ),
        "state_phase": state.get("phase") == "PHASE-SKILL-INTEGRATION-003",
        "state_subphase": state.get("subphase") == "COMPETITION-RC1-REPAIR-AND-INTEGRATION",
        "state_technical_status": state.get("technical_adjudication_status")
        == "COMPETITION_SKILL_RC_READY",
        "state_skill_version": state.get("active_skill_version") == SKILL_VERSION,
        "state_capability": state.get("skill_capability_status") == "COMPETITION_RC",
        "state_architecture": state.get("selected_architecture") == K1,
        "state_base_unselected": state.get("base_selected") is False,
        "state_third_party_false": state.get("third_party_integrated") is False,
        "state_next_phase": state.get("next_phase_allowed") == "PHASE-SKILL-DEVELOPMENT-EVAL-004",
        "state_has_no_blockers": state.get("blockers") == [],
        "decision_id": decision.get("decision_id")
        == "DECISION-COMPETITION-RC1-ARCHITECTURE-003F-R1",
        "decision_architecture": decision.get("selected_architecture") == K1,
        "decision_scope": decision.get("accepted_scope") == "COMPETITION_RC_IMPLEMENTATION_ONLY",
        "gate_selected_k1": gate.get("selected_architecture") == K1,
        "gate_cases": gate.get("case_evaluations") == 234,
        "gate_k1_8_of_8": all(
            item.get("status") == "PASS"
            for item in gate.get("architecture_results", {}).get(K1, {}).get("gates", {}).values()
        )
        and len(gate.get("architecture_results", {}).get(K1, {}).get("gates", {})) == 8,
        "e2e_two_pass": e2e.get("passed") == 2 and e2e.get("failed") == 0,
        "e2e_result_hash_current": sha256("evals/results/phase-003f-r1/end_to_end/result.json")
        == "3beefd5190547246a361e6829a2236224927af8a9673cc0344ff62f78676fa99",
        "e2e_ready_states": all(
            item.get("final_state") == "READY_FOR_PAPER_HANDOFF"
            for item in e2e.get("case_evidence", [])
        )
        and len(e2e.get("case_evidence", [])) == 2,
        "e2e_raw_mutation_stale": all(
            load_json(f"evals/results/phase-003f-r1/end_to_end/{kind}.json")
            .get("post_ready_raw_mutation_probe", {})
            .get("status")
            == "STALE"
            for kind in ("prediction", "optimization")
        ),
        "negative_30_pass": negative.get("passed") == 30
        and negative.get("failed") == 0
        and negative.get("unhandled_exceptions") == 0
        and negative.get("sensitive_values_reported") == 0
        and sha256("evals/results/phase-003f-r1/negative_tests/result.json")
        == "5c46849aee853b1bb1d9af43f7ea22d827681852e6a2150da6ad4bd0cd2f5f60",
        "formal_revision_003": revision.get("revision_id")
        == "FORMAL-SKILL-COMPETITION-RC1-REVISION-003"
        and revision.get("repair_cycle", {}).get("cycle") == 3
        and revision.get("repair_cycle", {}).get("focused_test") == "104 passed"
        and revision.get("repair_cycle", {}).get("tree_hash")
        == "76dce0d6a63ab78bd38a21c27d40fba0b2d5242e3283ade8cdc0b7dfd809b8d8",
        "formal_skill_version": SKILL_VERSION in skill,
        "formal_skill_capability": "Capability: `COMPETITION_RC`" in skill,
        "formal_skill_count_one": len(list((ROOT / ".agents/skills").glob("*/SKILL.md"))) == 1,
        "workflow_count_14": len(
            list((ROOT / ".agents/skills/cumcm-modeling-evidence/workflows").glob("*.md"))
        )
        == 14,
        "role_count_4": len(
            list((ROOT / ".agents/skills/cumcm-modeling-evidence/agents").glob("*.md"))
        )
        == 4,
        "state_deferred_exact": set(state.get("competition_rc1", {}).get("deferred_validation", []))
        == DEFERRED,
        "state_full_r3_deferred": state.get("competition_rc1", {}).get("full_r3_status")
        == "DEFERRED_NOT_PASSED",
        "zero_api_training_comparison_third_party": (
            state.get("competition_rc1", {}).get("api_calls") == 0
            and state.get("competition_rc1", {}).get("model_training") is False
            and state.get("competition_rc1", {}).get("real_comparison_model_starts") == 0
            and state.get("competition_rc1", {}).get("third_party_executions") == 0
        ),
        "project_version_relationship": (
            (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "0.3.0-competition-rc1"
            and SKILL_VERSION in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        ),
    }
    audit = state.get("competition_rc1", {}).get("integration_audit", {})
    audit_path = audit.get("path")
    checks["integration_audit_pass"] = (
        audit.get("status") == "PASS"
        and isinstance(audit_path, str)
        and (ROOT / audit_path).is_file()
        and audit.get("sha256") == sha256(audit_path)
    )
    registry = yaml.safe_load((ROOT / "benchmarks/case_registry.yaml").read_text(encoding="utf-8"))
    checks["development_registry_no_preselected_case"] = registry.get("cases") == []
    failed = sorted(name for name, value in checks.items() if not value)
    return {
        "ok": not failed,
        "check_count": len(checks),
        "failed_checks": failed,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    result = evaluate()
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
