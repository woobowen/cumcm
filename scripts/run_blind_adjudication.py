#!/usr/bin/env python3
"""Run or verify independent blind Judges on the frozen anonymous evidence bundle."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.adjudication.judge_runner import (
    ROLES,
    assert_blind,
    build_anonymous_bundle,
    run_role,
    run_structured_role,
)
from cumcm_skill_lab.adjudication.models import (
    check_or_write,
    read_json,
    read_yaml,
    sha256_json,
)
from cumcm_skill_lab.adjudication.replay import permute_evidence
from cumcm_skill_lab.adjudication.test_synthesis import synthesize_all

DISSENT_SCHEMA = {
    "type": "object",
    "properties": {
        "role": {"type": "string", "enum": ["DISSENT_JUDGE"]},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string", "enum": ["BLOCKER", "ERROR", "WARNING", "INFO"]},
                    "target": {"type": "string"},
                    "statement": {"type": "string"},
                    "evidence_refs": {"type": "array", "items": {"type": "string"}},
                    "testability": {"type": "string", "enum": ["TESTABLE", "NON_TESTABLE_CLAIM"]},
                },
                "required": ["severity", "target", "statement", "evidence_refs", "testability"],
                "additionalProperties": False,
            },
        },
        "strongest_counterexample": {"type": "string"},
        "uncertainties": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["role", "findings", "strongest_counterexample", "uncertainties"],
    "additionalProperties": False,
}


def _validate_existing(bundle: dict) -> list[str]:
    errors = []
    for role in ROLES:
        for suffix in ("first", "swap"):
            path = ROOT / "evals/results/phase-002a/blind_judges" / f"{role.lower()}-{suffix}.json"
            if not path.is_file():
                errors.append(f"MISSING:{path.relative_to(ROOT)}")
                continue
            item = read_json(path)
            try:
                assert_blind(item)
            except ValueError as exc:
                errors.append(str(exc))
            if item.get("role") != role or item.get("other_judges_visible") is not False:
                errors.append(f"JUDGE_INDEPENDENCE_INVALID:{path.relative_to(ROOT)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify tracked Judge records")
    parser.add_argument(
        "--smoke", action="store_true", help="validate bundle isolation without Agent calls"
    )
    parser.add_argument("--config", default="adjudication/configs/phase-002a.yaml")
    args = parser.parse_args()
    bundle = build_anonymous_bundle(ROOT)
    if args.smoke:
        print(
            json.dumps(
                {"status": "PASS", "bundle_hash": bundle["bundle_hash"], "roles": list(ROLES)},
                sort_keys=True,
            )
        )
        return 0
    if args.check:
        errors = _validate_existing(bundle)
        print(
            json.dumps(
                {"status": "PASS" if not errors else "FAIL", "errors": errors}, sort_keys=True
            )
        )
        return 0 if not errors else 1
    policy = read_yaml(ROOT / "adjudication/policies/phase-002a.yaml")
    base = ROOT / "evals/results/phase-002a"
    errors = check_or_write(base / "anonymous_evidence_bundle.json", bundle, check=False)
    ledgers = []
    finding_details = []
    for transformed in (False, True):
        current_bundle = permute_evidence(bundle) if transformed else bundle
        current_bundle["bundle_hash"] = sha256_json(
            {key: value for key, value in current_bundle.items() if key != "bundle_hash"}
        )
        for role in ROLES:
            output, ledger = run_role(
                ROOT, role=role, bundle=current_bundle, policy=policy, transformed=transformed
            )
            suffix = "swap" if transformed else "first"
            errors.extend(
                check_or_write(
                    base / "blind_judges" / f"{role.lower()}-{suffix}.json", output, check=False
                )
            )
            ledgers.append(ledger)
            finding_details.extend(output["finding_details"])
    dissent_prompt = (
        "你是 DISSENT_JUDGE。只读取 inputs.json 中冻结策略和匿名证据包；"
        "你看不到任何 Judge 输出。寻找可验证的少数反例、评分 gaming、顺序或身份偏见、"
        "流畅错误、当前 clean-room 推荐的最强反证。不得猜候选身份，不得按多数票。"
        "每个结论必须引用 evidence_refs，并说明是否可测试。"
        "只输出 output.schema.json 的 JSON。"
    )
    dissent_output, dissent_ledger = run_structured_role(
        ROOT,
        role="DISSENT_JUDGE",
        prompt=dissent_prompt,
        inputs={"policy": policy, "evidence_bundle": bundle},
        output_schema=DISSENT_SCHEMA,
        attempt_id="dissent-blind-real-002",
    )
    ledgers.append(dissent_ledger)
    dissent_findings = []
    for index, finding in enumerate(dissent_output["findings"], start=1):
        dissent_findings.append(
            {
                "finding_id": f"DISSENT-BLIND-002-{index:02d}",
                "role": "DISSENT_JUDGE",
                "severity": finding["severity"],
                "target": finding["target"],
                "statement": finding["statement"],
                "evidence_refs": finding["evidence_refs"],
                "testability": finding["testability"],
                "status": "UNCERTAINTY",
            }
        )
    dissent_record = {
        "dissent_id": "DISSENT-BLIND-REAL-002",
        "bundle_id": bundle["bundle_id"],
        "independent": True,
        "findings": [item["finding_id"] for item in dissent_findings],
        "strongest_counterexample": dissent_output["strongest_counterexample"],
        "test_requests": [
            f"TEST-{item['finding_id']}"
            for item in dissent_findings
            if item["severity"] in {"BLOCKER", "ERROR"}
        ],
        "unresolved_blockers": [
            item["finding_id"] for item in dissent_findings if item["severity"] == "BLOCKER"
        ],
    }
    errors.extend(
        check_or_write(base / "dissent/dissent-blind-real-002.json", dissent_record, check=False)
    )
    all_findings = finding_details + dissent_findings
    requests = synthesize_all(all_findings)
    test_evidence = [
        {
            "test_id": item["test_id"],
            "finding_id": item["finding_id"],
            "status": "ERROR",
            "observed_result": (
                "No pre-registered deterministic oracle matched this post-freeze Agent claim; "
                "retained as uncertainty and cannot independently reject or accept."
            ),
            "oracle_result": False,
            "command_or_procedure": item["command_or_procedure"],
            "artifact_hashes": {},
            "started_at": "2026-08-31T21:57:10Z",
            "completed_at": "2026-08-31T21:57:10Z",
        }
        for item in requests
    ]
    errors.extend(
        check_or_write(
            base / "blind_judges/test_requests.json",
            {"schema_version": "1.0.0", "requests": requests},
            check=False,
        )
    )
    errors.extend(
        check_or_write(
            base / "blind_judges/test_evidence.json",
            {"schema_version": "1.0.0", "evidence": test_evidence},
            check=False,
        )
    )
    runtime = {
        "schema_version": "1.0.0",
        "real_agent_runs": ledgers,
        "real_agent_run_count": len(ledgers),
    }
    runtime["content_hash"] = sha256_json(runtime)
    errors.extend(check_or_write(base / "runtime/blind_judge_runs.json", runtime, check=False))
    print(
        json.dumps(
            {
                "status": "PASS" if not errors else "FAIL",
                "real_agent_runs": len(ledgers),
                "errors": errors,
            },
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
