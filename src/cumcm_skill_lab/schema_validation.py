"""Validate JSON Schemas and positive/negative contract fixtures."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError

from .constants import SCHEMA_DRAFT
from .paths import relative


def validate_contracts(root: Path):
    errors: list[dict] = []
    schemas: dict[str, dict] = {}
    ids: list[str] = []
    for path in sorted((root / "contracts").glob("*.schema.json")):
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
        except (json.JSONDecodeError, ValueError) as exc:
            errors.append({"id": "SCHEMA_PARSE", "message": str(exc), "path": relative(path, root)})
            continue
        if schema.get("$schema") != SCHEMA_DRAFT:
            errors.append(
                {"id": "SCHEMA_DRAFT", "message": "unexpected draft", "path": relative(path, root)}
            )
        if not schema.get("version"):
            errors.append(
                {"id": "SCHEMA_VERSION", "message": "missing version", "path": relative(path, root)}
            )
        schema_id = schema.get("$id")
        if not schema_id:
            errors.append(
                {"id": "SCHEMA_ID", "message": "missing $id", "path": relative(path, root)}
            )
        else:
            ids.append(schema_id)
        schemas[path.name.removesuffix(".schema.json")] = schema
    if len(ids) != len(set(ids)):
        errors.append({"id": "SCHEMA_DUPLICATE_ID", "message": "$id values are not unique"})
    valid_count = 0
    valid_dir = root / "tests/fixtures/contracts/valid"
    for name, schema in schemas.items():
        fixture = valid_dir / f"{name}.json"
        if not fixture.is_file():
            errors.append({"id": "SCHEMA_VALID_FIXTURE_MISSING", "message": name})
            continue
        try:
            Draft202012Validator(schema).validate(json.loads(fixture.read_text(encoding="utf-8")))
            valid_count += 1
        except (json.JSONDecodeError, ValidationError) as exc:
            errors.append(
                {"id": "SCHEMA_VALID_FIXTURE", "message": str(exc), "path": relative(fixture, root)}
            )
    invalid_count = 0
    for fixture in sorted((root / "tests/fixtures/contracts/invalid").glob("*.json")):
        schema = schemas.get(fixture.stem)
        if schema is None:
            errors.append({"id": "SCHEMA_INVALID_FIXTURE_SCHEMA", "message": fixture.stem})
            continue
        try:
            Draft202012Validator(schema).validate(json.loads(fixture.read_text(encoding="utf-8")))
        except ValidationError:
            invalid_count += 1
        else:
            errors.append(
                {
                    "id": "SCHEMA_INVALID_ACCEPTED",
                    "message": "invalid fixture passed",
                    "path": relative(fixture, root),
                }
            )
    return {
        "schema_count": len(schemas),
        "valid_fixtures": valid_count,
        "invalid_rejected": invalid_count,
        "errors": errors,
    }
