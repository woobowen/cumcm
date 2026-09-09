"""Regression probes from native review; no simulated scientific acceptance is evidence."""

import importlib.util
import json

import pytest


@pytest.fixture
def adjudicator(repo_root):
    spec = importlib.util.spec_from_file_location(
        "wb_adjudication_tests", repo_root / "scripts/check_modular_workbench.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize(
    "text", ['{"status":"BLOCK","status":"PASS"}', '{"score":NaN}', '{"score":Infinity}']
)
def test_strict_parser_rejects_ambiguous_or_nonfinite_evidence(adjudicator, text):
    with pytest.raises(ValueError):
        adjudicator.strict_json(text)


def test_summary_labels_cannot_substitute_for_execution_records(adjudicator, tmp_path):
    path = tmp_path / adjudicator.BASE / "fake.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "derivation": "EXACT_JSON_WITH_PRIVATE_ARGV_PATH_REDACTION",
                "records": {
                    "case_state": {
                        "raw_sha256": "0" * 64,
                        "content": {
                            "state": "READY_FOR_PAPER_HANDOFF",
                            "skill_version": "0.2.0-competition-rc10",
                        },
                    },
                    "final_ledger": {
                        "raw_sha256": "0" * 64,
                        "content": {"status": "SUCCESS", "count": True, "max_count": 1},
                    },
                    "handoff": {
                        "raw_sha256": "0" * 64,
                        "content": {
                            "approved_by": ["MACHINE_TECHNICAL_GATES"],
                            "final_runs": ["MISSING"],
                        },
                    },
                    "capture:FAKE": {
                        "raw_sha256": "0" * 64,
                        "content": {"outcome": "SUCCESS", "run_id": None},
                    },
                },
            }
        )
    )
    binding = {
        "path": path.relative_to(tmp_path).as_posix(),
        "sha256": adjudicator.digest(path.read_bytes()),
    }
    with pytest.raises(ValueError, match="PROJECTION_UNDECLARED"):
        adjudicator.validate_family_evidence(tmp_path, {"record_packet": binding})


def test_exact_record_raw_bytes_must_reconstruct_content(adjudicator, tmp_path):
    path = tmp_path / adjudicator.BASE / "fake.json"
    path.parent.mkdir(parents=True)
    value = {
        "derivation": "EXACT_UTF8_JSON_NO_REDACTION",
        "records": {
            "record": {
                "raw_utf8": '{"status":"BLOCK"}',
                "raw_sha256": adjudicator.digest(b'{"status":"BLOCK"}'),
                "content": {"status": "PASS"},
            }
        },
    }
    path.write_text(json.dumps(value))
    binding = {
        "path": path.relative_to(tmp_path).as_posix(),
        "sha256": adjudicator.digest(path.read_bytes()),
    }
    with pytest.raises(ValueError, match="RAW_RECORD_IDENTITY_INVALID"):
        adjudicator.exact_records(tmp_path, binding)


def test_matrix_requires_actual_protocol_coverage(adjudicator):
    errors = adjudicator.validate_matrix(
        {
            "modules": [],
            "families": [{"kind": "mixed", "primary_requirements": 1}],
            "whole_known_problem_completed": False,
            "new_independent_validation": 0,
            "human_review": "NOT_RUN",
        }
    )
    assert {
        "WB_BOUNDARY_COVERAGE_INCOMPLETE",
        "WB_DEFAULT_EXPLICIT_EQUIVALENCE_INCOMPLETE",
        "WB_MIXED_PRIMARY_COVERAGE_INCOMPLETE",
    } <= set(errors)


@pytest.mark.parametrize(
    "name",
    [
        "native_review",
        "context_handoff",
        "known_interface",
        "review_roundtrip",
        "independent_recalculation",
    ],
)
def test_noncommand_receipt_requires_substantive_typed_detail(adjudicator, tmp_path, name):
    path = tmp_path / adjudicator.BASE / "empty.json"
    path.parent.mkdir(parents=True)
    path.write_text("{}")
    item = {
        "detail": {
            "path": path.relative_to(tmp_path).as_posix(),
            "sha256": adjudicator.digest(path.read_bytes()),
        }
    }
    with pytest.raises(ValueError, match="DETAIL_SCHEMA_INVALID"):
        adjudicator.validate_detail(tmp_path, name, item)


def test_read_and_binding_reject_symlinks(adjudicator, tmp_path):
    path = tmp_path / adjudicator.BASE / "fake.json"
    path.parent.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    outside.write_text("{}")
    path.symlink_to(outside)
    with pytest.raises(ValueError, match="UNSAFE_PATH"):
        adjudicator.read(tmp_path, path.relative_to(tmp_path).as_posix())


@pytest.mark.parametrize(
    "change",
    [
        {"exit_code": True},
        {"argv": []},
        {"elapsed_seconds": -1},
        {"ended_at": "2026-09-08T00:00:00Z"},
    ],
)
def test_command_records_reject_wrong_types_or_time(adjudicator, change):
    command = {
        "argv": ["ACTUAL_COMMAND"],
        "exit_code": 0,
        "started_at": "2026-09-09T00:00:00Z",
        "ended_at": "2026-09-09T00:00:01Z",
    }
    command.update(change)
    with pytest.raises(ValueError):
        adjudicator.actual_command(command)
