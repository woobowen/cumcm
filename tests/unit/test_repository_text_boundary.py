import subprocess
from pathlib import Path

from cumcm_skill_lab.paths import tracked_text_files


def test_text_scan_includes_new_code_but_not_ignored_local_input(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text("local-task.md\n")
    (tmp_path / "local-task.md").write_text("user input")
    (tmp_path / "new-code.py").write_text("print('new')\n")
    names = {p.name for p in tracked_text_files(tmp_path)}
    assert "new-code.py" in names
    assert "local-task.md" not in names


def test_sealed_directory_and_symlink_are_never_read(tmp_path: Path, monkeypatch) -> None:
    sealed = tmp_path / "benchmark-vault"
    sealed.mkdir()
    secret = sealed / "sealed.txt"
    secret.write_text("fixture only")
    (tmp_path / "linked.txt").symlink_to(secret)
    (tmp_path / "public.txt").write_text("public")
    original = Path.read_text

    def guarded_read(path, *args, **kwargs):
        assert path.resolve() != secret.resolve(), "sealed input was read"
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read)
    assert [p.name for p in tracked_text_files(tmp_path)] == ["public.txt"]
