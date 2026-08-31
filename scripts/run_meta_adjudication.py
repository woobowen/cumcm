#!/usr/bin/env python3
"""Run Evidence Meta-Adjudicator roles and emit deterministic machine decisions."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.adjudication.decision_records import build_decisions
from cumcm_skill_lab.adjudication.judge_runner import build_anonymous_bundle, run_structured_role
from cumcm_skill_lab.adjudication.meta_adjudicator import adjudicate
from cumcm_skill_lab.adjudication.models import check_or_write, read_json, read_yaml, sha256_json

META_SCHEMA = {
    "type": "object",
    "properties": {
        "role": {"type": "string", "enum": ["EVIDENCE_META_ADJUDICATOR"]},
        "policy_hash": {"type": "string"},
        "thresholds_unchanged": {"type": "boolean", "const": True},
        "majority_vote_used": {"type": "boolean", "const": False},
        "architecture_decision": {
            "type": "string",
            "enum": [
                "AUTOMATED_ACCEPTED",
                "AUTOMATED_REJECTED",
                "RETEST_REQUIRED",
                "EVIDENCE_INSUFFICIENT",
                "AUTOMATED_ABSTAINED",
                "STALE",
            ],
        },
        "reason_codes": {"type": "array", "items": {"type": "string"}},
        "unresolved_blockers": {"type": "array", "items": {"type": "string"}},
        "uncertainties": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "role",
        "policy_hash",
        "thresholds_unchanged",
        "majority_vote_used",
        "architecture_decision",
        "reason_codes",
        "unresolved_blockers",
        "uncertainties",
    ],
    "additionalProperties": False,
}


def _meta_records(decisions: list[dict], policy: dict, freeze: dict) -> list[dict]:
    return [
        {
            "meta_id": f"META-{item['decision_id']}",
            "bundle_id": "ANON-EVIDENCE-PHASE-002A",
            "policy_hash": policy["policy_hash"],
            "freeze_hash": freeze["freeze_hash"],
            "thresholds_unchanged": True,
            "majority_vote_used": False,
            "hard_gate_status": item["hard_gate_status"],
            "evidence_sufficiency": item["evidence_sufficiency"],
            "test_evidence": item["tests"],
            "decision": item["decision"],
            "reason_codes": item["reason_codes"],
        }
        for item in decisions
    ]


def _check_outputs() -> list[str]:
    expected = [
        ROOT / "evals/results/phase-002a/meta_adjudication" / f"meta-{name}.json"
        for name in ("architecture", "recovery_policy", "components")
    ]
    expected += [
        ROOT / "evals/results/phase-002a/automated_decisions" / f"{name}.json"
        for name in ("architecture", "recovery_policy", "components")
    ]
    return [f"MISSING:{path.relative_to(ROOT)}" for path in expected if not path.is_file()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify tracked outputs")
    parser.add_argument(
        "--smoke", action="store_true", help="exercise deterministic meta policy only"
    )
    parser.add_argument("--config", default="adjudication/configs/phase-002a.yaml")
    args = parser.parse_args()
    policy = read_yaml(ROOT / "adjudication/policies/phase-002a.yaml")
    freeze = read_json(ROOT / "evals/results/phase-002a/evidence_freeze_manifest.json")
    if args.smoke:
        result = adjudicate(
            bundle_id="SMOKE",
            policy=policy,
            freeze_hash=freeze["freeze_hash"],
            facts={"hard_gates": {"license": True}, "evidence_sufficiency": "INSUFFICIENT"},
            test_evidence=[],
        )
        print(json.dumps({"status": "PASS", "decision": result["decision"]}, sort_keys=True))
        return 0
    if args.check:
        errors = _check_outputs()
        print(
            json.dumps(
                {"status": "PASS" if not errors else "FAIL", "errors": errors}, sort_keys=True
            )
        )
        return 0 if not errors else 1
    bundle = build_anonymous_bundle(ROOT)
    judge_outputs = [
        read_json(path)
        for path in sorted((ROOT / "evals/results/phase-002a/blind_judges").glob("*.json"))
    ]
    dissent = read_json(ROOT / "evals/results/phase-002a/dissent/dissent-real-001.json")
    tests = read_json(ROOT / "evals/results/phase-002a/adversarial/test_evidence.json")
    inputs = {
        "policy": policy,
        "evidence_bundle": bundle,
        "judge_outputs": judge_outputs,
        "dissent": dissent,
        "test_evidence": tests,
    }
    prompt = (
        "你是 EVIDENCE_META_ADJUDICATOR。只读取 inputs.json。"
        "按冻结策略的字典序 Gate 应用证据；不得改阈值、补证据、按多数票、"
        "覆盖 hard failure 或猜候选身份。重大 dissent 未被可执行测试关闭时必须保留。"
        "输出 output.schema.json 要求的 JSON。"
    )
    base = ROOT / "evals/results/phase-002a"
    ledgers = []
    for suffix in ("first", "swap"):
        current = inputs if suffix == "first" else {key: inputs[key] for key in reversed(inputs)}
        output, ledger = run_structured_role(
            ROOT,
            role="EVIDENCE_META_ADJUDICATOR",
            prompt=prompt,
            inputs=current,
            output_schema=META_SCHEMA,
            attempt_id=f"meta-{suffix}",
        )
        check_or_write(
            base / "meta_adjudication" / f"meta-agent-{suffix}.json", output, check=False
        )
        ledgers.append(ledger)
    decisions = build_decisions(ROOT)
    metas = _meta_records(decisions, policy, freeze)
    errors = []
    names = ("architecture", "recovery_policy", "components")
    for name, meta, decision in zip(names, metas, decisions, strict=True):
        errors.extend(
            check_or_write(base / "meta_adjudication" / f"meta-{name}.json", meta, check=False)
        )
        errors.extend(
            check_or_write(base / "automated_decisions" / f"{name}.json", decision, check=False)
        )
    runtime = {
        "schema_version": "1.0.0",
        "real_agent_runs": ledgers,
        "real_agent_run_count": len(ledgers),
    }
    runtime["content_hash"] = sha256_json(runtime)
    errors.extend(check_or_write(base / "runtime/meta_agent_runs.json", runtime, check=False))
    print(
        json.dumps(
            {
                "status": "PASS" if not errors else "FAIL",
                "real_agent_runs": len(ledgers),
                "architecture_decision": decisions[0]["decision"],
                "errors": errors,
            },
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
