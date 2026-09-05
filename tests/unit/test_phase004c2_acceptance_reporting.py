import importlib.util
import json


def test_frozen_release_and_semantic_gaps_cannot_be_hidden(repo_root):
    spec = importlib.util.spec_from_file_location(
        "terminal_reporting", repo_root / "scripts/check_phase004c2_acceptance.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    base = repo_root / "evals/results/phase-004c2"
    release = json.loads((base / "rc5_release.json").read_text())
    block = json.loads((base / "rc5_release_acceptance_block.json").read_text())
    decision = json.loads(
        (
            base / "CUMCM-2019-C-VALIDATION-002/validation/DECISION-C-TARGET-VALIDATION-004C2.json"
        ).read_text()
    )
    state = json.loads((repo_root / "state/project_state.json").read_text())
    version = (repo_root / ".agents/skills/cumcm-modeling-evidence/VERSION").read_text()
    actual = module.assess(version, release, block, decision, state)
    assert actual["ok"] and actual["release_acceptance"] == "BLOCK"
    state["blockers"] = []
    state["risks"] = [item for item in state["risks"] if "RC5_VERSION_FILE_MISMATCH" not in item]
    hidden = module.assess(version, release, block, decision, state)
    assert "UNREPORTED_FROZEN_RELEASE_VERSION_MISMATCH" in hidden["errors"]
    decision["facts"]["pipeline_pass_requirements"]["requirement_claims_valid"] = True
    overclaim = module.assess(version, release, block, decision, state)
    assert "SEMANTIC_GAP_FALSELY_REPORTED_AS_COMPLETION" in overclaim["errors"]
