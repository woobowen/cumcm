import json

from jsonschema import Draft202012Validator

from cumcm_skill_lab.eval.reporting import build_outputs, summarize_evaluation


def test_reporting_builds_required_offline_outputs(repo_root):
    outputs, errors = build_outputs(repo_root)
    assert errors == []
    assert len(outputs) == 7
    assert "reports/upstream_dynamic_eval.md" in outputs
    assert "GATE_BASE_SELECTION_PENDING" in outputs["reports/human_gate_base_selection.md"]
    assert "RECOMMEND_CLEAN_ROOM_ARCHITECTURE" in outputs["reports/base_selection_proposal.md"]
    assert outputs["research/upstream_candidates/dynamic_evaluation.csv"].count("\n") == 19
    base = json.loads(
        outputs["research/upstream_candidates/dynamic_reviews/base_selection_proposal.json"]
    )
    components = json.loads(
        outputs["research/upstream_candidates/dynamic_reviews/component_selection_proposal.json"]
    )
    assert base["status"] == "PROPOSAL_ONLY"
    assert base["human_gate"] == "GATE_BASE_SELECTION_PENDING"
    assert base["base_selected"] is False
    assert components["third_party_integrated"] is False


def test_reporting_check_detects_and_recovers_stale_file(repo_root, tmp_path):
    outputs, errors = build_outputs(repo_root)
    assert errors == []
    relative = "reports/upstream_dynamic_eval.md"
    target = repo_root / relative
    original = target.read_text(encoding="utf-8") if target.exists() else None
    target.write_text("stale\n", encoding="utf-8")
    try:
        assert summarize_evaluation(repo_root, check=True)["status"] == "FAIL"
        assert any(
            item == f"REPORT_STALE:{relative}"
            for item in summarize_evaluation(repo_root, check=True)["errors"]
        )
        target.write_text(outputs[relative], encoding="utf-8")
        for path, text in outputs.items():
            if path != relative and not (repo_root / path).exists():
                (repo_root / path).parent.mkdir(parents=True, exist_ok=True)
                (repo_root / path).write_text(text, encoding="utf-8")
        assert summarize_evaluation(repo_root, check=True)["status"] == "PASS"
    finally:
        if original is None:
            target.unlink(missing_ok=True)
        else:
            target.write_text(original, encoding="utf-8")


def test_not_run_score_is_missing_not_zero(repo_root):
    fixture = json.loads((repo_root / "tests/fixtures/contracts/valid/eval_score.json").read_text())
    fixture.update(
        {
            "status": "NOT_RUN",
            "deterministic_score": None,
            "reviewer_score": None,
            "total_score": None,
            "dimensions": {},
            "evidence": [],
            "missing": ["run not attempted"],
            "confidence": "UNKNOWN",
        }
    )
    schema = json.loads((repo_root / "contracts/eval_score.schema.json").read_text())
    Draft202012Validator(schema).validate(fixture)
