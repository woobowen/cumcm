"""Compute layered AGENTS.md byte budgets and basic conflicts."""

from pathlib import Path

from .constants import CHAIN_WARNING_LIMIT, ROOT_AGENTS_LIMIT
from .paths import relative


def _agent_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("AGENTS.md")
        if not any(part in {".git", ".cache", ".venv"} for part in path.parts)
    )


def validate_instructions(root: Path):
    files = _agent_files(root)
    sizes = {relative(path, root): len(path.read_bytes()) for path in files}
    errors: list[dict] = []
    warnings: list[dict] = []
    root_size = sizes.get("AGENTS.md", 0)
    if root_size > ROOT_AGENTS_LIMIT:
        errors.append(
            {"id": "INSTRUCTION_ROOT_BUDGET", "message": f"root AGENTS.md is {root_size} bytes"}
        )
    root_file = root / "AGENTS.md"
    for path in files:
        chain = [root_file] if root_file.is_file() else []
        if path != root_file:
            current = path.parent
            nested: list[Path] = []
            while current != root and root in current.parents:
                candidate = current / "AGENTS.md"
                if candidate.is_file() and candidate != path:
                    nested.append(candidate)
                current = current.parent
            chain.extend(reversed(nested))
            chain.append(path)
        total = sum(len(item.read_bytes()) for item in dict.fromkeys(chain))
        if total > CHAIN_WARNING_LIMIT:
            warnings.append(
                {
                    "id": "INSTRUCTION_CHAIN_BUDGET",
                    "message": f"{relative(path, root)} chain is {total} bytes",
                }
            )
    return {
        "sizes": sizes,
        "total_project_bytes": sum(sizes.values()),
        "errors": errors,
        "warnings": warnings,
    }
