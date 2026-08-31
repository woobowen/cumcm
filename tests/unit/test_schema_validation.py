from cumcm_skill_lab.schema_validation import validate_contracts


def test_all_positive_and_negative_contract_fixtures(repo_root):
    result = validate_contracts(repo_root)
    assert result["errors"] == []
    assert result["schema_count"] == 17
    assert result["valid_fixtures"] == 17
    assert result["invalid_rejected"] >= 7
