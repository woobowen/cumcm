"""Fail-closed checks for candidate-derived plaintext evaluation packages."""

import re
from pathlib import PurePosixPath

ALLOWED_SUFFIXES = {".md", ".markdown", ".yaml", ".yml", ".json", ".txt"}
FORBIDDEN_SUFFIXES = {
    ".py",
    ".sh",
    ".bash",
    ".js",
    ".ts",
    ".mjs",
    ".cjs",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".bin",
}
CONTAMINATION_PATTERNS = {
    "HISTORICAL_DEMO": re.compile(r"(?:20\d{2}[-_ ]?[A-D]|cumcm20\d{2})", re.I),
    "ANSWER_OR_WINNING_MATERIAL": re.compile(
        r"(?:优秀论文|获奖论文|题解|winning[_ -]?paper)", re.I
    ),
    "DEMO_RESULT": re.compile(r"(?:final_paper|paper_output/(?:results|tables|figures))", re.I),
}
DANGEROUS_TEXT_PATTERNS = {
    "INSTALL_OR_GLOBAL_MUTATION": re.compile(r"(?:\binstall\b|~/.codex|~/.agents)", re.I),
    "NETWORK_OR_DOWNLOADER": re.compile(r"(?:curl|wget|playwright|requests\b|https?://)", re.I),
    "MCP_OR_HOOK": re.compile(r"(?:\bmcp\b|\bhook\b)", re.I),
    "DESTRUCTIVE_OR_BYPASS": re.compile(
        r"(?:rm\s+-rf|reset\s+--hard|clean\s+-fd|--yolo|dangerously)", re.I
    ),
}


def scan_text(text: str, patterns: dict[str, re.Pattern]) -> list[str]:
    return sorted(name for name, pattern in patterns.items() if pattern.search(text))


def inspect_source_entry(path: str, mode: str, data: bytes) -> list[dict]:
    findings: list[dict] = []
    suffix = PurePosixPath(path).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        findings.append({"id": "SOURCE_EXTENSION_NOT_ALLOWED", "path": path, "suffix": suffix})
    if suffix in FORBIDDEN_SUFFIXES:
        findings.append({"id": "SOURCE_CODE_FORBIDDEN", "path": path, "suffix": suffix})
    if int(mode, 8) & 0o111:
        findings.append({"id": "SOURCE_EXECUTABLE_FORBIDDEN", "path": path, "mode": mode})
    if b"\x00" in data:
        findings.append({"id": "SOURCE_BINARY_FORBIDDEN", "path": path})
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        findings.append({"id": "SOURCE_NOT_UTF8", "path": path})
        return findings
    for item in scan_text(text, CONTAMINATION_PATTERNS):
        findings.append({"id": f"SOURCE_{item}", "path": path})
    return findings


def normalized_instruction_findings(text: str) -> list[dict]:
    findings: list[dict] = []
    for item in scan_text(text, CONTAMINATION_PATTERNS):
        findings.append({"id": f"NORMALIZED_{item}"})
    for item in scan_text(text, DANGEROUS_TEXT_PATTERNS):
        findings.append({"id": f"NORMALIZED_{item}"})
    return findings
