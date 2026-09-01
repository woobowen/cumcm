"""Build cache-only sanitized instruction packages without executing upstream content."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .models import canonical_json, load_yaml, sha256_bytes, sha256_text
from .safety import inspect_source_entry, normalized_instruction_findings

BUILDER_VERSION = "1.0.0"


@dataclass(frozen=True)
class ArmSpec:
    arm_id: str
    candidate_id: str | None
    mode: str
    included_paths: tuple[str, ...]
    instruction: str


BASELINE_INSTRUCTION = """Evaluation arm policy:
- This is the no-project-level mathematical-modeling-Skill baseline.
- Follow only the common synthetic task, output Schema, and safety constraints provided in the run.
- Do not infer extra workflow requirements from this arm policy.
"""

HANDSOMEZR_INSTRUCTION = """Evaluation arm policy:
- Before modeling, trace each subtask's inputs, outputs, units, controllable decisions, parameters,
  reality constraints, evaluation criteria, and evidence-backed dependencies.
- Compare structurally distinct feasible candidate models against a simple baseline. Record fit,
  assumptions, implementation/time cost, rejection reasons, and conditions that would falsify the
  selection. Use a minimal executable sanity case before relying on a candidate.
- Work one subtask at a time through formalization, implementation, actual execution, validation,
  and evidence-justified sensitivity checks. Record issues and preserve rejected alternatives.
- Treat unresolved high-severity findings as blocking. Reopen the earliest affected subtask or model
  decision instead of allowing later prose or totals to hide the failure.
- Keep one append/supersede decision record and fail closed when required evidence is absent.
"""

YUSHUI_INSTRUCTION = """Evaluation arm policy:
- Start with a preflight that classifies each input's role and records a content hash. Do not
  advance when required inputs or prior-stage artifacts are absent.
- Persist a minimal recoverable workflow state containing current stage, completed prerequisites,
  structured handoff locations, and input/script/output hashes.
- On resume or before downstream use, recompute freshness hashes. Mark dependent artifacts STALE and
  restart at the earliest affected stage when an input, configuration, script, or output changed.
- Use structured JSON handoffs with explicit status and evidence fields between stages. A completed
  label without current hashes and required evidence is not an accepted result.
- Preserve history and fail closed at stage prerequisites; never repair validity by editing a
  report.
