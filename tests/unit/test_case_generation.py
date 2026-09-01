import json

from cumcm_skill_lab.eval.case_generation import (
    CASE_IDS,
    fixture_manifest_hash,
    generate_artifacts,
    materialize,
    result_is_stale,
)


def test_generation_is_byte_reproducible():
    first = generate_artifacts(20260831)
    second = generate_artifacts(20260831)
    assert first == second
    assert len(first) == 29


def test_materialize_check_never_repairs_changed_fixture(tmp_path):
    ok, changed = materialize(tmp_path, check=False)
    assert not ok
    assert len(changed) == 29
    target = tmp_path / "evals/fixtures/phase-002/CASE-001/input/problem.md"
    target.write_text("changed", encoding="utf-8")
    ok, mismatches = materialize(tmp_path, check=True)
    assert not ok
    assert "evals/fixtures/phase-002/CASE-001/input/problem.md" in mismatches
    assert target.read_text(encoding="utf-8") == "changed"


def test_generated_cases_are_synthetic_and_candidate_neutral():
    artifacts = generate_artifacts()
    case_text = b"\n".join(value for key, value in artifacts.items() if "/cases/" in key)
    assert b"handsomezr" not in case_text.lower()
    assert b"yushui" not in case_text.lower()
    for case_id in CASE_IDS:
        assert any(case_id in path for path in artifacts)


def test_case_003_oracle_uses_independent_enumeration():
    artifacts = generate_artifacts()
    oracle = json.loads(artifacts["evals/fixtures/phase-002/CASE-003/oracle.json"])
    assert oracle["optimum"]["ids"] == ["A", "B"]
    assert oracle["optimum"]["value"] == 19
    assert oracle["baseline"]["value"] == 14


def test_fixture_hash_marks_old_result_stale(tmp_path):
    materialize(tmp_path)
    current = fixture_manifest_hash(tmp_path)
    assert not result_is_stale(tmp_path, {"fixture_manifest_hash": current})
    assert result_is_stale(tmp_path, {"fixture_manifest_hash": "0" * 64})
