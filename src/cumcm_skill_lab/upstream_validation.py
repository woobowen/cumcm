"""Validate pinned upstream evidence and component cards without executing candidates."""

import json
import subprocess
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, ValidationError

from .constants import EXPECTED_CANDIDATES


def validate_upstreams(root: Path):
    errors: list[dict] = []
    manifest_path = root / "research/upstream_candidates/manifest.yaml"
    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        candidates = manifest["candidates"]
    except (OSError, yaml.YAMLError, KeyError, TypeError) as exc:
        return {
            "candidate_count": 0,
            "errors": [{"id": "UPSTREAM_MANIFEST_PARSE", "message": str(exc)}],
        }
    if len(candidates) != EXPECTED_CANDIDATES:
        errors.append(
            {
                "id": "UPSTREAM_COUNT",
                "message": f"expected {EXPECTED_CANDIDATES}, found {len(candidates)}",
            }
        )
    schema = json.loads(
        (root / "contracts/upstream_candidate.schema.json").read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(schema)
    seen: set[str] = set()
    for candidate in candidates:
        candidate_id = candidate.get("id", "UNKNOWN") if isinstance(candidate, dict) else "UNKNOWN"
        if candidate_id in seen:
            errors.append({"id": "UPSTREAM_DUPLICATE_ID", "message": candidate_id})
        seen.add(candidate_id)
        try:
            validator.validate(candidate)
        except ValidationError as exc:
            errors.append({"id": "UPSTREAM_SCHEMA", "message": f"{candidate_id}: {exc.message}"})
            continue
        if candidate["preliminary_reuse_mode"] != "EVALUATE":
            errors.append({"id": "UPSTREAM_PREMATURE_REUSE", "message": candidate_id})
        for evidence in candidate["evidence_paths"]:
            if evidence.startswith(".cache/") or not (root / evidence).exists():
                errors.append(
                    {"id": "UPSTREAM_EVIDENCE_PATH", "message": f"{candidate_id}: {evidence}"}
                )
    ignored = (
        subprocess.run(
            ["git", "check-ignore", "-q", ".cache/upstream"], cwd=root, check=False
        ).returncode
        == 0
    )
    tracked = subprocess.run(
        ["git", "ls-files", ".cache/upstream"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not ignored:
        errors.append({"id": "UPSTREAM_CACHE_NOT_IGNORED", "message": ".cache/upstream"})
    if tracked:
        errors.append({"id": "UPSTREAM_CACHE_TRACKED", "message": tracked})
    card_paths = sorted((root / "research/upstream_candidates/component_cards").glob("*.yaml"))
    if len(card_paths) > 5:
        errors.append({"id": "COMPONENT_CARD_LIMIT", "message": str(len(card_paths))})
    card_schema_path = root / "contracts/component_card.schema.json"
    if card_paths and not card_schema_path.is_file():
        errors.append({"id": "COMPONENT_CARD_SCHEMA_MISSING"})
    elif card_paths:
        card_validator = Draft202012Validator(
            json.loads(card_schema_path.read_text(encoding="utf-8"))
        )
        candidates_by_id = {candidate["id"]: candidate for candidate in candidates}
        for path in card_paths:
            try:
                card = yaml.safe_load(path.read_text(encoding="utf-8"))
                card_validator.validate(card)
            except (OSError, yaml.YAMLError, ValidationError) as exc:
                errors.append({"id": "COMPONENT_CARD_SCHEMA", "message": f"{path.name}: {exc}"})
                continue
            if path.stem != card["mechanism_id"]:
                errors.append({"id": "COMPONENT_CARD_FILENAME", "message": path.name})
            source = candidates_by_id.get(card["source_candidate"])
            if source is None or source["resolved_commit"] != card["source_commit"]:
                errors.append({"id": "COMPONENT_CARD_SOURCE_PIN", "message": card["mechanism_id"]})
            license_status = card["license_status"]
            if card["reuse_mode"] == "DIRECT_REUSE_CANDIDATE" and any(
                marker in license_status for marker in ("UNKNOWN", "RESTRICTED", "NO_LICENSE")
            ):
                errors.append(
                    {"id": "COMPONENT_CARD_DIRECT_REUSE_BLOCKED", "message": card["mechanism_id"]}
                )
    return {
        "candidate_count": len(candidates),
        "component_card_count": len(card_paths),
        "cache_ignored": ignored,
        "errors": errors,
    }
