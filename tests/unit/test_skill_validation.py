from pathlib import Path

from cumcm_skill_lab.skill_validation import parse_frontmatter, validate_skills

SKILL = """---
name: cumcm-modeling-evidence
description: Use for modeling. Do not use for paper prose.
---
body
"""


def _make_skill(root: Path, folder: str, content: str = SKILL):
    skill = root / ".agents/skills" / folder
    (skill / "agents").mkdir(parents=True)
    (skill / "SKILL.md").write_text(content, encoding="utf-8")
    (skill / "agents/openai.yaml").write_text(
        "policy:\n  allow_implicit_invocation: false\n", encoding="utf-8"
    )


def test_frontmatter_parses(tmp_path: Path):
    _make_skill(tmp_path, "cumcm-modeling-evidence")
    data = parse_frontmatter(tmp_path / ".agents/skills/cumcm-modeling-evidence/SKILL.md")
    assert data["name"] == "cumcm-modeling-evidence"


def test_duplicate_skill_name_is_rejected(tmp_path: Path):
    _make_skill(tmp_path, "one")
    _make_skill(tmp_path, "two")
    result = validate_skills(tmp_path, expected_count=2)
    assert "SKILL_DUPLICATE_NAME" in {item["id"] for item in result["errors"]}
