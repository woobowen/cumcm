from cumcm_skill_lab.schema_validation import validate_contracts


def test_all_positive_and_negative_contract_fixtures(repo_root):
    result = validate_contracts(repo_root)
    assert result["errors"] == []
    expected_schemas = len(list((repo_root / "contracts").glob("*.schema.json")))
    expected_invalid = len(list((repo_root / "tests/fixtures/contracts/invalid").glob("*.json")))
    assert result["schema_count"] == expected_schemas
    assert result["valid_fixtures"] == expected_schemas
    assert result["invalid_rejected"] == expected_invalid
