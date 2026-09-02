from copy import deepcopy

import pytest

from cumcm_skill_lab.failure_aware.supplemental import (
    PROTOCOL_FIELDS,
    START_PRECONDITIONS,
    build_protocol_fingerprint,
    evaluate_start_preconditions,
    protocol_compatibility,
)


@pytest.mark.parametrize("field", PROTOCOL_FIELDS)
def test_protocol_mutations_require_new_cohort(repo_root, field):
    frozen = build_protocol_fingerprint(repo_root)
    mutated = deepcopy(frozen)
    mutated[field] = f"MUTATED:{mutated[field]}"
    result = protocol_compatibility(frozen, mutated)
    assert result == {
        "result": "NEW_PROTOCOL_COHORT_REQUIRED",
        "drift_fields": [field],
        "pool_with_current_evidence": False,
    }


@pytest.mark.parametrize("missing", START_PRECONDITIONS)
def test_every_missing_precondition_yields_zero_starts(missing):
    preconditions = {name: True for name in START_PRECONDITIONS}
    preconditions[missing] = False
    assert evaluate_start_preconditions(preconditions) == [missing]
