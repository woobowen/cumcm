from pathlib import Path

from cumcm_skill_lab.instruction_validation import validate_instructions


def test_instruction_sizes_and_layering(tmp_path: Path):
    (tmp_path / "AGENTS.md").write_text("root", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "AGENTS.md").write_text("local", encoding="utf-8")
    result = validate_instructions(tmp_path)
    assert result["sizes"] == {"AGENTS.md": 4, "nested/AGENTS.md": 5}
    assert result["errors"] == []


def test_root_instruction_budget_fails(tmp_path: Path):
    (tmp_path / "AGENTS.md").write_text("x" * 9000, encoding="utf-8")
    result = validate_instructions(tmp_path)
    assert "INSTRUCTION_ROOT_BUDGET" in {item["id"] for item in result["errors"]}
