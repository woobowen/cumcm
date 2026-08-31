from cumcm_skill_lab.eval.safety import (
    inspect_source_entry,
    normalized_instruction_findings,
)


def _ids(findings):
    return {item["id"] for item in findings}


def test_sanitized_package_rejects_python():
    findings = inspect_source_entry("candidate.py", "100644", b"print('not executed')")
    assert "SOURCE_EXTENSION_NOT_ALLOWED" in _ids(findings)
    assert "SOURCE_CODE_FORBIDDEN" in _ids(findings)


def test_sanitized_package_rejects_shell():
    findings = inspect_source_entry("candidate.sh", "100644", b"echo no")
    assert "SOURCE_CODE_FORBIDDEN" in _ids(findings)


def test_sanitized_package_rejects_executable_markdown():
    findings = inspect_source_entry("instructions.md", "100755", b"plain text")
    assert "SOURCE_EXECUTABLE_FORBIDDEN" in _ids(findings)


def test_contamination_scan_detects_demo_and_answer_terms():
    findings = inspect_source_entry(
        "notes.md", "100644", "CUMCM2024-B 优秀论文 final_paper".encode()
    )
    ids = _ids(findings)
    assert "SOURCE_HISTORICAL_DEMO" in ids
    assert "SOURCE_ANSWER_OR_WINNING_MATERIAL" in ids
    assert "SOURCE_DEMO_RESULT" in ids


def test_normalized_instruction_rejects_install_network_and_mcp():
    findings = normalized_instruction_findings("Install via requests and start MCP")
    ids = _ids(findings)
    assert "NORMALIZED_INSTALL_OR_GLOBAL_MUTATION" in ids
    assert "NORMALIZED_NETWORK_OR_DOWNLOADER" in ids
    assert "NORMALIZED_MCP_OR_HOOK" in ids


def test_clean_normalized_instruction_passes():
    assert normalized_instruction_findings("Record hashes and stop when evidence is absent.") == []
