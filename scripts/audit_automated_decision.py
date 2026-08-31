#!/usr/bin/env python3
"""Run independent Decision Auditors and mechanically audit each automated decision."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.adjudication.decision_auditor import audit_decision_record, audit_payload
from cumcm_skill_lab.adjudication.judge_runner import run_structured_role
from cumcm_skill_lab.adjudication.models import check_or_write, read_json, read_yaml, sha256_json

AUDIT_SCHEMA = {
    "type": "object",
    "properties": {
        "role": {"type": "string", "enum": ["DECISION_AUDITOR"]},
        "result": {"type": "string", "enum": ["PASS", "FAIL"]},
        "checks": {"type": "object", "additionalProperties": {"type": "boolean"}},
        "failures": {"type": "array", "items": {"type": "string"}},
        "uncertainties": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["role", "result", "checks", "failures", "uncertainties"],
    "additionalProperties": False,
}


def _decision_paths():
    return sorted((ROOT / "evals/results/phase-002a/automated_decisions").glob("*.json"))


def _check_outputs() -> list[str]:
    errors = []
    for path in _decision_paths():
        audit_path = ROOT / "evals/results/phase-002a/decision_audit" / f"audit-{path.stem}.json"
        if not audit_path.is_file():
            errors.append(f"MISSING:{audit_path.relative_to(ROOT)}")
        elif read_json(audit_path).get("result") not in {"PASS", "FAIL"}:
            errors.append(f"INVALID:{audit_path.relative_to(ROOT)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify tracked audit records")
    parser.add_argument("--smoke", action="store_true", help="exercise mechanical audit only")
    parser.add_argument("--config", default="adjudication/configs/phase-002a.yaml")
    args = parser.parse_args()
    policy = read_yaml(ROOT / "adjudication/policies/phase-002a.yaml")
    if args.smoke:
        result = audit_payload(
            {}, policy_hash=policy["policy_hash"], expected_policy_hash=policy["policy_hash"]
        )
        print(
            json.dumps(
                {"status": "PASS" if result["result"] == "PASS" else "FAIL", **result},
                sort_keys=True,
            )
        )
        return 0 if result["result"] == "PASS" else 1
    if args.check:
        errors = _check_outputs()
        print(
            json.dumps(
                {"status": "PASS" if not errors else "FAIL", "errors": errors}, sort_keys=True
            )
        )
        return 0 if not errors else 1
    decisions = [read_json(path) for path in _decision_paths()]
    inputs = {
        "policy": policy,
        "decisions": decisions,
        "freeze": read_json(ROOT / "evals/results/phase-002a/evidence_freeze_manifest.json"),
        "eligibility": read_json(ROOT / "evals/results/phase-002a/eligibility/classification.json"),
        "blind_judges": [
            read_json(path)
            for path in sorted((ROOT / "evals/results/phase-002a/blind_judges").glob("*.json"))
        ],
        "dissent": read_json(ROOT / "evals/results/phase-002a/dissent/dissent-blind-real-002.json"),
        "meta": [
            read_json(path)
            for path in sorted(
                (ROOT / "evals/results/phase-002a/meta_adjudication").glob("meta-*.json")
            )
        ],
    }
    prompt = (
        "你是 DECISION_AUDITOR。只审查 inputs.json 中已冻结规则、证据链、Judge 独立性、"
        "Dissent、Meta 和自动决定的程序一致性。检查身份泄漏、recovery 排名、硬编码推荐、"
        "多数票、阈值改变、unsupported conclusion、规则或证据变更、重放以及网络措辞。"
        "技术结果可以是拒绝、弃权或证据不足；不得因其未接受而判 FAIL。"
        "只输出 output.schema.json 的 JSON。"
    )
    base = ROOT / "evals/results/phase-002a"
    ledgers = []
    agent_outputs = []
    for suffix in ("first", "swap"):
        current = inputs if suffix == "first" else {key: inputs[key] for key in reversed(inputs)}
        output, ledger = run_structured_role(
            ROOT,
            role="DECISION_AUDITOR",
            prompt=prompt,
            inputs=current,
            output_schema=AUDIT_SCHEMA,
            attempt_id=f"audit-{suffix}",
        )
        check_or_write(base / "decision_audit" / f"audit-agent-{suffix}.json", output, check=False)
        ledgers.append(ledger)
        agent_outputs.append(output)
    agent_pass = all(item["result"] == "PASS" for item in agent_outputs)
    errors = []
    audit_results = []
    for path, decision in zip(_decision_paths(), decisions, strict=True):
        audit = audit_decision_record(
            decision,
            policy_hash=policy["policy_hash"],
            expected_policy_hash=policy["policy_hash"],
            recovery_ranked=False,
            identity_leaked=False,
            replay_hash_verified=sha256_json(
                {key: value for key, value in decision.items() if key != "replay_hash"}
            )
            == decision["replay_hash"],
            raw_trace_tracked=False,
        )
        if not agent_pass:
            audit["checks"]["independent_agent_audits_pass"] = False
            audit["failures"].append("independent_agent_audits_pass")
            audit["result"] = "FAIL"
        else:
            audit["checks"]["independent_agent_audits_pass"] = True
        errors.extend(
            check_or_write(base / "decision_audit" / f"audit-{path.stem}.json", audit, check=False)
        )
        audit_results.append(audit)
    runtime = {
        "schema_version": "1.0.0",
        "real_agent_runs": ledgers,
        "real_agent_run_count": len(ledgers),
    }
    runtime["content_hash"] = sha256_json(runtime)
    errors.extend(check_or_write(base / "runtime/audit_agent_runs.json", runtime, check=False))
    overall = (
        "PASS" if not errors and all(item["result"] == "PASS" for item in audit_results) else "FAIL"
    )
    print(
        json.dumps(
            {
                "status": overall,
                "real_agent_runs": len(ledgers),
                "errors": errors,
                "agent_results": [item["result"] for item in agent_outputs],
            },
            sort_keys=True,
        )
    )
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
