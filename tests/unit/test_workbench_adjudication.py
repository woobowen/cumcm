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


@pytest.mark.parametrize("text", ['{"count":1e309}', '{"count":-1e309}'])
def test_numeric_overflow_is_not_finite_json(adjudicator, text):
    with pytest.raises(ValueError, match="NONFINITE"):
        adjudicator.strict_json(text)


@pytest.mark.parametrize(
    "fault",
    [
        "missing_requirement",
        "large_residual",
        "manifest_capture",
        "supporting_role",
        "final_before_model",
        "boolean_count",
    ],
)
def test_native_tampering_of_actual_captured_family_is_rejected(
    adjudicator, repo_root, tmp_path, fault
):
    source = repo_root / adjudicator.BASE / "development_exports/acceptance-001/mixed/records.json"
    packet = json.loads(source.read_text())
    records = packet["records"]

    def replace(key, value):
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True)
        records[key] = {
            "content": value,
            "raw_utf8": raw,
            "raw_sha256": adjudicator.digest(raw.encode()),
        }

    ledger = records["final_ledger"]["content"]
    if fault in {"missing_requirement", "large_residual"}:
        for rid in ledger["selected_run_ids"]:
            key = "final_check:" + rid
            value = records[key]["content"]
            if fault == "missing_requirement":
                del value["requirements"]["REQ-C"]
            else:
                value["requirements"]["REQ-C"]["recalculation_residuals"]["full_numeric_vector"][
                    "value"
                ] = 1e6
            replace(key, value)
            ledger["checks"][rid]["files"][f"runs/{rid}/final_check.json"] = records[key][
                "raw_sha256"
            ]
        replace("final_ledger", ledger)
    elif fault == "manifest_capture":
        handoff = records["handoff"]["content"]
        for run in handoff["final_runs"]:
            key = "manifest:" + run["run_id"]
            value = records[key]["content"]
            value["capture_record"]["sha256"] = "0" * 64
            replace(key, value)
            run["manifest_hash"] = adjudicator.canonical(value)
        replace("handoff", handoff)
    elif fault == "supporting_role":
        value = records["problem_requirements"]["content"]
        value["content"]["requirements"][2]["role"] = "SUPPORTING"
        value["content_hash"] = adjudicator.canonical(value["content"])
        replace("problem_requirements", value)
    elif fault == "final_before_model":
        for value in [ledger, *ledger["checks"].values()]:
            for key in ["started_at", "ended_at"]:
                value[key] = value[key].replace("2026-09-09", "2026-09-08")
        replace("final_ledger", ledger)
    else:
        value = dict(ledger, count=True)
        replace("final_ledger", value)
        records["final_ledger"]["content"] = dict(value, count=1)
    destination = tmp_path / adjudicator.BASE / "tampered.json"
    destination.parent.mkdir(parents=True)
    destination.write_text(json.dumps(packet))
    family = {
        "kind": "mixed",
        "primary_requirements": 3,
        "actual_model_starts": 2,
        "native_state": "READY_FOR_PAPER_HANDOFF",
        "case_id": "ORIGINAL-WATER-MIXED",
        "record_packet": {
            "path": destination.relative_to(tmp_path).as_posix(),
            "sha256": adjudicator.digest(destination.read_bytes()),
        },
    }
    if fault == "boolean_count":
        with pytest.raises(ValueError, match="RAW_RECORD_IDENTITY_INVALID"):
            adjudicator.validate_family_evidence(tmp_path, family)
    else:
        assert adjudicator.validate_family_evidence(tmp_path, family)


def test_actual_development_family_remains_replayable(adjudicator, repo_root):
    path = adjudicator.BASE + "/development_exports/acceptance-001/mixed/records.json"
    family = {
        "kind": "mixed",
        "primary_requirements": 3,
        "actual_model_starts": 2,
        "native_state": "READY_FOR_PAPER_HANDOFF",
        "case_id": "ORIGINAL-WATER-MIXED",
        "record_packet": {
            "path": path,
            "sha256": adjudicator.digest((repo_root / path).read_bytes()),
        },
    }
    assert adjudicator.validate_family_evidence(repo_root, family) == []
