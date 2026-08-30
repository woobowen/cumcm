"""Validate discoverable repository Skills and frontmatter."""

from pathlib import Path

import yaml

from .constants import EXPECTED_SKILL
from .paths import relative


def parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        raise ValueError(f"SKILL_FRONTMATTER_MISSING: {path}")
    try:
        end = lines[1:].index("---") + 1
    except ValueError as exc:
        raise ValueError(f"SKILL_FRONTMATTER_UNCLOSED: {path}") from exc
    data = yaml.safe_load("\n".join(lines[1:end]))
    if not isinstance(data, dict):
        raise ValueError(f"SKILL_FRONTMATTER_TYPE: {path}")
    return data


def discover_skills(root: Path) -> list[Path]:
    skills = []
    for path in root.rglob("SKILL.md"):
        if any(part in {".git", ".cache", ".venv"} for part in path.parts):
            continue
        parent = path.parent
        if parent.parent.name == "skills" and parent.parent.parent.name == ".agents":
            skills.append(path)
    return sorted(skills)


def validate_skills(root: Path, expected_name: str = EXPECTED_SKILL, expected_count: int = 1):
    errors: list[dict] = []
    skills = discover_skills(root)
    if len(skills) != expected_count:
        errors.append(
            {"id": "SKILL_COUNT", "message": f"expected {expected_count}, found {len(skills)}"}
        )
    names: list[str] = []
    for path in skills:
        try:
            data = parse_frontmatter(path)
        except ValueError as exc:
            errors.append(
                {"id": "SKILL_FRONTMATTER", "message": str(exc), "path": relative(path, root)}
            )
            continue
        name = data.get("name")
        description = data.get("description")
        names.append(name)
        if name != expected_name:
            errors.append(
                {
                    "id": "SKILL_NAME",
                    "message": f"unexpected name {name!r}",
                    "path": relative(path, root),
                }
            )
        if (
            not isinstance(description, str)
            or "Use for" not in description
            or "Do not use" not in description
        ):
            errors.append(
                {
                    "id": "SKILL_DESCRIPTION_BOUNDARY",
                    "message": "description needs use and exclusion boundaries",
                    "path": relative(path, root),
                }
            )
    if len(names) != len(set(names)):
        errors.append({"id": "SKILL_DUPLICATE_NAME", "message": "duplicate Skill name detected"})
    policy = root / ".agents/skills" / expected_name / "agents/openai.yaml"
    try:
        metadata = yaml.safe_load(policy.read_text(encoding="utf-8"))
        if metadata.get("policy", {}).get("allow_implicit_invocation") is not False:
            errors.append(
                {
                    "id": "SKILL_IMPLICIT_POLICY",
                    "message": "foundation must disable implicit invocation",
                }
            )
    except (OSError, yaml.YAMLError, AttributeError) as exc:
        errors.append({"id": "SKILL_OPENAI_YAML", "message": str(exc)})
    return {"skills": [relative(path, root) for path in skills], "names": names, "errors": errors}
