from cumcm_skill_lab.upstream_validation import validate_upstreams


def test_manifest_has_expected_enum_and_ignored_cache(repo_root):
    result = validate_upstreams(repo_root)
    assert result["candidate_count"] == 8
    assert result["component_card_count"] == 4
    assert result["cache_ignored"] is True
    assert result["errors"] == []
