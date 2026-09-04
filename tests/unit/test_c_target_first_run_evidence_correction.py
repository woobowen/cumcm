from __future__ import annotations

import copy
import hashlib
import json

from scripts.supersede_c_target_first_run_evidence import (
    ALLOWED_CHANGED_ARTIFACTS,
    build_corrected_freeze,
    canonical_hash,
)


def _hash(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_evidence_correction_changes_only_declared_summaries(tmp_path) -> None:
    root = tmp_path / "case"
    hashes = {}
    for relative in sorted(ALLOWED_CHANGED_ARTIFACTS):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "content": {
                        "manual_intervention_count": 0,
                        "value": f"new-{relative}",
                    }
                }
            ),
            encoding="utf-8",
        )
        hashes[relative] = "a" * 64
    state = root / "case_state.json"
    state.write_text("{}\n", encoding="utf-8")
    manifest = root / "runs/RUN-1/manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text("{}\n", encoding="utf-8")
    original = {
        "freeze_id": "CASE-FIRST-RUN-FREEZE-001",
        "case_state_sha256": "b" * 64,
        "first_run_artifact_hashes": hashes,
        "run_manifest_hashes": {"runs/RUN-1/manifest.json": _hash(manifest)},
        "failure_hashes": {},
        "timing_hash": "c" * 64,
        "manual_intervention_count": 0,
        "freeze_hash": "d" * 64,
    }
    snapshot = copy.deepcopy(original)

    corrected = build_corrected_freeze(
        original,
        original_path="first_run_freeze.json",
        original_sha256="e" * 64,
        original_commit="f" * 40,
        worktree_commit="1" * 40,
        correction_time="2026-09-05T00:45:00+08:00",
        case_root=root,
    )

    assert original == snapshot
    assert corrected["run_manifest_hashes"] == original["run_manifest_hashes"]
    assert set(corrected["evidence_correction"]["changed_artifacts"]) == (ALLOWED_CHANGED_ARTIFACTS)
    assert corrected["evidence_correction"]["run_evidence_changed"] is False
    payload = dict(corrected)
    digest = payload.pop("freeze_hash")
    assert canonical_hash(payload) == digest
