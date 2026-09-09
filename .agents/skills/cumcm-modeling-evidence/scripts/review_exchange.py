"""Bounded local derived review views and inert feedback findings. No execution API."""

from __future__ import annotations

import io
import json
import re
import zipfile

MAX_FILE = 2_000_000
MAX_PACKAGE = 8_000_000
MAX_FEEDBACK = 64_000
SECRET = re.compile(
    r"(?i)(?:-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY|"
    r"(?:api[_-]?key|password|access[_-]?token|client[_-]?secret)[\"']?\s*[:=]\s*[\"']?[^\s\"',}]{4,}|"
    r"gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|WORKBENCH_SECRET_CANARY)"
)
PRIVATE = re.compile(r"(?:/(?:home|Users)/[^/\s\"']+|[A-Za-z]:\\Users\\[^\\\s\"']+)")
INSTRUCTION = re.compile(
    r"(?i)(?:ignore (?:all |previous |system )?instructions|忽略.{0,12}(?:指令|规则)|"
    r"(?:读取|导出|打印).{0,10}(?:凭据|密钥|token)|(?:修改|重置|增加).{0,10}(?:预算|权限)|"
    r"(?:强制|改成|写入).{0,8}PASS|(?:切换|修改).{0,8}(?:模式|mode)|"
    r"(?:解封|读取).{0,8}(?:答案|保留题)|\b(?:curl|wget|bash|sudo|eval|exec)\b|"
    r"subprocess|os\.system|git\s+(?:push|reset|clean)|rm\s+-|\$\(|`[^`]+`)"
)


def read_text(path, limit=MAX_FILE):
    if path.stat().st_size > limit:
        raise ValueError("WB_SIZE_LIMIT")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeError as exc:
        raise ValueError("WB_BINARY_VIEW_REQUIRES_EXPLICIT_DERIVATION") from exc


def safe_view(path):
    text = read_text(path)
    if SECRET.search(text):
        raise ValueError("WB_CREDENTIAL_CONTENT_REJECTED")
    return PRIVATE.sub("<PRIVATE_USER_PATH>", text), ["UTF8_TEXT", "PRIVATE_USER_PREFIX_REDACTION"]


def write_immutable(core, path, data):
    if any(item.is_symlink() for item in (path, *path.parents)):
        raise ValueError("WB_EXPORT_SYMLINK_REJECTED")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError("WB_EXPORT_DESTINATION_CONFLICT")
    else:
        path.write_bytes(data)


