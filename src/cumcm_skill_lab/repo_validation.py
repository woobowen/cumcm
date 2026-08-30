"""Composite repository validation with stable finding identifiers."""

import csv
import json
import re
import subprocess
from pathlib import Path

import yaml

from .constants import REQUIRED_PATHS
from .instruction_validation import validate_instructions
from .leakage_validation import scan_leakage
from .paths import relative, tracked_text_files
from .report_generation import generate_status
from .schema_validation import validate_contracts
from .skill_validation import validate_skills
from .upstream_validation import validate_upstreams

SECRET_PATTERNS = {
    "SECRET_PRIVATE_KEY": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "SECRET_OPENAI_KEY": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "SECRET_GITHUB_TOKEN": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "SECRET_PASSWORD_ASSIGNMENT": re.compile(
        r"(?i)\b(?:password|api_key|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]"
    ),
}


def scan_secrets(root: Path):
    errors: list[dict] = []
    for path in tracked_text_files(root):
        rel = relative(path, root)
        if path.name == ".env" or path.name.startswith(".env.") and path.name != ".env.example":
            errors.append({"id": "SECRET_ENV_FILE", "path": rel})
        text = path.read_text(encoding="utf-8")
        for finding_id, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append({"id": finding_id, "path": rel})
    return {"errors": errors}


def _validate_yaml(root: Path):
    errors: list[dict] = []
    count = 0
    for path in tracked_text_files(root):
        if path.suffix not in {".yaml", ".yml"}:
            continue
        count += 1
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            errors.append({"id": "YAML_PARSE", "path": relative(path, root), "message": str(exc)})
    return count, errors


def _validate_csv(root: Path):
    expected = {
        "LICENSE_LEDGER.csv": [
            "candidate_id",
            "repository_url",
            "resolved_commit",
            "repository_license",
            "detected_from",
            "license_confidence",
            "subcomponent",
            "subcomponent_license",
            "redistribution_allowed",
            "modification_allowed",
            "attribution_required",
            "notice_required",
            "incompatible_or_unknown",
            "intended_reuse_mode",
            "reviewer",
            "reviewed_at",
            "notes",
        ],
        "research/upstream_candidates/skill_inventory.csv": [
            "candidate_id",
            "skill_path",
            "skill_name",
            "status",
            "claimed_capabilities",
            "observed_capabilities",
            "unverified_capabilities",
            "conflicts",
            "candidate_components",
            "dynamic_tests_required",
            "evidence",
        ],
        "research/upstream_candidates/static_evaluation.csv": [
            "candidate_id",
            "scope_fit_15",
            "recovery_15",
            "coverage_20",
            "review_gates_15",
            "evidence_10",
            "codex_10",
            "maintainability_5",
            "license_security_10",
            "total_provisional",
            "confidence",
            "status",
            "evidence",
        ],
    }
    errors: list[dict] = []
    for rel, columns in expected.items():
        path = root / rel
        if not path.is_file():
            errors.append({"id": "CSV_MISSING", "path": rel})
            continue
        with path.open(encoding="utf-8", newline="") as handle:
            header = next(csv.reader(handle), [])
        if header != columns:
            errors.append({"id": "CSV_COLUMNS", "path": rel, "message": f"expected {columns}"})
    return errors


def _tracked_path_errors(root: Path):
    output = subprocess.run(
        ["git", "ls-files"], cwd=root, check=False, capture_output=True, text=True
    ).stdout.splitlines()
    forbidden = (".cache/", ".venv/", "benchmark-vault/", "secrets/")
    return [
        {"id": "FORBIDDEN_TRACKED_PATH", "path": item}
        for item in output
        if item.startswith(forbidden)
    ]


def _script_risks(root: Path):
    errors: list[dict] = []
    patterns = (
        "rm -rf",
        "curl | sh",
        "wget | sh",
        "git reset --hard",
        "git clean -fd",
        "--yolo",
        "dangerously-skip-permissions",
    )
    for path in (root / "scripts").glob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in patterns:
            if pattern in text:
                errors.append(
                    {
                        "id": "SCRIPT_DANGEROUS_COMMAND",
                        "path": relative(path, root),
                        "message": pattern,
                    }
                )
    return errors


def validate_repo(root: Path, strict: bool = False):
    sections: dict[str, dict] = {}
    errors: list[dict] = []
    warnings: list[dict] = []
    missing = [path for path in REQUIRED_PATHS if not (root / path).exists()]
    errors.extend({"id": "REQUIRED_PATH_MISSING", "path": path} for path in missing)
    instructions = validate_instructions(root)
    skills = validate_skills(root)
    contracts = validate_contracts(root)
    upstreams = validate_upstreams(root)
    leakage = scan_leakage(root)
    secrets = scan_secrets(root)
    yaml_count, yaml_errors = _validate_yaml(root)
    sections.update(
        instructions=instructions,
        skills=skills,
        contracts=contracts,
        upstreams=upstreams,
        leakage=leakage,
        secrets=secrets,
    )
    for section in (instructions, skills, contracts, upstreams, leakage, secrets):
        errors.extend(section.get("errors", []))
        warnings.extend(section.get("warnings", []))
    errors.extend(yaml_errors)
    errors.extend(_validate_csv(root))
    errors.extend(_tracked_path_errors(root))
    errors.extend(_script_risks(root))
    try:
        current, _ = generate_status(root, check=True)
        if not current:
            errors.append({"id": "STATUS_REPORT_STALE", "path": "reports/current_state.md"})
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        errors.append({"id": "STATUS_REPORT_ERROR", "message": str(exc)})
    if strict and warnings:
        errors.extend(
            {"id": f"STRICT_{item['id']}", "message": item.get("message", "warning")}
            for item in warnings
        )
    return {
        "ok": not errors,
        "strict": strict,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "yaml_count": yaml_count,
        "errors": errors,
        "warnings": warnings,
        "sections": sections,
    }
