from cumcm_skill_lab.specification.validation import VALIDATION_COMMANDS


def test_validation_matrix_contains_required_commands():
    command_ids = {item[0] for item in VALIDATION_COMMANDS}
    assert {
        "RUFF_CHECK",
        "RUFF_FORMAT",
        "PYTEST",
        "CONTRACTS",
        "PHASE002D_R2_FREEZE",
        "COMPONENT_SPECS",
        "BENCHMARK_VAULT",
        "THRESHOLD_FREEZE",
        "IMPLEMENTATION_EMBARGO",
        "R2_ADJUDICATION",
        "R2_DECISION_AUDIT",
        "R2_REPLAY",
        "R2_REPORTS",
        "STRICT_REPOSITORY",
        "OFFLINE_CI",
        "GIT_DIFF_CHECK",
        "GIT_STATUS",
    } <= command_ids


def test_validation_matrix_has_no_model_or_network_command():
    forbidden = ("codex", "curl", "wget", "benchmark-vault/")
    for _, argv in VALIDATION_COMMANDS:
        command = " ".join(argv)
        assert not any(token in command for token in forbidden)
