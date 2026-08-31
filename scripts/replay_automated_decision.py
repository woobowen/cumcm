#!/usr/bin/env python3
"""Rebuild and verify Phase 002A decision hashes offline, including order/identity transforms."""

import argparse
import json

from _bootstrap import ROOT

from cumcm_skill_lab.adjudication.models import check_or_write, read_json, sha256_json


def replay_records() -> list[dict]:
    records = []
    for path in sorted((ROOT / "evals/results/phase-002a/automated_decisions").glob("*.json")):
        decision = read_json(path)
        body = {key: value for key, value in decision.items() if key != "replay_hash"}
        recomputed = sha256_json(body)
        transformed = dict(reversed(list(body.items())))
        records.append(
            {
                "decision_id": decision["decision_id"],
                "recorded_replay_hash": decision["replay_hash"],
                "recomputed_replay_hash": recomputed,
                "hash_verified": recomputed == decision["replay_hash"],
                "order_transformed_content_hash": sha256_json(transformed),
                "order_stable": sha256_json(transformed) == recomputed,
                "identity_swap_applicable": False,
                "identity_stable": True,
                "decision": decision["decision"],
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify replay output without writes")
    parser.add_argument("--config", default="adjudication/configs/phase-002a.yaml")
    args = parser.parse_args()
    records = replay_records()
    value = {"schema_version": "1.0.0", "records": records}
    value["content_hash"] = sha256_json(value)
    errors = []
    if not records:
        errors.append("NO_DECISIONS")
    if not all(item["hash_verified"] and item["order_stable"] for item in records):
        errors.append("REPLAY_MISMATCH")
    if not errors:
        errors.extend(
            check_or_write(
                ROOT / "evals/results/phase-002a/replay/replay.json",
                value,
                check=args.check,
            )
        )
    print(
        json.dumps(
            {"status": "PASS" if not errors else "FAIL", "records": len(records), "errors": errors},
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
