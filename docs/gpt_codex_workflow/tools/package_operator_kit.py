"""Local descriptive operator packages; never a case writer or scientific acceptor."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath

KIT = Path(__file__).resolve().parents[1]
REPO = KIT.parents[1]
VERSION = "1.0.0"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def check_name(name):
    p = PurePosixPath(name)
    if (
        p.is_absolute()
        or ".." in p.parts
        or "\\" in name
        or ":" in name
        or not name
        or str(p) != name
    ):
        raise ValueError("UNSAFE_PACKAGE_PATH")


def verify(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("DUPLICATE_PACKAGE_PATH")
        if sum(x.file_size for x in archive.infolist()) > 5_000_000:
            raise ValueError("PACKAGE_TOO_LARGE")
        for item in archive.infolist():
            check_name(item.filename)
            if stat.S_ISLNK(item.external_attr >> 16) or item.flag_bits & 1:
                raise ValueError("UNSAFE_PACKAGE_MEMBER")
        if archive.testzip():
            raise ValueError("PACKAGE_CRC_FAILED")
        manifest = json.loads(archive.read("PACKAGE_MANIFEST.json"))
        expected = manifest["files"]
        if set(expected) != set(names) - {"PACKAGE_MANIFEST.json"}:
            raise ValueError("PACKAGE_MEMBER_SET_MISMATCH")
        for name, sha in expected.items():
            if digest(archive.read(name)) != sha:
                raise ValueError("PACKAGE_CONTENT_HASH_MISMATCH")
        if digest(canonical(expected)) != manifest["payload_set_sha256"]:
            raise ValueError("PACKAGE_SET_HASH_MISMATCH")
        # Local Markdown links are required to work without the repository.
        for name in names:
            if not name.endswith(".md"):
                continue
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", archive.read(name).decode()):
                if target.startswith(("https://", "http://", "#")):
                    continue
                target = target.split("#")[0]
                joined = str(PurePosixPath(name).parent / target)
                if joined not in names:
                    raise ValueError("OFFLINE_LINK_MISSING:" + name + ":" + target)
        if manifest["kind"] == "NO_CASE":
            snapshot = json.loads(archive.read("STARTUP_SNAPSHOT.json"))
            if (
                snapshot["active_case"] is not None
                or snapshot["active_module"] is not None
                or snapshot["model_or_final_execution_authorized"]
                or snapshot["competition_problem_loaded"]
                or snapshot["schema_version"] == "brain-context/v1"
                or any("context.json" in n or n.startswith("example/") for n in names)
            ):
                raise ValueError("NO_CASE_ISOLATION_FAILED")
    return {
        "archive_sha256": digest(path.read_bytes()),
        "bytes": path.stat().st_size,
        "members": len(names),
        "kind": manifest["kind"],
        "payload_set_sha256": manifest["payload_set_sha256"],
        "status": "PACKAGE_INTEGRITY_VERIFIED_NOT_SCIENTIFIC_ACCEPTANCE",
    }


def build(kind, output, source=None, context=None, support=None):
    if output.exists():
        raise ValueError("OUTPUT_ALREADY_EXISTS")
    files = {
        p.name: p.read_bytes()
        for p in sorted(KIT.iterdir())
        if p.is_file() and p.suffix in {".md", ".json"}
    }
    if kind == "NO_CASE":
        files["STARTUP_SNAPSHOT.json"] = (
            canonical(
                {
                    "schema_version": "operator-startup-description/v1",
                    "operator_kit_version": VERSION,
                    "active_case": None,
                    "active_module": None,
                    "competition_problem_loaded": False,
                    "model_or_final_execution_authorized": False,
                    "example_loaded": False,
                    "authoritative_scientific_state": False,
                    "expected_response": "NO_ACTIVE_CASE",
                }
            )
            + b"\n"
        )
    else:
        if source is None or not source.is_dir():
            raise ValueError("SOURCE_DIRECTORY_REQUIRED")
        prefix = "example" if kind == "EXAMPLE_ONLY" else "review"
        for p in sorted(source.rglob("*")):
            if p.is_symlink():
                raise ValueError("SOURCE_SYMLINK_REJECTED")
            if p.is_file():
                files[prefix + "/" + p.relative_to(source).as_posix()] = p.read_bytes()
        if context:
            for name in ["context.json", "CONTEXT.md"]:
                files["context/" + name] = (context / name).read_bytes()
        if support:
            for p in sorted(support.rglob("*")):
                if p.is_symlink():
                    raise ValueError("SUPPORT_SYMLINK_REJECTED")
                if p.is_file():
                    files["support/" + p.relative_to(support).as_posix()] = p.read_bytes()
    files["READ_FIRST.txt"] = (
        f"Operator kit {VERSION}; package kind={kind}.\n"
        "Read START_HERE.md and the matching prompt. This package authorizes no execution.\n"
        "NO_CASE has no active problem; EXAMPLE_ONLY preserves an immutable completed example;\n"
        "NEXT_WEB is an actual new original rehearsal, pending user upload and new web response.\n"
        "Only included bytes are available offline; full environment/repository is not included.\n"
        "Inner review identity is unchanged. Outer support notes are derived, non-authoritative.\n"
    ).encode()
    if kind == "NEXT_WEB":
        files["NEXT_WEB_PROMPT.md"] = (
            "# 下一次真实网页审查：复制正文\n\n"
            "请先读READ_FIRST.txt和review/manifest.json，按WEB_PACKAGE_TRIAGE分诊；这是新原创演练，"
            "不是比赛题或旧示例。然后使用WEB_REVIEW_PROMPTS中的D和E视角，核数字、独立程序范围、"
            "完整符号、逐问中文结论与源字段。先声明实际可见文件/版本及是否运行代码。"
            "请输出独立REVIEW_SUMMARY.md；确有finding时另给严格web-feedback/v1 JSON，"
            "case/module/revision/package_hash从内层review/manifest.json读取，location/visible_materials"
            "使用其files键（去掉外层review/前缀）。包外support问题只在摘要定位，不能硬塞内层JSON。"
            "没有问题不造finding或空列表；不写正式PASS，不启动模块/Final。"
            "源码引用无字节记SOURCE_BYTES_NOT_AVAILABLE_HERE，独立算术不冒充完整重放。\n"
        ).encode()
    for name in files:
        check_name(name)
    hashes = {k: digest(v) for k, v in sorted(files.items())}
    files["PACKAGE_MANIFEST.json"] = (
        canonical(
            {
                "schema_version": "operator-package-description/v1",
                "kind": kind,
                "operator_kit_version": VERSION,
                "automatic_upload": False,
                "scientific_authority": False,
                "files": hashes,
                "payload_set_sha256": digest(canonical(hashes)),
            }
        )
        + b"\n"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 10, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return verify(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("verify")
    check.add_argument("--archive", type=Path, required=True)
    pack = sub.add_parser("build")
    pack.add_argument("--kind", choices=["NO_CASE", "EXAMPLE_ONLY", "NEXT_WEB"], required=True)
    pack.add_argument("--output", type=Path, required=True)
    pack.add_argument("--source", type=Path)
    pack.add_argument("--context", type=Path)
    pack.add_argument("--support", type=Path)
    args = parser.parse_args()
    result = (
        verify(args.archive)
        if args.command == "verify"
        else build(args.kind, args.output, args.source, args.context, args.support)
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
