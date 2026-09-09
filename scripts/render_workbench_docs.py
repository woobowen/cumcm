"""Render module task cards and index from the one Skill registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents/skills/cumcm-modeling-evidence"


def render():
    records = json.loads((SKILL / "references/modules.json").read_text())["modules"]
    outputs = {}
    index = [
        "# 十四模块目录",
        "",
        "配置真源为正式Skill的 `references/modules.json`。本目录由脚本生成。",
        "模块完成不等于科学结论成立；原生状态与模块产物分别显示。",
        "",
        "| ID | 职责 | 原生状态终点 | 任务卡 |",
        "|---|---|---|---|",
    ]
    for card in records:
        mid = card["id"]
        relative = f"references/modules/{mid}.md"
        target = card["native_target"] or "保持当前原生状态；核验本模块产物"
        index.append(
            f"| {mid} | {card['name']} | {target} | [{mid}]"
            f"(../../.agents/skills/cumcm-modeling-evidence/{relative}) |"
        )
        text = [
            f"# {mid} {card['name']}",
            "",
            f"目的：{card['action']}。",
            "",
            f"既有workflow：[说明](../../{card['workflow']})。",
            f"最少用户输入：{card['minimum_input']}。case/module/scope由用户指定，内部身份由工具定位。",
            f"前置模块：{', '.join(card['prerequisites']) or '无'}。"
            "仅接受当前范围且hash一致的前置；缺少时明确拒绝。",
            "",
            "允许工具：Codex阅读、一般资料研究（遵守case policy）、本地Python及既有公共CLI。",
            "禁止：把prepare算作研究完成；自动推进下一个模块；覆盖原始输入/历史Run；以网页意见或多数票代替证据。",
            "",
            "产物："
            + (", ".join(card["artifacts"]) or "work report所指的真实原件/代码/capture")
            + "，及独立work report和本地审查包。",
            f"工程核验：身份、前置、实际文件hash与适用core gate；原生状态终点：{target}。",
            f"科学审查：{card['review_question']}",
            f"完成的含义：{card['meaning']}。",
            "",
            f"停止：{card['stop']}",
            f"恢复：{card['recovery']}",
            f"下游影响：{card['downstream']}",
            "",
            "可复制给Codex的请求：",
            "",
            "```text",
            card["example"],
            f"先读取正式Skill与本任务卡。{card['action']}。",
            "使用prepare登记请求，在模块内实际分析/编码/核验，再complete核验并导出审查包。",
            "如未知或缺前置，报告具体缺口；不要猜内部hash，不补做未授权模块。",
            "```",
            "",
            "真实入口（REQ编号是用户可读请求名，可替换；CASE_ROOT须为独立工作区）：",
            "",
            "```bash",
            ".venv/bin/python .agents/skills/cumcm-modeling-evidence/scripts/cumcm_workbench.py "
            f"prepare --case-root <CASE_ROOT> --module {mid} --scope ALL --request-id REQ-{mid}",
            f"# Codex现在实际完成{mid}工作。prepare只生成任务，不运行研究或模型。",
            ".venv/bin/python .agents/skills/cumcm-modeling-evidence/scripts/cumcm_workbench.py "
            f"complete --case-root <CASE_ROOT> --request REQ-{mid} --report work/{mid}.json",
            "```",
            "",
            "M09使用run的model/checker操作；M10–M14在complete之前显式执行run的controller操作。",
            "真实命令的实测范围与结果见[Runbook](../../../../../docs/modular_workbench/RUNBOOK.md)。",
        ]
        outputs[SKILL / relative] = "\n".join(text) + "\n"
    outputs[ROOT / "docs/modular_workbench/MODULES.md"] = "\n".join(index) + "\n"
    return outputs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale = []
    for path, text in render().items():
        if args.check:
            if not path.is_file() or path.read_text() != text:
                stale.append(path.relative_to(ROOT).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    print(json.dumps({"status": "STALE" if stale else "CURRENT", "stale": stale}))
    return bool(stale)


if __name__ == "__main__":
    raise SystemExit(main())