"""

ARM_SPECS = (
    ArmSpec("NO_PROJECT_MODELING_SKILL", None, "NEUTRAL_BASELINE", (), BASELINE_INSTRUCTION),
    ArmSpec(
        "HANDSOMEZR",
        "handsomezr-mathmodel-skill",
        "SANITIZED_INSTRUCTION_ONLY",
        (
            "references/stage_02_analysis.md",
            "references/stage_03_model_selection.md",
            "references/stage_05_subproblem_loop.md",
            "references/feedback_layer2_backtrack.md",
            "templates/shared/decision_log.json",
        ),
        HANDSOMEZR_INSTRUCTION,
    ),
    ArmSpec(
        "YUSHUI",
        "yushui-mathmodel-skill",
        "SANITIZED_INSTRUCTION_ONLY_WITH_LICENSE_BLOCKER",
        (
            "docs/workflow-contracts.md",
            "packages/codex/skills/context-memory-keeper/SKILL.md",
            "packages/codex/skills/paper-workflow-orchestrator/SKILL.md",
            "packages/codex/skills/quality-assurance-auditor/SKILL.md",
        ),
        YUSHUI_INSTRUCTION,
    ),
)


def _git(repo: Path, args: list[str], *, binary: bool = False):
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=not binary,
    )
    if result.returncode:
        error = result.stderr.decode(errors="replace") if binary else result.stderr
        raise RuntimeError(f"UPSTREAM_GIT_READ_FAILED: {' '.join(args)}: {error.strip()}")
    return result.stdout


def _tree(repo: Path, commit: str) -> dict[str, tuple[str, str]]:
    output = _git(repo, ["ls-tree", "-r", commit])
    entries: dict[str, tuple[str, str]] = {}
    for line in output.splitlines():
        metadata, path = line.split("\t", 1)
        mode, kind, object_id = metadata.split()
        if kind == "blob":
            entries[path] = (mode, object_id)
    return entries


def _blob(repo: Path, commit: str, path: str) -> bytes:
    return _git(repo, ["show", f"{commit}:{path}"], binary=True)


def _manifest_candidates(root: Path) -> dict[str, dict]:
    return {
        item["id"]: item
        for item in load_yaml(root / "research/upstream_candidates/manifest.yaml")["candidates"]
    }


def _exclusion_reason(path: str) -> str:
    lowered = path.lower()
    suffix = Path(path).suffix.lower()
    if lowered.startswith("examples/") or any(
        word in lowered for word in ("winning", "empirical", "phrase_bank", "distilled")
    ):
        return "CONTAMINATION_OR_RESULT_MATERIAL"
    if suffix in {".py", ".sh", ".js", ".ts"} or lowered.startswith(
        ("scripts/", "tests/", ".github/")
    ):
        return "CODE_SCRIPT_TEST_OR_AUTOMATION"
    if suffix in {".zip", ".docx", ".pdf", ".png", ".jpg", ".jpeg", ".svg"}:
        return "BINARY_ARCHIVE_DOCUMENT_OR_IMAGE"
    if any(word in lowered for word in ("paper", "writing", "latex", "submission")):
        return "PAPER_OR_SUBMISSION_SCOPE"
    if any(word in lowered for word in ("mcp", "install", "download", "harvester")):
        return "NETWORK_INSTALL_OR_EXTERNAL_TOOLING"
    return "NOT_IN_MINIMAL_ALLOWLIST"


def _package_files(root: Path, spec: ArmSpec) -> tuple[dict[str, bytes], dict]:
    candidates = _manifest_candidates(root)
    source_hashes: dict[str, str] = {}
    source_findings: list[dict] = []
    included_lines: list[str] = []
    excluded_lines: list[str] = []
    license_record: dict
    commit: str | None = None

    if spec.candidate_id is None:
        license_record = {
            "candidate_id": None,
            "status": "NOT_APPLICABLE",
            "direct_adoption_eligible": False,
        }
    else:
        candidate = candidates[spec.candidate_id]
        commit = candidate["resolved_commit"]
        repo = root / ".cache/upstream" / spec.candidate_id
        actual = _git(repo, ["rev-parse", "HEAD"]).strip()
        if actual != commit:
            raise RuntimeError(f"PINNED_COMMIT_MISMATCH: {spec.candidate_id}: {actual} != {commit}")
        tree = _tree(repo, commit)
        missing = sorted(set(spec.included_paths) - set(tree))
        if missing:
            raise RuntimeError(f"ALLOWLIST_PATH_MISSING: {spec.candidate_id}: {missing}")
        for path in sorted(tree):
            mode, _ = tree[path]
            if path in spec.included_paths:
                data = _blob(repo, commit, path)
                source_hashes[path] = sha256_bytes(data)
                findings = inspect_source_entry(path, mode, data)
                source_findings.extend(findings)
                included_lines.append(f"{path}\t{source_hashes[path]}\tCONSULTED_NOT_COPIED")
            else:
                excluded_lines.append(f"{path}\t{_exclusion_reason(path)}")
        detected = candidate["detected_license"]
        license_record = {
            "candidate_id": spec.candidate_id,
            "resolved_commit": commit,
            "status": detected,
            "license_files": candidate["license_files"],
            "direct_adoption_eligible": False,
            "fork_and_adapt_eligible": False
            if detected == "UNKNOWN_NO_LICENSE"
            else "NEEDS_HUMAN_REVIEW",
            "evaluation_only": True,
        }

    normalized = spec.instruction.strip() + "\n"
    normalized_findings = normalized_instruction_findings(normalized)
    blocking_source = [
        item
        for item in source_findings
        if item["id"]
        in {
            "SOURCE_EXTENSION_NOT_ALLOWED",
            "SOURCE_CODE_FORBIDDEN",
            "SOURCE_EXECUTABLE_FORBIDDEN",
            "SOURCE_BINARY_FORBIDDEN",
            "SOURCE_NOT_UTF8",
        }
    ]
    package_status = "PACKAGE_UNSAFE" if blocking_source or normalized_findings else "PACKAGE_SAFE"
    security = {
        "status": package_status,
        "raw_source_copied": False,
        "third_party_code_executed": False,
        "candidate_dependencies_installed": False,
        "source_findings": source_findings,
        "normalized_findings": normalized_findings,
        "blocking_findings": blocking_source + normalized_findings,
    }
    contamination = {
        "status": "PASS" if not normalized_findings else "FAIL",
        "source_findings_recorded": [
            item for item in source_findings if "DEMO" in item["id"] or "ANSWER" in item["id"]
        ],
        "normalized_findings": [
            item for item in normalized_findings if "DEMO" in item["id"] or "ANSWER" in item["id"]
        ],
        "separation": "SUCCESS" if not normalized_findings else "FAILED",
        "note": "Raw consulted blobs are hashed and scanned but never copied into the package.",
    }
    files: dict[str, bytes] = {
        "included_files.txt": (
            ("\n".join(included_lines) + "\n") if included_lines else "NONE\n"
        ).encode(),
        "excluded_files.txt": (
            ("\n".join(excluded_lines) + "\n") if excluded_lines else "NONE\n"
        ).encode(),
        "file_hashes.json": (json.dumps(source_hashes, sort_keys=True, indent=2) + "\n").encode(),
        "security_findings.json": (json.dumps(security, sort_keys=True, indent=2) + "\n").encode(),
        "license_status.json": (
            json.dumps(license_record, sort_keys=True, indent=2) + "\n"
        ).encode(),
        "contamination_scan.json": (
            json.dumps(contamination, sort_keys=True, indent=2) + "\n"
        ).encode(),
        "normalized_instruction.txt": normalized.encode(),
    }
    payload_hashes = {name: sha256_bytes(data) for name, data in sorted(files.items())}
    manifest = {
        "schema_version": "1.0.0",
        "builder_version": BUILDER_VERSION,
        "arm_id": spec.arm_id,
        "candidate_id": spec.candidate_id,
        "resolved_commit": commit,
        "evaluation_mode": spec.mode,
        "status": package_status,
        "source_files_are_copied": False,
        "payload_hashes": payload_hashes,
        "package_hash": sha256_text(canonical_json(payload_hashes)),
        "limitations": [
            "Tests only the normalized textual mechanism subset.",
            "Does not establish full upstream behavior, safety, correctness, or reuse rights.",
        ],
    }
    files["package_manifest.json"] = (
        json.dumps(manifest, sort_keys=True, indent=2) + "\n"
    ).encode()
    return files, manifest


def build_packages(root: Path, *, check: bool = False) -> tuple[bool, list[str], list[dict]]:
    mismatches: list[str] = []
    manifests: list[dict] = []
    package_root = root / ".cache/upstream-eval/packages"
    for spec in ARM_SPECS:
        files, manifest = _package_files(root, spec)
        manifests.append(manifest)
        for name, expected in files.items():
            path = package_root / spec.arm_id / name
            actual = path.read_bytes() if path.is_file() else None
            if actual != expected:
                mismatches.append(path.relative_to(root).as_posix())
                if not check:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(expected)
    return not mismatches, sorted(mismatches), manifests
