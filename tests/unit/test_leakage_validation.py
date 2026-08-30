from pathlib import Path

from cumcm_skill_lab.leakage_validation import scan_leakage


def test_policy_negation_is_allowlisted(tmp_path: Path):
    path = tmp_path / "benchmarks"
    path.mkdir()
    (path / "AGENTS.md").write_text("Do not read benchmark-vault/answers", encoding="utf-8")
    assert scan_leakage(tmp_path)["findings"] == []


def test_unqualified_vault_reference_fails(tmp_path: Path):
    path = tmp_path / "benchmarks"
    path.mkdir()
    (path / "bad.txt").write_text("load benchmark-vault/answers.json", encoding="utf-8")
    result = scan_leakage(tmp_path)
    assert result["findings"][0]["id"] == "LEAKAGE_VAULT_REFERENCE"