def export_package(wb, root, rid, output, *, archive=False):
    core = wb.core
    request = wb.find_request(root, rid)
    done = wb.receipt(root, request)
    if not done:
        raise ValueError("WB_MODULE_REPORT_REQUIRED_BEFORE_EXPORT")
    target = wb.safe_path(root, output, must_exist=False)
    if target.is_file():
        raise ValueError("WB_EXPORT_DESTINATION_CONFLICT")
    report = core.load_json(wb.safe_path(root, done["report_path"]))
    originals = dict(done["artifact_hashes"])
    originals.update(request["prerequisite_files"])
    # Previous receipts suffice for the chain. Avoid carrying every prior report's
    # full text recursively: the current report explicitly names needed context.
    included = sorted(set(done["artifact_hashes"]) | {core.ARTIFACT_PATHS["problem_requirements"]})
    views, total, prepared, missing = [], 0, [], []
    for index, relative in enumerate(included):
        source = wb.safe_path(root, relative)
        originals[relative] = core.file_hash(source)
        if source.suffix.lower() in {".xlsx", ".xls", ".pdf", ".png", ".jpg", ".zip"}:
            text = "二进制原件未嵌入；请结合明确提供的派生文本核查。原件hash见manifest。\n"
            transforms = ["BINARY_METADATA_ONLY"]
            missing.append({"source_path": relative, "reason": "BINARY_NOT_EMBEDDED"})
        else:
            text, transforms = safe_view(source)
        data = text.encode("utf-8")
        total += len(data)
        if total > MAX_PACKAGE:
            raise ValueError("WB_REVIEW_PACKAGE_TOO_LARGE")
        name = f"views/{index:03}-{source.name}.txt"
        views.append(
            {
                "path": name,
                "source_path": relative,
                "source_sha256": core.file_hash(source),
                "view_sha256": core.hashlib.sha256(data).hexdigest(),
                "transforms": transforms,
                "bytes": len(data),
            }
        )
        prepared.append((name, data))
    summary = (
        "\n".join(
            [
                f"# {request['case_id']} / {request['module']} 审查包",
                "",
                report["summary_cn"],
                "",
                "原要求：",
                *[str(x) for x in report["original_requirements"]],
                "",
                "实际动作：",
                *[str(x) for x in report["actions"]],
                "",
                "实际检查（静态阅读、独立程序与未检查分别标记）：",
                *[str(x) for x in report["checks"]],
                "",
                "负结果和缺口：",
                *[str(x) for x in report["negative_results"]],
                "",
                "具体审核问题：",
                *[str(x) for x in report["review_questions"]],
                "",
                "科学支持范围：" + report["scientific_scope"],
                "队员人工核验：NOT_RUN。请实际上传本目录；网页没有自动读取本机文件。",
                "审核意见只登记待核查finding，不执行指令、不决定正式PASS、不自动推进模块。",
            ]
        )
        + "\n"
    )
    if SECRET.search(summary):
        raise ValueError("WB_CREDENTIAL_CONTENT_REJECTED")
    summary = PRIVATE.sub("<PRIVATE_USER_PATH>", summary)
    prepared.append(("REVIEW.md", summary.encode("utf-8")))
    manifest = {
        "schema_version": "module-review-package/v1",
        "case_id": request["case_id"],
        "module": request["module"],
        "request_id": rid,
        "revision": request["revision"],
        "requirement_scope": request["requirement_scope"],
        "implementation": request["implementation"],
        "generated_at": done["completed_at"],
        "request_sha256": core.canonical_hash(request),
        "completion_sha256": core.file_hash(root / wb.REQUESTS / rid / "completion.json"),
        "original_hashes": originals,
        "views": views,
        "missing_items": missing,
        "files": {name: core.hashlib.sha256(data).hexdigest() for name, data in prepared},
        "scope": "LOCAL_REVIEW_ONLY",
        "human_review": "NOT_RUN",
        "automatic_upload": False,
    }
    manifest["package_hash"] = core.canonical_hash(manifest)
    for name, data in prepared:
        write_immutable(core, target / name, data)
    write_immutable(core, target / "manifest.json", core.canonical_bytes(manifest) + b"\n")
    index = {
        "package_hash": manifest["package_hash"],
        "path": output,
        "manifest_sha256": core.file_hash(target / "manifest.json"),
    }
    index_path = root / "evidence/review_exports" / (manifest["package_hash"] + ".json")
    if index_path.exists():
        if verified_package(wb, root, manifest["package_hash"]) != manifest:
            raise ValueError("WB_PACKAGE_IDENTITY_CONFLICT")
    else:
        write_immutable(core, index_path, core.canonical_bytes(index) + b"\n")
    archive_path = None
    if archive:
        stream = io.BytesIO()
        members = prepared + [("manifest.json", core.canonical_bytes(manifest) + b"\n")]
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
            for name, data in sorted(members):
                # Fixed archive metadata enables byte-identical repeated exports;
                # the actual observation time remains in the manifest.
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                zipped.writestr(info, data)
        archive_path = output + ".zip"
        write_immutable(core, wb.safe_path(root, archive_path, must_exist=False), stream.getvalue())
    return {
        "status": "EXPORTED_LOCAL_ONLY",
        **index,
        "archive": archive_path,
        "upload_files": [output + "/REVIEW.md", output + "/manifest.json", output + "/views/"],
    }


