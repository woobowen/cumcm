"""Path helpers that never escape the repository."""

import os
import subprocess
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
    excluded = {
        ".git",
        ".venv",
        ".cache",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        "benchmark-vault",
        "local-answers",
        "reference-answers",
        "secrets",
    }
    if (root / ".git").exists():
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=root,
            capture_output=True,
            check=True,
        )
        paths = [root / os.fsdecode(name) for name in result.stdout.split(b"\0") if name]
    else:
        # Fixture trees have no Git metadata. Prune sealed directories before traversal.
        paths = []
        for directory, children, files in os.walk(root):
            children[:] = [name for name in children if name not in excluded]
            paths.extend(Path(directory) / name for name in files)
    for path in sorted(set(paths)):
        if (
            not path.is_file()
            or path.is_symlink()
            or any(part in excluded for part in path.relative_to(root).parts)
        ):
            continue
        try:
            path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        yield path
