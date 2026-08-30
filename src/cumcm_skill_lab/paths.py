"""Path helpers that never escape the repository."""

from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / ".git").exists():
            return candidate
    raise RuntimeError("REPO_ROOT_NOT_FOUND: expected pyproject.toml and .git")


def relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def tracked_text_files(root: Path):
    excluded = {".git", ".venv", ".cache", "__pycache__", ".pytest_cache", ".ruff_cache"}
    for path in root.rglob("*"):
        if not path.is_file() or any(part in excluded for part in path.parts):
            continue
        try:
            path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        yield path
