from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from cumcm_skill_lab.eval.models import load_json


def test_component_cards_are_limited_gap_bound_and_schema_valid(repo_root: Path):
    card_paths = sorted((repo_root / "research/upstream_candidates/component_cards").glob("*.yaml"))
    assert 0 < len(card_paths) <= 5
    schema = load_json(repo_root / "contracts/component_card.schema.json")
    validator = Draft202012Validator(schema)
    for path in card_paths:
        card = yaml.safe_load(path.read_text(encoding="utf-8"))
        validator.validate(card)
        assert card["reuse_mode"] == "CLEAN_ROOM_REIMPLEMENT_CANDIDATE"
        assert "CASE-" in card["actual_gap_addressed"]


def test_component_cards_never_offer_direct_reuse(repo_root: Path):
    for path in (repo_root / "research/upstream_candidates/component_cards").glob("*.yaml"):
        text = path.read_text(encoding="utf-8")
        assert "reuse_mode: DIRECT_REUSE_CANDIDATE" not in text
        assert "human_review_required: true" in text