def verified_package(wb, root, package_hash):
    core = wb.core
    if not isinstance(package_hash, str) or not core.HEX64.fullmatch(package_hash):
        raise ValueError("WB_PACKAGE_HASH_INVALID")
    index_path = root / "evidence/review_exports" / (package_hash + ".json")
    if not index_path.is_file():
        raise ValueError("WB_PACKAGE_UNKNOWN")
    index = core.load_json(index_path)
    manifest_path = wb.safe_path(root, index["path"] + "/manifest.json")
    if core.file_hash(manifest_path) != index["manifest_sha256"]:
        raise ValueError("WB_EXPORTED_MANIFEST_CHANGED")
    manifest = core.load_json(manifest_path)
    if (
        core.canonical_hash({k: v for k, v in manifest.items() if k != "package_hash"})
        != package_hash
    ):
        raise ValueError("WB_PACKAGE_HASH_MISMATCH")
    for relative, digest in manifest["files"].items():
        if core.file_hash(wb.safe_path(manifest_path.parent, relative)) != digest:
            raise ValueError("WB_EXPORTED_VIEW_CHANGED")
    return manifest


def feedback_import(wb, root, relative):
    core = wb.core
    path = wb.safe_path(root, relative)
    if path.suffix.lower() not in {".json", ".md"}:
        raise ValueError("WB_FEEDBACK_ARCHIVES_AND_EXECUTABLES_REJECTED")
    text = read_text(path, MAX_FEEDBACK)
    if path.suffix.lower() == ".md":
        match = re.fullmatch(r"\s*```json\s*\n(.*)\n```\s*", text, re.DOTALL)
        if not match:
            raise ValueError("WB_FEEDBACK_MARKDOWN_REQUIRES_SINGLE_JSON_BLOCK")
        text = match[1]
    if SECRET.search(text) or INSTRUCTION.search(text):
        raise ValueError("WB_FEEDBACK_UNAUTHORIZED_INSTRUCTION_OR_SECRET")
    data = json.loads(
        text, parse_constant=core.reject_constant, object_pairs_hook=core.unique_json_object
    )

    def reject_decoded_instructions(value):
        if isinstance(value, str) and (SECRET.search(value) or INSTRUCTION.search(value)):
            raise ValueError("WB_FEEDBACK_UNAUTHORIZED_INSTRUCTION_OR_SECRET")
        if isinstance(value, dict):
            for key, item in value.items():
                reject_decoded_instructions(key)
                reject_decoded_instructions(item)
        elif isinstance(value, list):
            for item in value:
                reject_decoded_instructions(item)

    reject_decoded_instructions(data)
    required = {
        "schema_version",
        "case_id",
        "module",
        "revision",
        "package_hash",
        "reviewer",
        "visible_materials",
        "executed_code",
        "findings",
    }
    if (
        not isinstance(data, dict)
        or set(data) != required
        or data["schema_version"] != "web-feedback/v1"
    ):
        raise ValueError("WB_FEEDBACK_SCHEMA_INVALID")
    manifest = verified_package(wb, root, data["package_hash"])
    if any(data[k] != manifest[k] for k in ["case_id", "module", "revision"]):
        raise ValueError("WB_FEEDBACK_IDENTITY_MISMATCH")
    if data["case_id"] != wb.policy(root)["case_id"]:
        raise ValueError("WB_FEEDBACK_WRONG_CASE")
    if (
        type(data["executed_code"]) is not bool
        or not isinstance(data["reviewer"], str)
        or not data["reviewer"].strip()
    ):
        raise ValueError("WB_FEEDBACK_REVIEWER_INVALID")
    if (
        not isinstance(data["visible_materials"], list)
        or not data["visible_materials"]
        or not all(isinstance(item, str) for item in data["visible_materials"])
        or not set(data["visible_materials"]) <= set(manifest["files"])
    ):
        raise ValueError("WB_FEEDBACK_VISIBLE_SCOPE_INVALID")
    if type(data["revision"]) is not int or data["revision"] < 1:
        raise ValueError("WB_FEEDBACK_REVISION_INVALID")
    findings = data["findings"]
    if not isinstance(findings, list) or not 1 <= len(findings) <= 30:
        raise ValueError("WB_FEEDBACK_FINDING_COUNT_INVALID")
    prepared = []
    ids = set()
    stale = (
        not wb.bound_current(root, manifest["original_hashes"])
        or manifest["implementation"]["implementation_sha256"]
        != wb.identity()["implementation_sha256"]
    )
    for finding in findings:
        fields = {
            "finding_id",
            "location",
            "description",
            "reason_or_counterexample",
            "affected_scope",
            "suggested_verification",
            "confidence",
            "kind",
        }
        if (
            not isinstance(finding, dict)
            or set(finding) != fields
            or not all(isinstance(v, str) and v.strip() for v in finding.values())
        ):
            raise ValueError("WB_FEEDBACK_FINDING_INVALID")
        fid = finding["finding_id"]
        if not wb.ID.fullmatch(fid) or fid in ids or finding["location"] not in manifest["files"]:
            raise ValueError("WB_FEEDBACK_LOCATION_OR_ID_INVALID")
        if finding["kind"] not in {
            "CALCULATION",
            "EVIDENCE",
            "SCIENTIFIC",
            "ALTERNATIVE",
        } or finding["confidence"] not in {"HIGH", "MEDIUM", "LOW", "UNKNOWN"}:
            raise ValueError("WB_FEEDBACK_KIND_INVALID")
        ids.add(fid)
        key = data["package_hash"][:16] + "-" + fid
        record = {
            "schema_version": "registered-finding/v1",
            "finding_key": key,
            "case_id": data["case_id"],
            "module": data["module"],
            "revision": data["revision"],
            "package_hash": data["package_hash"],
            "reviewer": data["reviewer"],
            "visible_materials": data["visible_materials"],
            "executed_code": data["executed_code"],
            "finding": finding,
            "status": "STALE" if stale else "PENDING_VERIFICATION",
            "formal_acceptance": False,
        }
        target = root / "evidence/review_findings" / (key + ".json")
        if target.exists():
            previous = core.load_json(target)
            if {k: v for k, v in previous.items() if k != "status"} != {
                k: v for k, v in record.items() if k != "status"
            }:
                raise ValueError("WB_FINDING_ID_CONFLICT")
            record = previous
        prepared.append((target, record))
    for target, record in prepared:
        write_immutable(core, target, core.canonical_bytes(record) + b"\n")
    return {
        "status": "REGISTERED_STALE" if stale else "REGISTERED_PENDING",
        "findings": [r["finding_key"] for _, r in prepared],
        "formal_state_changed": False,
        "scripts_executed": 0,
    }


