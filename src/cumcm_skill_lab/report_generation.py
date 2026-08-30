"""Generate deterministic human status from authoritative project state."""

import json
from pathlib import Path


def render_status_text(state: dict) -> str:
    blockers = "\n".join(f"- {item}" for item in state["blockers"]) or "- None"
    risks = "\n".join(f"- {item}" for item in state["risks"]) or "- None"
    verified = state["last_verified_commit"] or "UNVERIFIED"
    return f"""<!-- GENERATED FILE — DO NOT EDIT -->
# Current project state

- Project: `{state["project_id"]}`
- Phase: `{state["phase"]}`
- Status: `{state["status"]}`
- Active plan: `{state["current_plan"]}`
- Branch: `{state["current_branch"]}`
- Skill version: `{state["active_skill_version"]}`
- Skill capability: `{state.get("skill_capability_status", "UNKNOWN")}`
- Base selected: `{str(state.get("base_selected", False)).lower()}`
- Third-party integrated: `{str(state.get("third_party_integrated", False)).lower()}`
- Last verified commit: `{verified}`
- Updated: `{state["updated_at"]}` by `{state["updated_by"]}`

## Blockers

{blockers}

## Risks

{risks}
"""


def generate_status(root: Path, check: bool = False) -> tuple[bool, str]:
    state = json.loads((root / "state/project_state.json").read_text(encoding="utf-8"))
    expected = render_status_text(state)
    output = root / "reports/current_state.md"
    if check:
        actual = output.read_text(encoding="utf-8") if output.exists() else ""
        return actual == expected, expected
    output.write_text(expected, encoding="utf-8")
    return True, expected
