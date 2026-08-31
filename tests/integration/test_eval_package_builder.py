import json
import subprocess

import pytest
import yaml

from cumcm_skill_lab.eval.package_builder import ARM_SPECS, build_packages


@pytest.fixture
def package_project(repo_root, tmp_path):
    root = tmp_path / "project"
    (root / "research/upstream_candidates").mkdir(parents=True)
    candidates = []
    for spec in ARM_SPECS:
        if spec.candidate_id is None:
            continue
        repo = root / ".cache/upstream" / spec.candidate_id
        repo.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(
            ["git", "config", "user.email", "eval@example.invalid"], cwd=repo, check=True
        )
        subprocess.run(["git", "config", "user.name", "Eval Fixture"], cwd=repo, check=True)
        for path in spec.included_paths:
            target = repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("Synthetic mechanism source; no answer content.\n", encoding="utf-8")
        subprocess.run(["git", "add", *spec.included_paths], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "fixture"], cwd=repo, check=True)
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo, check=True, text=True, capture_output=True
        ).stdout.strip()
        license_status = (
            "UNKNOWN_NO_LICENSE" if spec.arm_id == "YUSHUI" else "MIT_ROOT_WITH_EXTERNAL_EXCLUSIONS"
        )
        candidates.append(
            {
                "id": spec.candidate_id,
                "resolved_commit": commit,
                "detected_license": license_status,
                "license_files": [] if spec.arm_id == "YUSHUI" else ["LICENSE"],
            }
        )
    (root / "research/upstream_candidates/manifest.yaml").write_text(
        yaml.safe_dump({"candidates": candidates}), encoding="utf-8"
    )
    return root


def test_build_packages_is_deterministic_and_cache_only(package_project):
    ok, mismatches, manifests = build_packages(package_project)
    assert not ok
    assert mismatches
    ok, mismatches, second = build_packages(package_project, check=True)
    assert ok
    assert mismatches == []
    assert manifests == second
    for manifest in second:
        assert manifest["status"] == "PACKAGE_SAFE"
    unknown = next(item for item in second if item["arm_id"] == "YUSHUI")
    assert unknown["candidate_id"] == "yushui-mathmodel-skill"
    license_record = json.loads(
        (package_project / ".cache/upstream-eval/packages/YUSHUI/license_status.json").read_text(
            encoding="utf-8"
        )
    )
    assert license_record["status"] == "UNKNOWN_NO_LICENSE"
    assert license_record["direct_adoption_eligible"] is False


def test_pinned_commit_mismatch_fails_closed(package_project):
    manifest_path = package_project / "research/upstream_candidates/manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["candidates"][0]["resolved_commit"] = "0" * 40
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    with pytest.raises(RuntimeError, match="PINNED_COMMIT_MISMATCH"):
        build_packages(package_project)
