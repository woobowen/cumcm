"""Repository invariants shared by deterministic validators."""

EXPECTED_SKILL = "cumcm-modeling-evidence"
EXPECTED_CANDIDATES = 8
ROOT_AGENTS_LIMIT = 8 * 1024
CHAIN_WARNING_LIMIT = 32 * 1024
SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"

REQUIRED_PATHS = (
    "AGENTS.md",
    "GOALS.md",
    "WORKFLOW.md",
    "PLANS.md",
    "README.md",
    "VERSION",
    "CHANGELOG.md",
    "THIRD_PARTY_NOTICES.md",
    "LICENSE_LEDGER.csv",
    ".agents/skills/cumcm-modeling-evidence/SKILL.md",
    "docs/SOURCE_OF_TRUTH.md",
    "plans/active/PLAN-0002-upstream-dynamic-evaluation.md",
    "research/upstream_candidates/manifest.yaml",
    "state/project_state.json",
    "reports/current_state.md",
    "reports/foundation_acceptance.md",
)
