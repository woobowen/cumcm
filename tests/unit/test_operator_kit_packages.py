"""Operator archives are descriptive, complete, inert and identity-separated."""

import importlib.util
import json
import zipfile
from pathlib import Path

import pytest


@pytest.fixture
def kit():
    path = (
        Path(__file__).resolve().parents[2]
        / "docs/gpt_codex_workflow/tools/package_operator_kit.py"
    )
    spec = importlib.util.spec_from_file_location("operator_packages", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rewrite(path, files):
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)


def members(path):
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def test_no_case_cannot_inherit_example_or_execution_authority(kit, tmp_path):
    path = tmp_path / "start.zip"
    receipt = kit.build("NO_CASE", path)
    assert receipt["kind"] == "NO_CASE"
    files = members(path)
    snapshot = json.loads(files["STARTUP_SNAPSHOT.json"])
    assert snapshot["active_case"] is None and snapshot["active_module"] is None
    assert not snapshot["model_or_final_execution_authorized"]
    assert not any("context.json" in name for name in files)
    snapshot["active_case"] = "COMPLETED-EXAMPLE"
    files["STARTUP_SNAPSHOT.json"] = kit.canonical(snapshot)
    manifest = json.loads(files["PACKAGE_MANIFEST.json"])
    manifest["files"]["STARTUP_SNAPSHOT.json"] = kit.digest(files["STARTUP_SNAPSHOT.json"])
    manifest["payload_set_sha256"] = kit.digest(kit.canonical(manifest["files"]))
    files["PACKAGE_MANIFEST.json"] = kit.canonical(manifest)
    rewrite(path, files)
    with pytest.raises(ValueError, match="NO_CASE_ISOLATION_FAILED"):
        kit.verify(path)


@pytest.mark.parametrize("mutation", ["missing", "tampered", "unexpected"])
def test_archive_incomplete_or_changed_payload_fails_closed(kit, tmp_path, mutation):
    path = tmp_path / "start.zip"
    kit.build("NO_CASE", path)
    files = members(path)
    if mutation == "missing":
        del files["BRAIN_START.md"]
    elif mutation == "tampered":
        files["BRAIN_START.md"] += b"\nChanged instructions"
    else:
        files["extra.txt"] = b"unregistered"
    rewrite(path, files)
    with pytest.raises(ValueError, match="PACKAGE_(MEMBER_SET|CONTENT_HASH)_MISMATCH"):
        kit.verify(path)


def test_example_and_next_preserve_original_inner_identity(kit, tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    payload = b'{"case_id":"ORIGINAL-ONLY","package_hash":"unchanged"}\n'
    (source / "manifest.json").write_bytes(payload)
    for kind, prefix in [("EXAMPLE_ONLY", "example"), ("NEXT_WEB", "review")]:
        path = tmp_path / (kind + ".zip")
        kit.build(kind, path, source)
        files = members(path)
        assert files[prefix + "/manifest.json"] == payload
        assert "STARTUP_SNAPSHOT.json" not in files
        with pytest.raises(ValueError, match="OUTPUT_ALREADY_EXISTS"):
            kit.build(kind, path, source)


def test_symlink_source_rejected_without_copying_outside(kit, tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("outside source scope")
    (source / "link.txt").symlink_to(outside)
    with pytest.raises(ValueError, match="SOURCE_SYMLINK_REJECTED"):
        kit.build("EXAMPLE_ONLY", tmp_path / "pack.zip", source)


@pytest.mark.parametrize("name", ["../escape", "/absolute", "C:/escape", "a\\b", "./x"])
def test_unsafe_zip_member_paths_rejected(kit, name):
    with pytest.raises(ValueError, match="UNSAFE_PACKAGE_PATH"):
        kit.check_name(name)
