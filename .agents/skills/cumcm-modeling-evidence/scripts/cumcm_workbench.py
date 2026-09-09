#!/usr/bin/env python3
"""单模块本地工作台。prepare不是求解；所有科学接受仍由cumcm_case/controller执行。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import cumcm_case as core

CATALOG = core.SKILL_ROOT / "references/modules.json"
REQUESTS = "evidence/module_requests"
POLICY = "state/case_policy.json"
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,95}\Z")


def safe_path(root, relative, *, must_exist=True):
    if (
        not isinstance(relative, str)
        or relative != Path(relative).as_posix()
        or "\\" in relative
        or any(part.startswith(".") for part in Path(relative).parts)
        or any(
            part.lower() in {"secrets", "credentials", "benchmark-vault"}
            for part in Path(relative).parts
        )
    ):
        raise ValueError("WB_UNSAFE_PATH")
    path = core.relative_case_path(root, relative)
    if path is None:
        raise ValueError("WB_UNSAFE_PATH")
    for index in range(1, len(Path(relative).parts) + 1):
        if root.joinpath(*Path(relative).parts[:index]).is_symlink():
            raise ValueError("WB_SYMLINK_REJECTED")
    if must_exist and not path.is_file():
        raise ValueError("WB_ARTIFACT_MISSING:" + relative)
    return path


def catalog():
    return {m["id"]: m for m in core.load_json(CATALOG)["modules"]}


def module(mid):
    if mid not in catalog():
        raise ValueError("WB_UNKNOWN_MODULE")
    return catalog()[mid]


def identity():
    roots = [
        core.SKILL_ROOT,
        core.REPO_ROOT / "contracts",
        core.REPO_ROOT / "rules",
        core.REPO_ROOT / "docs/modular_workbench",
    ]
    paths = [
        p
        for root in roots
        for p in root.rglob("*")
        if p.is_file() and p.suffix in {".py", ".md", ".json", ".yaml"}
    ]
    paths += [
        core.REPO_ROOT / "scripts/finalize_fresh_c_validation.py",
        core.REPO_ROOT / "pyproject.toml",
    ]
    mapping = {p.relative_to(core.REPO_ROOT).as_posix(): core.file_hash(p) for p in sorted(paths)}
    return {
        "tool_commit": core.current_git_commit(),
        "implementation_sha256": core.canonical_hash(mapping),
    }


def policy(root):
    state = core.load_state(root)
    path = safe_path(root, POLICY)
    value = core.load_json(path)
    if (
        value.get("schema_version") != "case-policy/v1"
        or value.get("case_id") != state["case_id"]
        or value.get("mode") not in {"GUIDED_LOCAL", "LAB_EVAL"}
        or state["evidence_bindings"].get(POLICY) != core.file_hash(path)
    ):
        raise ValueError("WB_CASE_POLICY_IDENTITY_INVALID")
    return value


def initialize(root, case_id, kind, mode):
    if case_id.startswith("CUMCM-"):
        raise ValueError("WB_HISTORICAL_CASE_REQUIRES_REGISTERED_NEW_CHILD")
    if mode == "LAB_EVAL":
        raise ValueError("WB_LAB_INIT_REQUIRES_EXISTING_REGISTERED_PROTOCOL")
    if root.resolve().is_relative_to(core.REPO_ROOT.resolve()):
        raise ValueError("WB_CASE_WORKSPACE_MUST_BE_SEPARATE")
    # The caller already acquired the public writer lock.
    if (
        root.exists()
        and any(root.iterdir())
        and {p.name for p in root.iterdir()} != {".case-writer.lock"}
    ):
        raise ValueError("WB_EXISTING_CASE_REQUIRES_RESUME")
    state = core.initialize_case(root, case_id, kind)
    value = {
        "schema_version": "case-policy/v1",
        "case_id": case_id,
        "mode": mode,
        "revision": 1,
        "execution_mode": "GUIDED_SINGLE_MODULE",
        "created_at": core.utc_now(),
        "automatic_publication": False,
        "team_compliance_review": "NOT_RUN",
        "research_policy": "USER_AUTHORIZED_GENERAL_SOURCES_ONLY",
    }
    core.write_json(root / POLICY, value, overwrite=False)
    state["evidence_bindings"][POLICY] = core.file_hash(root / POLICY)
    state["history"][0]["evidence"].append(POLICY)
    core.write_json(core.state_path(root), state)
    return {"status": "INITIALIZED", "case_id": case_id, "mode": mode, "model_starts": 0}


def scope_ids(root, value):
    content = core.load_json(root / core.ARTIFACT_PATHS["problem_requirements"]).get("content", {})
    known = sorted(
        r["requirement_id"]
        for r in content.get("requirements", [])
        if isinstance(r, dict) and isinstance(r.get("requirement_id"), str)
    )
    if value == "ALL":
        return known or ["ALL"]
    ids = value.split(",")
    if (
        len(set(ids)) != len(ids)
        or any(not ID.fullmatch(item) for item in ids)
        or not set(ids) <= set(known)
    ):
        raise ValueError("WB_REQUIREMENT_SCOPE_INVALID")
    return sorted(ids)


def request_records(root):
    records = [core.load_json(p) for p in sorted((root / REQUESTS).glob("*/request.json"))]
    for record in records:
        validate_request_identity(root, record)
    return records


def validate_request_identity(root, request):
    pol = policy(root)
    rid = request.get("request_id", "")
    if not isinstance(rid, str) or not ID.fullmatch(rid):
        raise ValueError("WB_REQUEST_ID_INVALID")
    relative = f"{REQUESTS}/{rid}/request.json"
    if (
        request.get("case_id") != pol["case_id"]
        or request.get("module") not in catalog()
        or request.get("mode") != pol["mode"]
        or request.get("execution_mode") != "GUIDED_SINGLE_MODULE"
        or type(request.get("revision")) is not int
        or request["revision"] != pol["revision"]
        or core.load_state(root)["evidence_bindings"].get(relative)
        != core.file_hash(safe_path(root, relative))
    ):
        raise ValueError("WB_REQUEST_IDENTITY_INVALID")


def bind_record(root, relative):
    state = core.load_state(root)
    state["evidence_bindings"][relative] = core.file_hash(safe_path(root, relative))
    core.write_json(core.state_path(root), state)


def bound_current(root, bindings):
    return all(
        safe_path(root, path, must_exist=False).is_file() and core.file_hash(root / path) == digest
        for path, digest in bindings.items()
    )


def receipt(root, request):
    path = root / REQUESTS / request["request_id"] / "completion.json"
    if not path.exists():
        return None
    value = core.load_json(path)
    if (
        value.get("request_sha256") != core.canonical_hash(request)
        or any(value.get(k) != request[k] for k in ["case_id", "module", "request_id"])
        or value.get("requirement_scope") != request["requirement_scope"]
        or not value.get("artifact_hashes")
        or core.load_state(root)["evidence_bindings"].get(path.relative_to(root).as_posix())
        != core.file_hash(path)
    ):
        raise ValueError("WB_RECEIPT_REQUEST_MISMATCH")
    return value


def request_status(root, request):
    validate_request_identity(root, request)
    if request["implementation"]["implementation_sha256"] != identity()["implementation_sha256"]:
        return "STALE_IMPLEMENTATION"
    if not bound_current(root, request["prerequisite_files"]):
        return "STALE_PREREQUISITE"
    done = receipt(root, request)
    if done:
        return "COMPLETED" if bound_current(root, done["artifact_hashes"]) else "STALE_OUTPUT"
    return "PREPARED"


def prepare(root, mid, scope, request_id=None):
    card = module(mid)
    pol = policy(root)
    ids = ["ALL"] if mid in {"M01", "M02"} and scope == "ALL" else scope_ids(root, scope)
    prerequisites = {POLICY: core.file_hash(root / POLICY)}
    for previous in card["prerequisites"]:
        eligible = [
            r
            for r in request_records(root)
            if r["module"] == previous
            and (r["requirement_scope"] == ids or r["requirement_scope"] == ["ALL"])
            and request_status(root, r) == "COMPLETED"
        ]
        if len(eligible) != 1:
            raise ValueError("WB_PREREQUISITE_MISSING_OR_STALE:" + previous)
        done = receipt(root, eligible[0])
        prerequisites.update(eligible[0]["prerequisite_files"])
        prerequisites.update(done["artifact_hashes"])
        req_relative = f"{REQUESTS}/{eligible[0]['request_id']}/request.json"
        prerequisites[req_relative] = core.file_hash(root / req_relative)
        rel = f"{REQUESTS}/{eligible[0]['request_id']}/completion.json"
        prerequisites[rel] = core.file_hash(root / rel)
    # Runtime plans are a fixed scope. Independent subquestions require an explicit
    # new scoped child; a narrow request cannot execute a whole-question plan.
    known = scope_ids(root, "ALL")
    if mid >= "M08" and ids != known:
        raise ValueError("WB_RUNTIME_SCOPE_CONFLICT_USE_SCOPED_CHILD")
    body = {
        "schema_version": "module-request/v1",
        "case_id": pol["case_id"],
        "module": mid,
        "requirement_scope": ids,
        "revision": pol["revision"],
        "mode": pol["mode"],
        "execution_mode": "GUIDED_SINGLE_MODULE",
        "implementation": identity(),
        "prerequisite_files": prerequisites,
    }
    rid = request_id or "REQ-" + core.canonical_hash(body)[:20]
    if not ID.fullmatch(rid):
        raise ValueError("WB_REQUEST_ID_INVALID")
    target = root / REQUESTS / rid / "request.json"
    if target.exists():
        existing = core.load_json(target)
        if any(existing.get(k) != v for k, v in body.items()):
            raise ValueError("WB_REQUEST_ID_CONFLICT")
        return {"status": request_status(root, existing), "request": existing}
    active = [r for r in request_records(root) if request_status(root, r) == "PREPARED"]
    if active:
        raise ValueError("WB_UNFINISHED_REQUEST_REQUIRES_RESUME")
    request = {**body, "request_id": rid, "prepared_at": core.utc_now()}
    core.write_json(target, request, overwrite=False)
    bind_record(root, target.relative_to(root).as_posix())
    prompt = (
        f"仅执行 {pol['case_id']} 的 {mid}（{card['name']}），范围 {','.join(ids)}。\n"
        f"{card['action']}。\n最少输入：{card['minimum_input']}。\n{card['stop']}\n"
        "准备接口没有完成分析。将真实动作、检查和负结果写入work report。"
    )
    (target.parent / "TASK.md").write_text(prompt + "\n", encoding="utf-8")
    core.write_json(
        target.parent / "work-report.template.json",
        {
            "case_id": pol["case_id"],
            "module": mid,
            "request_id": rid,
            "revision": pol["revision"],
            "requirement_scope": ids,
            "summary_cn": "",
            "original_requirements": [],
            "actions": [],
            "artifacts": [],
            "checks": [],
            "negative_results": [],
            "review_questions": [],
            "scientific_scope": "",
            "human_review": "NOT_RUN",
        },
        overwrite=False,
    )
    return {"status": "PREPARED", "request": request, "task": prompt, "analysis_completed": False}


def find_request(root, rid):
    if not ID.fullmatch(rid):
        raise ValueError("WB_REQUEST_ID_INVALID")
    request = core.load_json(safe_path(root, f"{REQUESTS}/{rid}/request.json"))
    validate_request_identity(root, request)
    if request.get("case_id") != policy(root)["case_id"] or request.get("request_id") != rid:
        raise ValueError("WB_REQUEST_IDENTITY_INVALID")
    if request_status(root, request).startswith("STALE"):
        raise ValueError("WB_REQUEST_STALE")
    return request


def controller():
    path = core.REPO_ROOT / "scripts/finalize_fresh_c_validation.py"
    spec = importlib.util.spec_from_file_location("workbench_common_controller", path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def run_operation(
    root, rid, operation, *, candidate=None, seed=None, run_id=None, code=None, timeout=600
):
    request = find_request(root, rid)
    if receipt(root, request):
        raise ValueError("WB_MODULE_ALREADY_COMPLETED")
    mid = request["module"]
    if (operation in {"model", "checker"} and mid != "M09") or (
        operation == "controller" and mid not in {"M10", "M11", "M12", "M13", "M14"}
    ):
        raise ValueError("WB_OPERATION_OUTSIDE_MODULE")
    args = {
        "operation": operation,
        "candidate": candidate,
        "seed": seed,
        "run_id": run_id,
        "code": code,
        "timeout": timeout,
    }
    key = core.canonical_hash(args)[:20]
    path = root / REQUESTS / rid / "operations" / (key + ".json")
    if path.exists():
        prior = core.load_json(path)
        if prior["status"] == "COMPLETED":
            return {**prior, "reused": True}
        raise ValueError("WB_OPERATION_STARTED_OR_FAILED_REQUIRES_RECOVERY")
    value = {
        "request_id": rid,
        "arguments": args,
        "started_at": core.utc_now(),
        "status": "RUNNING",
    }
    core.write_json(path, value, overwrite=False)
    try:
        if operation == "model":
            if core.load_state(root)["state"] == "EXPERIMENT_PLAN_VALIDATED":
                core.advance_once(root)
            result = core.execute_case_code(
                root,
                run_id=run_id,
                candidate_id=candidate,
                seed=seed,
                code_path=code,
                timeout_seconds=timeout,
            )
        elif operation == "checker":
            result = core.execute_scientific_check(
                root, run_id=run_id, code_path=code, timeout_seconds=timeout
            )
        else:
            result = controller().module_step(root, mid)
        if isinstance(result, dict) and result.get("status") in {
            "BLOCK",
            "REJECTED",
            "FAILED",
            "BLOCK_NATIVE_CONTRACTS",
        }:
            raise ValueError("WB_CORE_REJECTED:" + str(result.get("reason_codes", result)))
        value.update(status="COMPLETED", result=result)
    except Exception as exc:
        value.update(status="FAILED", reason=str(exc))
        raise
    finally:
        value["ended_at"] = core.utc_now()
        core.write_json(path, value)
    return value


def complete_module(root, rid, report_path):
    request = find_request(root, rid)
    existing = receipt(root, request)
    if existing:
        return existing
    mid = request["module"]
    card = module(mid)
    report = core.load_json(safe_path(root, report_path))
    required = {
        "case_id",
        "module",
        "request_id",
        "revision",
        "requirement_scope",
        "summary_cn",
        "original_requirements",
        "actions",
        "artifacts",
        "checks",
        "negative_results",
        "review_questions",
        "scientific_scope",
        "human_review",
    }
    if (
        not isinstance(report, dict)
        or set(report) != required
        or report.get("case_id") != request["case_id"]
        or report.get("module") != mid
        or any(report.get(k) != request[k] for k in ["request_id", "revision", "requirement_scope"])
        or type(report.get("revision")) is not int
    ):
        raise ValueError("WB_WORK_REPORT_IDENTITY_INVALID")
    if report["human_review"] != "NOT_RUN":
        raise ValueError("WB_HUMAN_REVIEW_REQUIRES_SEPARATE_ACTUAL_RECEIPT")
    if any(
        not isinstance(report[k], list) or not report[k]
        for k in [
            "original_requirements",
            "actions",
            "artifacts",
            "checks",
            "negative_results",
            "review_questions",
        ]
    ):
        raise ValueError("WB_WORK_REPORT_INCOMPLETE")
    if any(
        not isinstance(report[k], str) or not report[k].strip()
        for k in ["summary_cn", "scientific_scope"]
    ):
        raise ValueError("WB_WORK_REPORT_INCOMPLETE")
    files = {path: core.file_hash(safe_path(root, path)) for path in report["artifacts"]}
    files[report_path] = core.file_hash(root / report_path)
    for key in card["artifacts"]:
        relative = core.ARTIFACT_PATHS[key]
        if key == "modeling_to_paper_handoff":
            core.load_json(safe_path(root, relative))
        else:
            core.read_artifact(root, key)
        files[relative] = core.file_hash(root / relative)
    if mid == "M01":
        originals = [p for p in report["artifacts"] if p.startswith(("problem/", "data/raw/"))]
        if not originals:
            raise ValueError("WB_ORIGINAL_INPUTS_REQUIRED")
        core.write_json(
            root / "evidence/intake_registry.json",
            {"original_hashes": {p: files[p] for p in originals}, "observed_at": core.utc_now()},
            overwrite=False,
        )
        files["evidence/intake_registry.json"] = core.file_hash(
            root / "evidence/intake_registry.json"
        )
    if mid in {"M04", "M07"} and not any(p.startswith("models/") for p in files):
        raise ValueError("WB_MODEL_ANALYSIS_OR_CODE_REQUIRED")
    if mid == "M09":
        plan = core.read_artifact(root, "experiment_plan")["content"]
        captures = sorted(root.glob("runs/*/execution_capture.json"))
        expected = {(c, s) for c in plan["candidate_ids"] for s in plan["random_seeds"]}
        observed = set()
        for path in captures:
            capture = core.load_json(path)
            core.verify_current_capture_files(root, capture)
            pair = (capture["candidate_id"], capture["seed"])
            if pair in observed:
                raise ValueError("WB_DUPLICATE_ACTUAL_ATTEMPT")
            observed.add(pair)
            files[path.relative_to(root).as_posix()] = core.file_hash(path)
            files[capture["output"]["path"]] = core.file_hash(root / capture["output"]["path"])
        if observed != expected:
            raise ValueError("WB_EXECUTION_INCOMPLETE")
    if mid >= "M10":
        ops = [core.load_json(p) for p in (root / REQUESTS / rid / "operations").glob("*.json")]
        if not any(
            op["arguments"]["operation"] == "controller" and op["status"] == "COMPLETED"
            for op in ops
        ):
            raise ValueError("WB_ACTUAL_CONTROLLER_OPERATION_REQUIRED")
    elif card["native_target"]:
        target = card["native_target"]
        current = core.load_state(root)["state"]
        if current not in core.STATES or core.STATES.index(current) > core.STATES.index(target):
            raise ValueError("WB_NATIVE_STATE_OUTSIDE_MODULE")
        while core.load_state(root)["state"] != target:
            core.advance_once(root)
    if card["native_target"] and core.load_state(root)["state"] != card["native_target"]:
        raise ValueError("WB_NATIVE_TARGET_NOT_REACHED")
    result = {
        "schema_version": "module-completion/v1",
        "case_id": request["case_id"],
        "module": mid,
        "request_id": rid,
        "request_sha256": core.canonical_hash(request),
        "completed_at": core.utc_now(),
        "requirement_scope": request["requirement_scope"],
        "artifact_hashes": files,
        "report_path": report_path,
        "execution": "COMPLETED",
        "engineering": "CONTRACTS_CHECKED",
        "scientific": report["scientific_scope"],
        "human_review": "NOT_RUN",
        "native_state": core.load_state(root)["state"],
        "next_module_started": False,
    }
    core.write_json(root / REQUESTS / rid / "completion.json", result, overwrite=False)
    bind_record(root, f"{REQUESTS}/{rid}/completion.json")
    return result


def status(root):
    return {
        "case_id": policy(root)["case_id"],
        "policy": policy(root),
        "native_state": core.load_state(root),
        "modules": [
            {
                "request_id": r["request_id"],
                "module": r["module"],
                "scope": r["requirement_scope"],
                "status": request_status(root, r),
            }
            for r in request_records(root)
        ],
        "human_review": "NOT_RUN",
        "implementation": identity(),
    }


def derive_case(root, destination, case_id, scope, *, revision=False):
    """Copy immutable intake only; never carry accepted states, Runs or budgets."""
    parent = policy(root)
    if parent["mode"] != "GUIDED_LOCAL":
        raise ValueError("WB_LAB_REVISION_REQUIRES_REGISTERED_PROTOCOL")
    if destination == root or destination.is_relative_to(root):
        raise ValueError("WB_CHILD_ROOT_MUST_BE_SEPARATE")
    ids = scope_ids(root, scope)
    requirements = core.read_artifact(root, "problem_requirements")["content"]
    selected = [r for r in requirements["requirements"] if r["requirement_id"] in ids]
    if any(set(r.get("dependency_requirements", [])) - set(ids) for r in selected):
        raise ValueError("WB_SCOPED_CHILD_DEPENDENCY_MISSING")
    intake = core.load_json(safe_path(root, "evidence/intake_registry.json"))
    files = intake["original_hashes"]
    if not bound_current(root, files):
        raise ValueError("WB_ORIGINAL_CHANGED_RESTORE_OR_REGISTER_NEW_INPUT")
    origin = {
        "parent_case_id": parent["case_id"],
        "parent_revision": parent["revision"],
        "parent_policy_sha256": core.file_hash(root / POLICY),
        "parent_requirements_sha256": core.file_hash(
            root / core.ARTIFACT_PATHS["problem_requirements"]
        ),
        "requirement_scope": ids,
        "all_parent_requirements": scope_ids(root, "ALL"),
        "original_hashes": files,
        "reason": "REVISION" if revision else "SCOPED_CHILD",
        "parent_completion_inherited": False,
    }
    with core.case_writer(destination):
        if (destination / "evidence/parent_origin.json").exists():
            existing = core.load_json(destination / "evidence/parent_origin.json")
            if existing != origin or policy(destination)["case_id"] != case_id:
                raise ValueError("WB_CHILD_IDENTITY_CONFLICT")
            return {"status": "EXISTING_CHILD", "case_id": case_id, "model_starts": 0}
        initialize(destination, case_id, core.load_state(root)["case_kind"], "GUIDED_LOCAL")
        child_policy = policy(destination)
        child_policy["revision"] = parent["revision"] + 1 if revision else 1
        child_policy["parent_origin_sha256"] = core.canonical_hash(origin)
        core.write_json(destination / POLICY, child_policy)
        bind_record(destination, POLICY)
        for relative in files:
            target = safe_path(destination, relative, must_exist=False)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(safe_path(root, relative), target)
        requirements["requirements"] = selected
        requirements["case_id"] = case_id
        core.write_json(
            destination / core.ARTIFACT_PATHS["problem_requirements"],
            core.artifact("problem_requirements", requirements),
        )
        core.write_json(destination / "evidence/parent_origin.json", origin, overwrite=False)
        bind_record(destination, "evidence/parent_origin.json")
    return {
        "status": "NEW_REVISION" if revision else "NEW_SCOPED_CHILD",
        "case_id": case_id,
        "scope": ids,
        "native_state": "CREATED",
        "model_starts": 0,
        "aggregate_parent_completion": False,
    }


def resume(root, rid=None):
    result = status(root)
    records = request_records(root)
    if rid:
        records = [r for r in records if r["request_id"] == rid]
        if not records:
            raise ValueError("WB_REQUEST_MISSING")
    result["operations"] = [
        core.load_json(p)
        for request in records
        for p in sorted((root / REQUESTS / request["request_id"] / "operations").glob("*.json"))
    ]
    result["recovery"] = {
        "automatic_starts": 0,
        "prepared": "继续原请求；complete可重入并补导出审查包。",
        "completed_operation": "相同run参数复用已记录结果，不启动第二次。",
        "interrupted_operation": "保留STARTED/FAILED；核对实际capture和Final账本后新建revision。",
        "changed_input": "原件不可覆盖。新输入另行登记，新root重做受影响模块，不继承Final通过。",
    }
    return result


def freeze_code(root, paths):
    if policy(root)["mode"] != "GUIDED_LOCAL":
        raise ValueError("WB_LAB_FREEZE_USES_REGISTERED_PROTOCOL")
    for path in paths:
        safe_path(root, path)
        if not path.startswith("models/") or not path.endswith(".py"):
            raise ValueError("WB_CODE_SCOPE_INVALID")

    def git(*args):
        return (
            subprocess.check_output(
                [
                    "git",
                    "-c",
                    "core.hooksPath=/dev/null",
                    "-c",
                    "commit.gpgSign=false",
                    "-c",
                    "user.name=CUMCM Local",
                    "-c",
                    "user.email=local@invalid",
                    *args,
                ],
                cwd=root,
                stderr=subprocess.STDOUT,
            )
            .decode()
            .strip()
        )

    if not (root / ".git").exists():
        git("init", "-q")
    if (root / ".git").is_symlink() or not (root / ".git").is_dir():
        raise ValueError("WB_LOCAL_GIT_DIRECTORY_REQUIRED")
    if git("remote"):
        raise ValueError("WB_LOCAL_CASE_REMOTE_FORBIDDEN")
    staged = git("diff", "--cached", "--name-only", "-z").split("\0")
    if set(filter(None, staged)) - set(paths):
        raise ValueError("WB_UNRELATED_STAGED_FILES_REJECTED")
    git("add", "--", *paths)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=root, check=False).returncode:
        git("commit", "-q", "-m", "Freeze case-local modeling code")
    commit = git("rev-parse", "HEAD")
    return {
        "case_code_commit": commit,
        "remote_count": 0,
        "code_files": [
            {
                "scope": "CASE_ROOT",
                "path": p,
                "repository_path": f"CASE_GIT/{commit}/{p}",
                "sha256": core.file_hash(root / p),
            }
            for p in paths
        ],
    }


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    subs = p.add_subparsers(dest="command", required=True)
    subs.add_parser("modules")
    show = subs.add_parser("show")
    show.add_argument("module")
    for name in [
        "init",
        "prepare",
        "run",
        "complete",
        "status",
        "resume",
        "revision",
        "scoped-child",
        "freeze-code",
        "review-export",
        "context-export",
        "context-verify",
        "feedback-import",
        "feedback-resolve",
    ]:
        cmd = subs.add_parser(name)
        cmd.add_argument("--case-root", type=Path, required=True)
        if name == "init":
            cmd.add_argument("--case-id", required=True)
            cmd.add_argument(
                "--kind", choices=["general", "prediction", "optimization"], default="general"
            )
            cmd.add_argument("--mode", choices=["GUIDED_LOCAL", "LAB_EVAL"], default="GUIDED_LOCAL")
        if name == "prepare":
            cmd.add_argument("--module", required=True)
            cmd.add_argument("--scope", default="ALL")
            cmd.add_argument("--request-id")
        if name == "resume":
            cmd.add_argument("--request")
        if name in {"revision", "scoped-child"}:
            cmd.add_argument("--destination", type=Path, required=True)
            cmd.add_argument("--case-id", required=True)
            cmd.add_argument("--scope", default="ALL")
        if name in {"run", "complete", "review-export"}:
            cmd.add_argument("--request", required=True)
        if name == "run":
            cmd.add_argument(
                "--operation", choices=["model", "checker", "controller"], required=True
            )
            cmd.add_argument("--candidate")
            cmd.add_argument("--seed", type=int)
            cmd.add_argument("--run-id")
            cmd.add_argument("--code")
            cmd.add_argument("--timeout", type=int, default=600)
        if name == "complete":
            cmd.add_argument("--report", required=True)
        if name == "freeze-code":
            cmd.add_argument("--code", nargs="+", required=True)
        if name in {"review-export", "context-export"}:
            cmd.add_argument("--output", required=True)
        if name == "context-verify":
            cmd.add_argument("--context", required=True)
        if name == "review-export":
            cmd.add_argument("--zip", action="store_true")
        if name == "feedback-import":
            cmd.add_argument("--feedback", required=True)
        if name == "feedback-resolve":
            cmd.add_argument("--finding", required=True)
            cmd.add_argument(
                "--disposition",
                choices=["CONFIRMED", "NEEDS_EVIDENCE", "ALTERNATIVE_DESIGN", "NOT_SUPPORTED"],
                required=True,
            )
            cmd.add_argument("--evidence", required=True)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command in {"modules", "show"}:
            result = catalog() if args.command == "modules" else module(args.module)
        else:
            root = args.case_root.resolve()
            if args.command in {"status", "resume"}:
                result = resume(root, args.request) if args.command == "resume" else status(root)
            else:
                with core.case_writer(root):
                    if args.command == "init":
                        result = initialize(root, args.case_id, args.kind, args.mode)
                    elif args.command == "prepare":
                        result = prepare(root, args.module, args.scope, args.request_id)
                    elif args.command == "run":
                        result = run_operation(
                            root,
                            args.request,
                            args.operation,
                            candidate=args.candidate,
                            seed=args.seed,
                            run_id=args.run_id,
                            code=args.code,
                            timeout=args.timeout,
                        )
                    elif args.command == "complete":
                        import review_exchange

                        result = complete_module(root, args.request, args.report)
                        result = {
                            **result,
                            "review_package": review_exchange.export_package(
                                sys.modules[__name__], root, args.request, "reviews/" + args.request
                            ),
                        }
                    elif args.command == "freeze-code":
                        result = freeze_code(root, args.code)
                    elif args.command in {"revision", "scoped-child"}:
                        result = derive_case(
                            root,
                            args.destination.resolve(),
                            args.case_id,
                            args.scope,
                            revision=args.command == "revision",
                        )
                    else:
                        import review_exchange

                        result = review_exchange.dispatch(sys.modules[__name__], root, args)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        ImportError,
        subprocess.CalledProcessError,
    ) as exc:
        print(
            json.dumps(
                {"status": "BLOCK", "reason_codes": [str(exc)], "next_module_started": False},
                ensure_ascii=False,
            )
        )
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
