from pathlib import Path

from cumcm_skill_lab.repo_validation import scan_private_paths, scan_secrets


def test_synthetic_api_key_is_detected(tmp_path: Path):
    (tmp_path / "leak.txt").write_text("sk-" + "x" * 24, encoding="utf-8")
    result = scan_secrets(tmp_path)
    assert result["errors"][0]["id"] == "SECRET_OPENAI_KEY"


def test_normal_text_passes(tmp_path: Path):
    (tmp_path / "safe.txt").write_text("credential status UNKNOWN", encoding="utf-8")
    assert scan_secrets(tmp_path)["errors"] == []


def test_private_absolute_path_is_detected(tmp_path: Path):
    (tmp_path / "report.md").write_text(
        "workspace: /" + "home/example-user/private-project", encoding="utf-8"
    )
    result = scan_private_paths(tmp_path)
    assert result["errors"][0]["id"] == "PRIVATE_UNIX_HOME_PATH"


def test_redacted_repository_path_passes(tmp_path: Path):
    (tmp_path / "report.md").write_text("workspace: <REPO_ROOT>", encoding="utf-8")
    assert scan_private_paths(tmp_path)["errors"] == []
