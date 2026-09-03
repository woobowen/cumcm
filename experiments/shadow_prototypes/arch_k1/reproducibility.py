"""Canonical hash-bound reproducibility kernel."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from typing import Any

from experiments.shadow_prototypes.common.interface import canonical_json, sha256_json

FIELDS = frozenset(
    {
        "run_id",
        "revision_id",
        "prior_manifest_hash",
        "current",
        "authority",
        "input_hash",
        "code_commit",
        "config_hash",
        "seed",
        "command",
        "cwd",
        "environment_hash",
        "dependency_hash",
        "output_hash",
        "outcome",
    }
)
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
PRIVATE_KEYS = frozenset(
    {
        "api_key",
        "access_token",
        "password",
        "credential",
        "client_secret",
        "secret",
        "browser_state",
        "hidden_reasoning",
        "raw_trace",
        "private_path",
    }
)
WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")


def _unsafe_path(value: Any) -> bool:
    return bool(
        isinstance(value, str)
        and (
            value.startswith(("/", "~"))
            or WINDOWS_ABSOLUTE.match(value)
            or ".." in value.replace("\\", "/").split("/")
        )
    )


def _private_paths(value: Any, prefix: str = "$") -> tuple[str, ...]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            path = f"{prefix}.{key}"
            if str(key).lower() in PRIVATE_KEYS:
                found.append(path)
            else:
                found.extend(_private_paths(item, path))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            found.extend(_private_paths(item, f"{prefix}[{index}]"))
    elif isinstance(value, str) and (_unsafe_path(value) or "credential=" in value):
        found.append(prefix)
    return tuple(sorted(set(found)))


def verified_run_record(
    record: Any, isolated_state: Mapping[str, Any], *, expected_run_id: str | None = None
) -> bool:
    if not isinstance(record, Mapping):
        return False
    run_id = record.get("run_id")
    hashes = isolated_state.get("trusted_manifest_hashes", {})
    return bool(
        isinstance(hashes, Mapping)
        and (expected_run_id is None or run_id == expected_run_id)
        and run_id in set(isolated_state.get("trusted_run_ids", ()))
        and record.get("decision_id")
        and record.get("authority") == "existing-native-run-ledger"
        and record.get("status") == "PASS"
        and record.get("current") is True
        and record.get("audited") is True
        and record.get("artifact_hash") == hashes.get(run_id)
    )


def evaluate_reproducibility(
    payload: Mapping[str, Any], isolated_state: Mapping[str, Any]
) -> tuple[bool, tuple[str, ...], dict[str, Any]]:
    reasons: list[str] = []
    manifest = payload.get("manifest")
    capture = payload.get("trusted_capture")
    private_paths = _private_paths(payload)
    if private_paths:
        reasons.append("K1_REPRO_PRIVATE_FIELD_REDACTED_AND_REJECTED")
    if not isinstance(manifest, Mapping) or not set(manifest) >= FIELDS:
        reasons.append("K1_REPRO_REQUIRED_BINDING_MISSING")
    else:
        hashes_valid = all(
            HEX64.fullmatch(str(manifest.get(field)))
            for field in (
                "input_hash",
                "config_hash",
                "environment_hash",
                "dependency_hash",
                "output_hash",
            )
        ) and bool(HEX40.fullmatch(str(manifest.get("code_commit"))))
        if not hashes_valid:
            reasons.append("K1_REPRO_HASH_FORMAT_INVALID")
        if manifest.get("run_id") not in set(isolated_state.get("trusted_run_ids", ())):
            reasons.append("K1_REPRO_REGISTERED_RUN_REQUIRED")
        trusted_manifests = isolated_state.get("trusted_repro_manifest_hashes", {})
        if not isinstance(trusted_manifests, Mapping) or sha256_json(
            manifest
        ) != trusted_manifests.get(manifest.get("run_id")):
            reasons.append("K1_REPRO_NATIVE_MANIFEST_BINDING_INVALID")
        if (
            not manifest.get("revision_id")
            or manifest.get("prior_manifest_hash") is None
            or not HEX64.fullmatch(str(manifest.get("prior_manifest_hash")))
            or manifest.get("current") is not True
            or manifest.get("authority") != "existing-native-run-ledger"
        ):
            reasons.append("K1_REPRO_REVISION_OR_AUTHORITY_INVALID")
        command = manifest.get("command")
        if (
            not isinstance(command, (list, tuple))
            or not command
            or not all(isinstance(item, str) and item for item in command)
        ):
            reasons.append("K1_REPRO_ARGV_INVALID")
        elif command[0].lower() in {
            "sh",
            "bash",
            "zsh",
            "cmd",
            "cmd.exe",
            "powershell",
            "pwsh",
        } or any(item in {"-c", "/c", "-command"} for item in command[1:]):
            reasons.append("K1_REPRO_SHELL_ONLY_ARGV_REJECTED")
        elif any(_unsafe_path(item) for item in command):
            reasons.append("K1_REPRO_COMMAND_PATH_REJECTED")
        cwd = manifest.get("cwd")
        if not isinstance(cwd, str) or _unsafe_path(cwd):
            reasons.append("K1_REPRO_CWD_INVALID")
    if not isinstance(capture, Mapping):
        reasons.append("K1_REPRO_TRUSTED_CAPTURE_MISSING")
    elif isinstance(manifest, Mapping):
        trusted_captures = isolated_state.get("trusted_capture_hashes", {})
        if not isinstance(trusted_captures, Mapping) or sha256_json(
            capture
        ) != trusted_captures.get(manifest.get("run_id")):
            reasons.append("K1_REPRO_TRUSTED_CAPTURE_BINDING_INVALID")
        computed = {
            "run_id": capture.get("run_id"),
            "revision_id": capture.get("revision_id"),
            "prior_manifest_hash": capture.get("prior_manifest_hash"),
            "current": capture.get("current"),
            "authority": capture.get("authority"),
            "input_hash": sha256_json(capture.get("input_content")),
            "code_commit": capture.get("code_commit"),
            "config_hash": sha256_json(capture.get("config_content")),
            "seed": capture.get("seed"),
            "command": capture.get("command"),
            "cwd": capture.get("cwd"),
            "environment_hash": sha256_json(capture.get("environment")),
            "dependency_hash": sha256_json(capture.get("dependencies")),
            "output_hash": sha256_json(capture.get("output_content")),
            "outcome": capture.get("outcome"),
        }
        if canonical_json(manifest) != canonical_json(computed):
            reasons.append("K1_REPRO_MUTATION_OR_BINDING_MISMATCH")
        seed = capture.get("seed")
        if (
            isinstance(seed, bool)
            or not isinstance(seed, (int, float))
            or not math.isfinite(float(seed))
        ):
            reasons.append("K1_REPRO_AMBIGUOUS_SEED_REJECTED")
    outcome = manifest.get("outcome") if isinstance(manifest, Mapping) else None
    if outcome not in {"SUCCESS", "FAILED", "PARTIAL", "SUPERSEDED"}:
        reasons.append("K1_REPRO_OUTCOME_INVALID")
    elif outcome != "SUCCESS":
        reasons.append(f"K1_REPRO_TERMINAL_NON_SUCCESS_RETAINED:{outcome}")
    return (
        not reasons,
        tuple(sorted(set(reasons))),
        {
            "canonical_manifest_hash": sha256_json(manifest)
            if isinstance(manifest, Mapping)
            else None,
            "private_fields_redacted": len(private_paths),
            "retained_outcome": outcome,
        },
    )


__all__ = ["evaluate_reproducibility", "verified_run_record"]
