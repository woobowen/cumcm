from cumcm_skill_lab.eval.reporting import build_outputs, summarize_evaluation


def test_reporting_builds_required_offline_outputs(repo_root):
    outputs, errors = build_outputs(repo_root)
    assert errors == []
    assert len(outputs) == 7
    assert "reports/upstream_dynamic_eval.md" in outputs
    assert "GATE_BASE_SELECTION_PENDING" in outputs["reports/human_gate_base_selection.md"]
    assert "RECOMMEND_CLEAN_ROOM_ARCHITECTURE" in outputs["reports/base_selection_proposal.md"]
    assert outputs["research/upstream_candidates/dynamic_evaluation.csv"].count("\n") == 19


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
