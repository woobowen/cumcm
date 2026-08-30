"""Context-aware answer leakage indicators for formal project content."""

import re
from pathlib import Path

from .paths import relative

NEGATION = (
    "forbid",
    "forbidden",
    "never",
    "do not",
    "must not",
    "禁止",
    "不得",
    "reserved",
    "excluded",
    "ignored",
)
PATTERNS = {
    "LEAKAGE_VAULT_REFERENCE": re.compile(r"benchmark-vault(?:/|\\\\)\S+", re.IGNORECASE),
    "LEAKAGE_PROBLEM_NUMBER": re.compile(
        r"\b(?:19|20)\d{2}\s*(?:年|[-_/])?\s*[A-D]\s*(?:题|problem)\b", re.IGNORECASE
    ),
    "LEAKAGE_ANSWER_PLATFORM": re.compile(
        r"(?:题解|优秀论文|solution\s+blog|answer\s+repository)", re.IGNORECASE
    ),
}


def _allowed(line: str) -> bool:
    lowered = line.lower()
    return any(word in lowered for word in NEGATION)


def scan_leakage(root: Path):
    findings: list[dict] = []
    targets = [
        root / ".agents/skills",
        root / "benchmarks",
        root / "rules",
        root / "tests/fixtures",
    ]
    for base in targets:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or any(
                part in {".cache", ".venv", "__pycache__"} for part in path.parts
            ):
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for number, line in enumerate(lines, 1):
                if _allowed(line):
                    continue
                for finding_id, pattern in PATTERNS.items():
                    if pattern.search(line):
                        findings.append(
                            {"id": finding_id, "path": relative(path, root), "line": number}
                        )
    return {"findings": findings, "errors": findings}
