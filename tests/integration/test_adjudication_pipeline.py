import json
from pathlib import Path

import pytest

from cumcm_skill_lab.adjudication.decision_engine import decide
from cumcm_skill_lab.adjudication.models import read_json
from cumcm_skill_lab.adjudication.replay import order_stable

CASE_PATHS = sorted(Path("evals/adjudication/cases").glob("CASE-ADJ-*.json"))


@pytest.mark.parametrize("relative", CASE_PATHS, ids=lambda path: path.stem)
def test_adjudication_case(repo_root, relative):
    case = read_json(repo_root / relative)
    assert decide(case["facts"])["decision"] == case["expected"]


def test_all_required_adjudication_cases_exist():
    assert len(CASE_PATHS) == 18


def test_all_cases_are_project_authored_and_answer_free(repo_root):
    text = "\n".join((repo_root / path).read_text(encoding="utf-8") for path in CASE_PATHS)
    assert "historical answer" not in text.lower()
    assert "excellent paper" not in text.lower()


def test_case_replay_is_order_stable(repo_root):
    for relative in CASE_PATHS:
        case = read_json(repo_root / relative)
        assert order_stable({"facts": case["facts"]})


def test_case_files_are_valid_json(repo_root):
    for relative in CASE_PATHS:
        json.loads((repo_root / relative).read_text(encoding="utf-8"))
