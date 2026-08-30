"""Validate the pinned upstream candidate manifest without executing candidates."""

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
    schema = __import__("json").loads(
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
    return {"candidate_count": len(candidates), "cache_ignored": ignored, "errors": errors}
