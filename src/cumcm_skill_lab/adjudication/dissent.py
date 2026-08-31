"""Dissent helpers keep minority counterexamples separate from votes."""

from __future__ import annotations


def build_dissent(bundle_id: str, findings: list[dict]) -> dict:
    serious = [item for item in findings if item["severity"] in {"BLOCKER", "ERROR"}]
    return {
        "dissent_id": f"DISSENT-{bundle_id}",
        "bundle_id": bundle_id,
        "independent": True,
        "findings": [item["finding_id"] for item in findings],
        "strongest_counterexample": (
            serious[0]["statement"] if serious else "No executable counterexample found."
        ),
        "test_requests": [f"TEST-{item['finding_id']}" for item in serious],
        "unresolved_blockers": [
            item["finding_id"] for item in findings if item["severity"] == "BLOCKER"
        ],
    }
