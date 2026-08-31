# ruff: noqa: E501
"""Rebuild Phase 002 score summaries and human-gated proposals offline."""

from __future__ import annotations

import csv
import io
import json
from collections import defaultdict
from pathlib import Path
from statistics import median

import yaml

from .models import file_sha256, load_json, validate_json

ARM_ORDER = ("ARM-A", "ARM-B", "ARM-C")
OUTPUT_PATHS = (
    "research/upstream_candidates/dynamic_evaluation.csv",
    "research/upstream_candidates/dynamic_reviews/base_selection_proposal.json",
    "research/upstream_candidates/dynamic_reviews/component_selection_proposal.json",
    "reports/upstream_dynamic_eval.md",
    "reports/base_selection_proposal.md",
    "reports/component_portfolio_proposal.md",
    "reports/human_gate_base_selection.md",
)


def _text(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _load_cards(root: Path) -> list[dict]:
    return [
        yaml.safe_load(path.read_text(encoding="utf-8"))
        for path in sorted((root / "research/upstream_candidates/component_cards").glob("*.yaml"))
    ]


def _load_evidence(root: Path) -> dict:
    reveal = load_json(root / "evals/results/phase-002/reveal_record.json")
    scores = [
        load_json(path)
        for path in sorted((root / "evals/results/phase-002/scores").rglob("*.json"))
    ]
    runs = [
        load_json(path) for path in sorted((root / "evals/results/phase-002/runs").rglob("*.json"))
    ]
    current_runs = {
        (item["anonymous_arm_id"], item["case_id"], item["run_index"]): item for item in runs
    }
    cases = [
        load_json(path) for path in sorted((root / "evals/cases/phase-002").glob("CASE-*.json"))
    ]
    packages = load_json(
        root / "research/upstream_candidates/dynamic_reviews/package_safety_review.json"
    )
    return {
        "reveal": reveal,
        "scores": scores,
        "runs": runs,
        "current_runs": current_runs,
        "cases": cases,
        "fixture_manifest": load_json(root / "evals/fixtures/phase-002/manifest.json"),
        "packages": packages,
        "cards": _load_cards(root),
    }


def _aggregate(evidence: dict) -> dict[str, dict]:
    scores_by_arm: dict[str, list[dict]] = defaultdict(list)
    runs_by_arm: dict[str, list[dict]] = defaultdict(list)
    for item in evidence["scores"]:
        scores_by_arm[item["anonymous_arm_id"]].append(item)
    for item in evidence["runs"]:
        runs_by_arm[item["anonymous_arm_id"]].append(item)
    packages_by_actual = {item["arm_id"]: item for item in evidence["packages"]["arms"]}
    output: dict[str, dict] = {}
    for arm in ARM_ORDER:
        actual = evidence["reveal"]["anonymous_to_actual"][arm]
        scores = scores_by_arm[arm]
        runs = runs_by_arm[arm]
        output[arm] = {
            "actual": actual,
            "scores": scores,
            "runs": runs,
            "deterministic_median": median(item["deterministic_score"] for item in scores),
            "reviewer_median": median(item["reviewer_score"] for item in scores),
            "total_median": median(item["total_score"] for item in scores),
            "total_min": min(item["total_score"] for item in scores),
            "total_max": max(item["total_score"] for item in scores),
            "hard_failures": sum(len(item["hard_failures"]) for item in scores),
            "low_confidence": sum(item["confidence"] == "LOW" for item in scores),
            "completed": sum(item["completion_status"] == "COMPLETED" for item in runs),
            "failed": sum(item["completion_status"] == "FAILED" for item in runs),
            "duration": sum(item["duration_seconds"] for item in runs),
            "input_tokens": sum(
                (item.get("token_usage") or {}).get("input_tokens", 0) for item in runs
            ),
            "output_tokens": sum(
                (item.get("token_usage") or {}).get("output_tokens", 0) for item in runs
            ),
            "package": packages_by_actual[actual],
        }
    return output


def _base_proposal(aggregate: dict[str, dict]) -> dict:
    return {
        "schema_version": "1.0.0",
        "proposal_id": "BASE-PROP-PHASE-002",
        "status": "PROPOSAL_ONLY",
        "recommendation": "RECOMMEND_CLEAN_ROOM_ARCHITECTURE",
        "fallback": (
            "Retain NO_PROJECT_MODELING_SKILL as the neutral starting point and keep the single "
            "formal Skill SCAFFOLD_ONLY until human-approved clean-room mechanisms pass fresh tests."
        ),
        "evidence": [
            "Frozen median totals: native baseline 62.5, HANDSOMEZR 60.5, YUSHUI 60.0.",
            "All 18 arm/case cells are scored and no hard failure was detected.",
            "All three arms exposed shared measurable gaps in model selection, freshness, reproducibility artifacts, and claim support.",
            "Four clean-room mechanism cards bind those gaps to observable next-phase tests.",
        ],
        "counter_evidence": [
            "Only six project-authored synthetic cases and one current observation per arm/case were used.",
            "Five current cells were recovered from retained harness false-positive failures and have LOW confidence.",
            "Sanitized instruction-only packages do not establish full upstream repository behavior.",
            "The median spread is only 2.5 points and neither candidate shows a consistent advantage over the native baseline.",
        ],
        "dynamic_quality": (
            "The neutral baseline has the highest median total, but all arms show complementary strengths and material shared failures; comparative confidence is insufficient for winner-takes-all adoption."
        ),
        "legal_reusability": (
            "YUSHUI is UNKNOWN_NO_LICENSE; HANDSOMEZR has external/corpus exclusions; selected component sources have root or subresource gaps. Direct copy or fork is not proposed."
        ),
        "technical_integrability": (
            "Whole-package adoption would conflict with the single-Skill, single-state, Source/Claim/Run, and human-gate architecture. Native clean-room contracts can avoid those conflicts."
        ),
        "security_acceptability": (
            "Evaluation packages were text-only and isolated, but upstream repositories contain network, installer, MCP, subprocess, Git, or broad-tool surfaces. Those surfaces remain excluded."
        ),
        "maintenance_feasibility": (
            "Four bounded native mechanisms are maintainable only with deterministic Schemas and negative tests; a wholesale upstream fork or large Skill pool is not maintainable in current scope."
        ),
        "unresolved_questions": [
            "Which, if any, clean-room mechanisms may enter a Phase 003 design?",
            "What project license will govern future integration?",
            "What per-resource license evidence is required before any non-clean-room reuse?",
            "What frozen validation set and success thresholds will test Phase 003 without answer exposure?",
            "How should recovery-affected evidence be weighted in the human decision?",
        ],
        "human_gate": "GATE_BASE_SELECTION_PENDING",
        "base_selected": False,
    }


def _component_proposal(cards: list[dict]) -> dict:
    return {
        "schema_version": "1.0.0",
        "proposal_id": "COMP-PROP-PHASE-002",
        "status": "PROPOSAL_ONLY",
        "components": [
            {
                "mechanism_id": card["mechanism_id"],
                "actual_gap": card["actual_gap_addressed"],
                "benefit": card["measured_or_expected_benefit"],
                "reuse_mode": card["reuse_mode"],
                "license_status": card["license_status"],
                "contamination_status": card["contamination_risk"],
                "clean_room_work": " ".join(card["clean_room_requirements"]),
                "required_tests": card["required_tests"],
            }
            for card in cards
        ],
        "rejected_components": [
            "Whole upstream base or Skill-pool adoption: scope, state, security, license, and contamination conflicts.",
            "Network OCR/search, MCPs, installers, updaters, remote queues, or Git automation: outside the offline evaluation and safety boundary.",
            "Paper-writing and document-lint workflow: outside modeling scope and not tied to a measured Phase 002 gap.",
            "Subjective judge panels or agent votes: cannot constitute mathematical or experimental evidence.",
            "A second total controller, state tree, or evidence ledger: violates the single source-of-truth architecture.",
        ],
        "human_gate": "GATE_BASE_SELECTION_PENDING",
        "third_party_integrated": False,
    }


def _dynamic_csv(evidence: dict, aggregate: dict[str, dict]) -> str:
    fields = [
        "evaluation_id",
        "anonymous_arm",
        "revealed_candidate",
        "evaluation_mode",
        "case_id",
        "run_index",
        "run_status",
        "recovery_affected",
        "deterministic_score",
        "reviewer_score",
        "total_score",
        "hard_failures",
        "confidence",
        "duration_seconds",
        "input_tokens",
        "output_tokens",
        "direct_adoption_eligible",
        "run_hash",
        "score_hash",
    ]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    freeze = load_json(Path(evidence["root"]) / "evals/results/phase-002/score_freeze.json")
    for score in sorted(
        evidence["scores"], key=lambda item: (item["anonymous_arm_id"], item["case_id"])
    ):
        key = (score["anonymous_arm_id"], score["case_id"], score["run_index"])
        run = evidence["current_runs"][key]
        arm = aggregate[score["anonymous_arm_id"]]
        package = arm["package"]
        if package["arm_id"] == "NO_PROJECT_MODELING_SKILL":
            adoption_eligibility = "NOT_APPLICABLE_NATIVE"
        elif package.get("direct_adoption_eligible", False):
            adoption_eligibility = "ELIGIBLE"
        else:
            adoption_eligibility = "INELIGIBLE"
        stem = f"run-{score['run_index']:03d}.json"
        run_relative = (
            f"evals/results/phase-002/runs/{score['anonymous_arm_id']}/{score['case_id']}/{stem}"
        )
        score_relative = (
            f"evals/results/phase-002/scores/{score['anonymous_arm_id']}/{score['case_id']}/{stem}"
        )
        writer.writerow(
            {
                "evaluation_id": score["evaluation_id"],
                "anonymous_arm": score["anonymous_arm_id"],
                "revealed_candidate": arm["actual"],
                "evaluation_mode": package["mode"],
                "case_id": score["case_id"],
                "run_index": score["run_index"],
                "run_status": run["completion_status"],
                "recovery_affected": str(score["affected_by_run_failure"]).lower(),
                "deterministic_score": score["deterministic_score"],
                "reviewer_score": score["reviewer_score"],
                "total_score": score["total_score"],
                "hard_failures": ";".join(score["hard_failures"]),
                "confidence": score["confidence"],
                "duration_seconds": run["duration_seconds"],
                "input_tokens": (run.get("token_usage") or {}).get("input_tokens", 0),
                "output_tokens": (run.get("token_usage") or {}).get("output_tokens", 0),
                "direct_adoption_eligible": adoption_eligibility,
                "run_hash": freeze["run_hashes"][run_relative],
                "score_hash": freeze["score_hashes"][score_relative],
            }
        )
    return stream.getvalue()


def _dynamic_report(evidence: dict, aggregate: dict[str, dict]) -> str:
    manifest = evidence["fixture_manifest"]
    case_rows = []
    for case in evidence["cases"]:
        case_path = f"evals/cases/phase-002/{case['case_id']}.json"
        case_rows.append(
            "| {case_id} | {purpose} | {risks} | `{oracle}` | `FROZEN` | `{fixture_hash}` |".format(
                case_id=case["case_id"],
                purpose=_text(case["purpose"]),
                risks=_text(", ".join(case["risk_tags"])),
                oracle=case["oracle_path"],
                fixture_hash=manifest["files"][case_path],
            )
        )
    arm_rows = []
    for arm in ARM_ORDER:
        item = aggregate[arm]
        arm_rows.append(
            f"| {arm} | {item['actual']} | {item['package']['mode']} | 6 | "
            f"{item['completed']} | {item['failed']} | 0 | {item['hard_failures']} | "
            f"{item['deterministic_median']:.1f} | {item['reviewer_median']:.1f} | "
            f"{item['total_median']:.1f} | {item['total_min']:.1f}–{item['total_max']:.1f} | "
            f"{item['low_confidence']}/6 LOW |"
        )
    total_runs = sum(len(item["runs"]) for item in aggregate.values())
    total_completed = sum(item["completed"] for item in aggregate.values())
    total_failed = sum(item["failed"] for item in aggregate.values())
    total_duration = sum(item["duration"] for item in aggregate.values())
    total_input = sum(item["input_tokens"] for item in aggregate.values())
    total_output = sum(item["output_tokens"] for item in aggregate.values())
    return "\n".join(
        [
            "# Upstream Dynamic Evaluation",
            "",
            "Status: `PROPOSAL_ONLY`; `GATE_BASE_SELECTION_PENDING` is open.",
            "",
            "## Method and integrity",
            "",
            "Six deterministic synthetic cases compared one neutral no-project-Skill baseline with two",
            "sanitized instruction-only candidate packages using `gpt-5.4`, `medium`, and",
            "`workspace-write`. All 18 initial 70/30 scores were frozen before identity reveal. No",
            "third-party code or dependency was executed or installed, no MCP or remote was configured,",
            "and no historical answer material was used.",
            "",
            "## Cases",
            "",
            "| Case | Purpose | Injected risks | Deterministic oracle | Status | Case fixture hash |",
            "|---|---|---|---|---|---|",
            *case_rows,
            "",
            "## Revealed arms and frozen scores",
            "",
            "Medians are across six cases. Completed/failed count all retained real attempts; two failed",
            "CASE-001 attempts were followed by the only two allowed calibration runs.",
            "",
            "| Arm | Revealed candidate | Mode | Planned cells | Completed runs | Failed runs | Not-run | Hard failures | Deterministic median /70 | Reviewer median /30 | Total median /100 | Total range | Confidence |",
            "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
            *arm_rows,
            "",
            "## Runtime inventory",
            "",
            f"- Retained real runs: {total_runs}/20 budget ({total_completed} completed, {total_failed} failed, 0 not-run).",
            "- Calibration: 2/2 used; no further real run is permitted.",
            f"- Total retained duration: {total_duration:.6f} seconds.",
            f"- Observable token usage: {total_input} input and {total_output} output tokens.",
            "- Current score cells: 18/18; five are recovery-affected and forced to LOW confidence.",
            "- Process outcomes: every retained process exited 0 and every workspace reported no remote.",
            "",
            "## Result interpretation",
            "",
            "The native baseline has the highest median total (62.5), followed by HANDSOMEZR (60.5)",
            "and YUSHUI (60.0). The small spread, single current observation per cell, and uneven",
            "recovery effects do not justify automatic selection. CASE-004 and CASE-005 expose shared",
            "critical gaps, so the proposal is a native clean-room architecture with the neutral baseline",
            "as fallback—not adoption of a score winner.",
            "",
            "## Limitations",
            "",
            "- Synthetic cases do not establish real CUMCM performance.",
            "- Sanitized text packages do not establish full upstream runtime behavior.",
            "- YUSHUI remains `UNKNOWN_NO_LICENSE` and contaminated source material was excluded.",
            "- HANDSOMEZR has external/corpus exclusions and its full repository was not executed.",
            "- Five score cells depend on append-only parser recovery while original FAILED manifests remain.",
            "- Dynamic quality, legal reusability, technical integrability, security, and maintenance are separate decisions.",
            "",
        ]
    )


def _base_report(proposal: dict) -> str:
    evidence = "\n".join(f"- {item}" for item in proposal["evidence"])
    counter = "\n".join(f"- {item}" for item in proposal["counter_evidence"])
    unresolved = "\n".join(f"- {item}" for item in proposal["unresolved_questions"])
    return f"""# Base Selection Proposal

`PROPOSAL_ONLY — HUMAN GATE REQUIRED`

## Recommended option

`{proposal["recommendation"]}`: preserve the native single-Skill and single-state architecture and,
only after approval, clean-room reimplement the bounded mechanisms in the component portfolio.

## Fallback option

{proposal["fallback"]}

## Supporting evidence

{evidence}

## Counter-evidence

{counter}

## Separate rulings

- Dynamic quality: {proposal["dynamic_quality"]}
- Legal reusability: {proposal["legal_reusability"]}
- Technical integrability: {proposal["technical_integrability"]}
- Security acceptability: {proposal["security_acceptability"]}
- Maintenance feasibility: {proposal["maintenance_feasibility"]}
- Integration cost: high for whole candidates; medium-to-high for four native clean-room contracts and negative-test suites.
- Competition-time burden: must be measured; fail-closed gates need concise paths and cannot become unconditional token-heavy ceremony.

## Eighteen-factor assessment

| Factor | Evidence-based assessment |
|---|---|
| 1. Hard failures | Zero across 18 frozen scores; this does not cancel five retained/recovered harness failures. |
| 2. Relative baseline gain | Candidate median totals are 2.0 and 2.5 points below the native baseline; no positive aggregate gain is established. |
| 3. Problem interpretation | CASE-001 scores are moderate and all arms leave operational assumptions or validation incomplete. |
| 4. Data audit | CASE-002 is comparatively strong, but every arm lacks downstream empirical confirmation and some edge diagnostics. |
| 5. Actual run evidence | 20 real attempts are retained; 13 completed and seven failed, with 18 scoreable current cells after bounded recovery. |
| 6. Validation and robustness | CASE-004 exposes test leakage or selection inconsistency in every arm and missing robustness evidence. |
| 7. State recovery | CASE-005 deterministic scores are 7/7/0; no arm persists exact freshness closure or restart state. |
| 8. Evidence chain | CASE-006 and cross-case Reviewer findings show missing hash-bound claim/result artifacts. |
| 9. Runtime variation | Per-run duration and token use vary widely; one current observation per cell cannot estimate stable variance. |
| 10. Token and time | Retained runs are expensive; any new gate must show measurable benefit and bounded contest-time overhead. |
| 11. Scope fit | Whole candidate workflows include paper, service, or orchestration scope outside the modeling Skill. |
| 12. License | YUSHUI has no detected license; other candidates/components have external, corpus, or subresource gaps. |
| 13. Security | Text-only evaluation was safe, but whole upstreams include prohibited network, MCP, installer, subprocess, Git, or broad-tool behavior. |
| 14. Answer contamination | Historical/demo/corpus content was excluded and remains a blocker to copying or benchmark exposure. |
| 15. Integration conflict | Whole candidates would compete with the one-Skill, one-state, Source/Claim/Run architecture. |
| 16. Adaptation cost | Four clean-room native mechanisms require medium-to-high design, Schema, migration, and negative-test work. |
| 17. Long-term maintenance | A bounded native portfolio is feasible; forks or large Skill pools are not supported by current evidence. |
| 18. Competition-time burden | Not yet measured; human approval must require latency/token budgets and a fail-fast path. |

## Unresolved questions

{unresolved}

No base is selected, no third-party content is integrated, and the next phase remains prohibited
until `GATE_BASE_SELECTION_PENDING` is explicitly decided by a human.
"""


def _component_report(cards: list[dict], proposal: dict) -> str:
    rows = []
    for card in cards:
        rows.append(
            f"| `{card['mechanism_id']}` | {card['source_candidate']} | `{card['source_commit']}` | "
            f"{_text(card['actual_gap_addressed'])} | {_text(card['measured_or_expected_benefit'])} | "
            f"`{card['reuse_mode']}` | {_text(card['license_status'])} | {_text(card['contamination_risk'])} |"
        )
    rejected = "\n".join(f"- {item}" for item in proposal["rejected_components"])
    detail_sections = []
    for card in cards:
        work = "\n".join(f"- {item}" for item in card["clean_room_requirements"])
        tests = "\n".join(f"- {item}" for item in card["required_tests"])
        detail_sections.extend(
            [
                f"## `{card['mechanism_id']}`",
                "",
                f"- Source files: {', '.join(f'`{item}`' for item in card['source_files'])}",
                f"- Security risk: {card['security_risk']}",
                f"- Integration conflict: {card['integration_conflict']}",
                f"- Maintenance cost: `{card['maintenance_cost']}`; confidence: `{card['confidence']}`.",
                "- Clean-room work:",
                work,
                "- Required tests:",
                tests,
                "",
            ]
        )
    return "\n".join(
        [
            "# Component Portfolio Proposal",
            "",
            "Status: `PROPOSAL_ONLY — HUMAN GATE REQUIRED`. No component is integrated.",
            "",
            "| Mechanism | Source | Commit | Actual observed gap | Measured or expected benefit | Reuse mode | License | Contamination |",
            "|---|---|---|---|---|---|---|---|",
            *rows,
            "",
            "Every card requires a project-native clean-room specification, new implementation,",
            "Schema-bound state/evidence integration, and the negative tests listed in the card. No source",
            "file, prose, dependency, tool declaration, template, example, or asset is approved for copy.",
            "",
            *detail_sections,
            "## Rejected or deferred",
            "",
            rejected,
            "",
        ]
    )


def _gate_report(proposal: dict, cards: list[dict]) -> str:
    mechanisms = ", ".join(f"`{card['mechanism_id']}`" for card in cards)
    return f"""# Human Gate — Base Selection

Gate: `GATE_BASE_SELECTION_PENDING`

## Recommended方案

`RECOMMEND_CLEAN_ROOM_ARCHITECTURE`: keep the native architecture and consider only these four
clean-room mechanisms: {mechanisms}.

## 备选方案

{proposal["fallback"]}

## 支持与反对证据

支持：18/18 cells have frozen scores; no hard failure occurred; four repeated gaps have observable
tests. 反对：only six synthetic cases were used, five cells are recovery-affected, score medians
differ by at most 2.5 points, and sanitized packages cannot prove full repository behavior.

## 许可证、污染、安全和运行限制

- YUSHUI is `UNKNOWN_NO_LICENSE`; no direct copy or fork is legal-evidence-supported.
- HANDSOMEZR and every selected component source have external, corpus, per-Skill, or subresource gaps.
- Historical/demo/corpus content remains excluded; no candidate example may enter future validation.
- Network, MCP, installers, updaters, subprocess queues, broad tool declarations, and Git automation remain excluded.
- Real-run budget is exhausted at 20/20; Phase 002 evidence cannot be improved by another retry.
- Clean-room gates may not reduce current fail-closed security, evidence, state, or human-approval rules.

## Human must answer exactly

1. Approve or reject `RECOMMEND_CLEAN_ROOM_ARCHITECTURE` as the Phase 003 design direction; this is not approval of any upstream base.
2. Approve or reject retaining `NO_PROJECT_MODELING_SKILL` as the neutral fallback while the formal Skill remains `SCAFFOLD_ONLY`.
3. For each of the four cards, approve, reject, or defer clean-room specification work; no direct reuse option is offered.
4. Decide the project license and the minimum per-resource license evidence required before any future port/direct reuse.
5. Approve or reject the proposed frozen Phase 003 validation design and success thresholds before any implementation sees validation answers.
6. Decide whether recovery-affected cells may inform qualitative gap discovery but not comparative rank.
7. Confirm that Phase 003 must preserve one formal Skill, one authoritative state, no benchmark-answer access, and human approval for high-risk gates.

Until all required approvals are recorded, `base_selected=false`, `third_party_integrated=false`, and
`PHASE-SKILL-INTEGRATION-003` must not start.
"""


def build_outputs(root: Path) -> tuple[dict[str, str], list[str]]:
    evidence = _load_evidence(root)
    evidence["root"] = root.as_posix()
    aggregate = _aggregate(evidence)
    base = _base_proposal(aggregate)
    components = _component_proposal(evidence["cards"])
    errors = [
        f"BASE_PROPOSAL_SCHEMA:{item}"
        for item in validate_json(base, root / "contracts/base_selection_proposal.schema.json")
    ]
    errors.extend(
        f"COMPONENT_PROPOSAL_SCHEMA:{item}"
        for item in validate_json(
            components, root / "contracts/component_selection_proposal.schema.json"
        )
    )
    outputs = {
        "research/upstream_candidates/dynamic_evaluation.csv": _dynamic_csv(evidence, aggregate),
        "research/upstream_candidates/dynamic_reviews/base_selection_proposal.json": json.dumps(
            base, ensure_ascii=False, sort_keys=True, indent=2
        )
        + "\n",
        "research/upstream_candidates/dynamic_reviews/component_selection_proposal.json": json.dumps(
            components, ensure_ascii=False, sort_keys=True, indent=2
        )
        + "\n",
        "reports/upstream_dynamic_eval.md": _dynamic_report(evidence, aggregate),
        "reports/base_selection_proposal.md": _base_report(base),
        "reports/component_portfolio_proposal.md": _component_report(evidence["cards"], components),
        "reports/human_gate_base_selection.md": _gate_report(base, evidence["cards"]),
    }
    return outputs, errors


def summarize_evaluation(root: Path, *, check: bool = False) -> dict:
    outputs, errors = build_outputs(root)
    mismatches: list[str] = []
    for relative, expected in outputs.items():
        path = root / relative
        if check:
            actual = path.read_text(encoding="utf-8") if path.is_file() else ""
            if actual != expected:
                mismatches.append(relative)
        elif not errors:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
    errors.extend(f"REPORT_STALE:{item}" for item in mismatches)
    hashes = {
        relative: file_sha256(root / relative)
        for relative in OUTPUT_PATHS
        if (root / relative).is_file()
    }
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "output_count": len(outputs),
        "hashes": hashes,
    }
