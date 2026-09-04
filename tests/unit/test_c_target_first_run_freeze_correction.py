from __future__ import annotations

import copy

import pytest

from scripts.check_c_target_first_run_freezes import canonical_hash
from scripts.supersede_c_target_first_run_freeze import build_corrected_freeze


def test_metadata_correction_preserves_original_and_fixes_full_rc3() -> None:
    original = {
        "freeze_id": "CASE-FIRST-RUN-FREEZE-001",
        "batch_skill_version": "RC3",
        "formal_skill_version": "0.2.0-competition-rc3",
        "freeze_hash": "a" * 64,
    }
    snapshot = copy.deepcopy(original)

    corrected = build_corrected_freeze(
        original,
        original_path="evals/results/original.json",
        original_sha256="b" * 64,
        original_commit="c" * 40,
        correction_time="2026-09-05T00:20:00+08:00",
        worktree_commit="d" * 40,
    )

    assert original == snapshot
    assert corrected["batch_skill_version"] == "0.2.0-competition-rc3"
    assert corrected["supersedes_freeze"]["sha256"] == "b" * 64
    assert corrected["metadata_correction"]["case_evidence_changed"] is False
    payload = dict(corrected)
    freeze_hash = payload.pop("freeze_hash")
    assert canonical_hash(payload) == freeze_hash


def test_metadata_correction_rejects_non_short_alias() -> None:
    with pytest.raises(ValueError, match="ORIGINAL_FREEZE_NOT_ELIGIBLE"):
        build_corrected_freeze(
            {
                "freeze_id": "CASE-FIRST-RUN-FREEZE-001",
                "batch_skill_version": "0.2.0-competition-rc3",
                "formal_skill_version": "0.2.0-competition-rc3",
            },
            original_path="original.json",
            original_sha256="b" * 64,
            original_commit="c" * 40,
            correction_time="2026-09-05T00:20:00+08:00",
            worktree_commit="d" * 40,
        )
