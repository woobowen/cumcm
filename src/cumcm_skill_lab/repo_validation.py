"""Composite repository validation with stable finding identifiers."""

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

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

PRIVATE_PATH_PATTERNS = {
    "PRIVATE_UNIX_HOME_PATH": re.compile(r"(?<![A-Za-z0-9_<])/(?:home|Users)/[^/\s`]+/"),
    "PRIVATE_WINDOWS_HOME_PATH": re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s`]+\\"),
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


def scan_private_paths(root: Path):
    """Reject tracked-delivery text that exposes a user's home path."""
    errors: list[dict] = []
    for path in tracked_text_files(root):
        rel = relative(path, root)
        text = path.read_text(encoding="utf-8")
        for finding_id, pattern in PRIVATE_PATH_PATTERNS.items():
            if pattern.search(text):
                errors.append({"id": finding_id, "path": rel})
    return {"errors": errors}


def validate_delivery_policy(root: Path):
    """Validate the sole tracked remote truth and mandatory delivery rule."""
    rel = "rules/workflow_rules.yaml"
    path = root / rel
    errors: list[dict] = []
    if not path.is_file():
        return {"errors": [{"id": "GIT_DELIVERY_CONFIG_MISSING", "path": rel}]}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return {"errors": [{"id": "GIT_DELIVERY_CONFIG_INVALID", "path": rel, "message": str(exc)}]}
    delivery = data.get("git_delivery")
    required = {
        "remote_name": str,
        "repository": str,
        "remote_url": str,
        "protected_base_branch": str,
        "preferred_task_branch": str,
        "allow_force_push": bool,
        "allow_agent_merge": bool,
    }
    if not isinstance(delivery, dict):
        errors.append({"id": "GIT_DELIVERY_CONFIG_INVALID", "path": rel})
        return {"errors": errors}
    for key, expected_type in required.items():
        value = delivery.get(key)
        if not isinstance(value, expected_type) or isinstance(value, str) and not value:
            errors.append(
                {
                    "id": "GIT_DELIVERY_FIELD_INVALID",
                    "path": rel,
                    "message": key,
                }
            )
    if delivery.get("allow_force_push") is not False:
        errors.append({"id": "GIT_DELIVERY_FORCE_PUSH", "path": rel})
    if delivery.get("allow_agent_merge") is not False:
        errors.append({"id": "GIT_DELIVERY_AGENT_MERGE", "path": rel})

    remote_url = delivery.get("remote_url")
    if isinstance(remote_url, str) and remote_url:
        occurrences: list[dict] = []
        for candidate in tracked_text_files(root):
            count = candidate.read_text(encoding="utf-8").count(remote_url)
            if count:
                occurrences.append({"path": relative(candidate, root), "count": count})
        if occurrences != [{"path": rel, "count": 1}]:
            errors.append(
                {
                    "id": "GIT_DELIVERY_REMOTE_TRUTH_COUNT",
                    "path": rel,
                    "message": str(occurrences),
                }
            )

    rule = next(
        (
            item
            for item in data.get("rules", [])
            if isinstance(item, dict) and item.get("id") == "GIT-DELIVERY-001"
        ),
        None,
    )
    if not rule:
        errors.append({"id": "GIT_DELIVERY_RULE_MISSING", "path": rel})
    elif (
        rule.get("level") != "MUST"
        or rule.get("failure_severity") != "BLOCKER"
        or rule.get("status") != "ACTIVE"
        or (rule.get("enforcement") or {}).get("type") != "manual_and_git_verification"
    ):
        errors.append({"id": "GIT_DELIVERY_RULE_INVALID", "path": rel})
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


def _active_plan_errors(root: Path) -> list[dict]:
    """Bind the one active plan to formal state instead of a phase-specific path."""
    errors: list[dict] = []
    active_dir = root / "plans/active"
    active = sorted(active_dir.glob("*.md")) if active_dir.is_dir() else []
    if len(active) != 1:
        errors.append(
            {
                "id": "ACTIVE_PLAN_COUNT",
                "path": "plans/active",
                "message": f"expected 1, found {len(active)}",
            }
        )
        return errors
    state_path = root / "state/project_state.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append({"id": "PROJECT_STATE_INVALID", "message": str(exc)})
        return errors
    schema = json.loads((root / "contracts/project_state.schema.json").read_text(encoding="utf-8"))
    state_errors = sorted(
        Draft202012Validator(schema).iter_errors(state), key=lambda item: list(item.path)
    )
    errors.extend(
        {
            "id": "PROJECT_STATE_SCHEMA",
            "path": "state/project_state.json",
            "message": item.message,
        }
        for item in state_errors
    )
    content_commit = state.get("content_verified_commit")
    if content_commit:
        head_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        if head_result.returncode == 0 and content_commit == head_result.stdout.strip():
            errors.append(
                {
                    "id": "PROJECT_STATE_SELF_REFERENCE",
                    "path": "state/project_state.json",
                    "message": "content_verified_commit must name a prior content commit",
                }
            )
    manifest = state.get("verification_manifest")
    if manifest:
        manifest_path = root / manifest["path"]
        actual_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        if actual_hash != manifest["sha256"]:
            errors.append(
                {
                    "id": "VERIFICATION_MANIFEST_HASH",
                    "path": manifest["path"],
                    "message": actual_hash,
                }
            )
    receipt = state.get("delivery_receipt_for_commit")
    if receipt and (
        receipt["commit"] != content_commit or receipt["remote_sha"] != receipt["commit"]
    ):
        errors.append(
            {
                "id": "DELIVERY_RECEIPT_MISMATCH",
                "path": "state/project_state.json",
                "message": "receipt must bind the content-verified commit",
            }
        )
    current = active[0].relative_to(root).as_posix()
    if state.get("current_plan") != current:
        errors.append(
            {
                "id": "CURRENT_PLAN_MISMATCH",
                "path": current,
                "message": str(state.get("current_plan")),
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
    privacy = scan_private_paths(root)
    delivery = validate_delivery_policy(root)
    yaml_count, yaml_errors = _validate_yaml(root)
    sections.update(
        instructions=instructions,
        skills=skills,
        contracts=contracts,
        upstreams=upstreams,
        leakage=leakage,
        secrets=secrets,
        privacy=privacy,
        delivery=delivery,
    )
    for section in (
        instructions,
        skills,
        contracts,
        upstreams,
        leakage,
        secrets,
        privacy,
        delivery,
    ):
        errors.extend(section.get("errors", []))
        warnings.extend(section.get("warnings", []))
    errors.extend(yaml_errors)
    errors.extend(_validate_csv(root))
    errors.extend(_tracked_path_errors(root))
    errors.extend(_script_risks(root))
    errors.extend(_active_plan_errors(root))
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