def feedback_resolve(wb, root, key, disposition, evidence):
    core = wb.core
    if not wb.ID.fullmatch(key):
        raise ValueError("WB_FINDING_ID_INVALID")
    finding = core.load_json(wb.safe_path(root, "evidence/review_findings/" + key + ".json"))
    manifest = verified_package(wb, root, finding["package_hash"])
    if (
        finding["status"] == "STALE"
        or not wb.bound_current(root, manifest["original_hashes"])
        or manifest["implementation"]["implementation_sha256"]
        != wb.identity()["implementation_sha256"]
    ):
        raise ValueError("WB_STALE_FINDING_CANNOT_RESOLVE_CURRENT")
    path = wb.safe_path(root, evidence)
    data = core.load_json(path)
    fields = {"finding_key", "method", "rationale", "observations", "evidence_files"}
    if not isinstance(data, dict) or set(data) != fields or data.get("finding_key") != key:
        raise ValueError("WB_DISPOSITION_EVIDENCE_INVALID")
    if (
        data["method"]
        not in {"INDEPENDENT_RECOMPUTATION", "SCIENTIFIC_ARGUMENT", "EVIDENCE_GAP_ANALYSIS"}
        or not isinstance(data["rationale"], str)
        or len(data["rationale"].strip()) < 20
        or not isinstance(data["observations"], list)
        or not data["observations"]
    ):
        raise ValueError("WB_DISPOSITION_REASONING_REQUIRED")
    if disposition == "CONFIRMED" and data["method"] == "EVIDENCE_GAP_ANALYSIS":
        raise ValueError("WB_COUNTEREXAMPLE_NOT_REPRODUCED")
    if not isinstance(data["evidence_files"], list) or not data["evidence_files"]:
        raise ValueError("WB_DISPOSITION_ACTUAL_EVIDENCE_REQUIRED")
    hashes = {p: core.file_hash(wb.safe_path(root, p)) for p in data["evidence_files"]}
    result = {
        "finding_key": key,
        "disposition": disposition,
        "evidence_sha256": core.file_hash(path),
        "evidence_path": evidence,
        "bound_files": hashes,
        "formal_acceptance": False,
        "next_module_started": False,
    }
    target = root / "evidence/review_dispositions" / (key + ".json")
    write_immutable(core, target, core.canonical_bytes(result) + b"\n")
    return result


def context_export(wb, root, output):
    core = wb.core
    current = wb.status(root)
    findings = [
        core.load_json(p) for p in sorted((root / "evidence/review_findings").glob("*.json"))
    ]
    source = {
        "case_state_sha256": core.file_hash(core.state_path(root)),
        "policy_sha256": core.file_hash(root / wb.POLICY),
        "requests": {r["request_id"]: core.canonical_hash(r) for r in wb.request_records(root)},
        "files": {
            p.relative_to(root).as_posix(): core.file_hash(p)
            for folder in [wb.REQUESTS, "evidence/review_findings", "evidence/review_dispositions"]
            for p in sorted((root / folder).rglob("*.json"))
            if p.is_file()
        },
    }
    body = {
        "schema_version": "brain-context/v1",
        "source": source,
        "status": current,
        "findings": findings,
        "execution_mode": "GUIDED_SINGLE_MODULE",
        "derived_view_only": True,
        "local_facts_are_authoritative": True,
        "web_and_team_acceptance": "NOT_RUN",
    }
    body["context_hash"] = core.canonical_hash(body)
    target = wb.safe_path(root, output, must_exist=False)
    if SECRET.search(json.dumps(body, ensure_ascii=False)):
        raise ValueError("WB_CREDENTIAL_CONTENT_REJECTED")
    write_immutable(core, target / "context.json", core.canonical_bytes(body) + b"\n")
    lines = [
        f"# 当前上下文：{current['case_id']}",
        "",
        f"原生状态：{current['native_state']['state']}",
        "来源指纹：" + body["context_hash"],
        "",
        "当前模块记录：",
    ]
    lines += [
        f"- {m['module']} {m['scope']} {m['status']} ({m['request_id']})"
        for m in current["modules"]
    ]
    lines += [
        "",
        "待核查意见：" + str(len(findings)),
        "默认只执行用户指定的一个模块。没有实际上传文件，网页不能声称读取本机。",
        "新大脑负责当前协调，旧对话供历史咨询；同项目记忆不等于严格盲审或版本同步。",
        "请同时提供START_HERE、角色提示词及本次相关审查包；这里不自动授权任何脚本或Git发布。",
    ]
    write_immutable(core, target / "CONTEXT.md", ("\n".join(lines) + "\n").encode())
    return {
        "status": "CONTEXT_EXPORTED_LOCAL_ONLY",
        "path": output,
        "context_hash": body["context_hash"],
    }


def context_verify(wb, root, relative):
    core = wb.core
    body = core.load_json(wb.safe_path(root, relative))
    if (
        not isinstance(body, dict)
        or core.canonical_hash({k: v for k, v in body.items() if k != "context_hash"})
        != body.get("context_hash")
        or body["status"]["case_id"] != wb.policy(root)["case_id"]
    ):
        raise ValueError("WB_CONTEXT_IDENTITY_INVALID")
    source = body["source"]
    if (
        core.file_hash(core.state_path(root)) != source["case_state_sha256"]
        or not wb.bound_current(root, source["files"])
        or wb.status(root) != body["status"]
    ):
        raise ValueError("WB_CONTEXT_STALE_REEXPORT_REQUIRED")
    return {
        "status": "CONTEXT_CURRENT",
        "context_hash": body["context_hash"],
        "scripts_executed": 0,
    }


def dispatch(wb, root, args):
    if args.command == "review-export":
        return export_package(wb, root, args.request, args.output, archive=args.zip)
    if args.command == "context-export":
        return context_export(wb, root, args.output)
    if args.command == "context-verify":
        return context_verify(wb, root, args.context)
    if args.command == "feedback-import":
        return feedback_import(wb, root, args.feedback)
    return feedback_resolve(wb, root, args.finding, args.disposition, args.evidence)
