# 2024 C diagnostic replay

{
  "aggregate_primary_ids": [
    "REQ-2024C-CONSTRAINTS",
    "REQ-2024C-MANAGEMENT",
    "REQ-2024C-Q1-DISCOUNT",
    "REQ-2024C-Q1-WASTE",
    "REQ-2024C-Q2-UNCERTAINTY",
    "REQ-2024C-Q3-DEPENDENCE"
  ],
  "answer_state": "SEALED",
  "case_id": "CUMCM-2024-C-VALIDATION-001",
  "claim_contract_version": "claim-evidence/v2",
  "claim_gate": {
    "accepted": true,
    "final": false,
    "reason_codes": [
      "RC_CLAIM_EXACT_SUPPORT_VALID"
    ],
    "status": "PASS"
  },
  "classification": "POST_VALIDATION_DIAGNOSTIC_REPLAY",
  "comparison_gate": {
    "accepted": true,
    "final": false,
    "reason_codes": [
      "RC_LEAKAGE_SAFE_COMPARISON_VALID"
    ],
    "status": "PASS"
  },
  "derived_claim_sha256": "e5e7083e05d0d5f30544ef7295dd2bd8b2dba1967df7d1c0c43647527ea5217a",
  "derived_handoff_sha256": "4f8c1ce5553ca114763584daf5eef8b484de5f42750918f361d894c47ed28290",
  "diagnostic_id": "CUMCM-2024-C-POST-VALIDATION-DEVELOPMENT-DIAGNOSTIC",
  "elapsed_seconds": 0.137,
  "failed_runs_retained": 0,
  "final_gate": {
    "accepted": true,
    "final": false,
    "reason_codes": [
      "RC_FINAL_RESULT_EXACTLY_BOUND"
    ],
    "status": "PASS"
  },
  "handoff_gate": {
    "accepted": true,
    "final": false,
    "reason_codes": [
      "RC_MODELING_TO_PAPER_HANDOFF_VALID"
    ],
    "status": "PASS"
  },
  "new_model_runs": 0,
  "no_validation_credit": true,
  "old_case_state": "REJECTED",
  "old_files_unchanged": true,
  "old_verdict": "C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT",
  "primary_requirement_count": 6,
  "reason_codes": [],
  "robustness_gate": {
    "accepted": true,
    "final": false,
    "reason_codes": [
      "RC_ROBUSTNESS_EXACTLY_BOUND"
    ],
    "status": "PASS"
  },
  "run_count": 4,
  "run_gates": [
    {
      "accepted": true,
      "final": false,
      "reason_codes": [
        "RC_REPRODUCIBILITY_MANIFEST_VALID"
      ],
      "status": "PASS"
    },
    {
      "accepted": true,
      "final": false,
      "reason_codes": [
        "RC_REPRODUCIBILITY_MANIFEST_VALID"
      ],
      "status": "PASS"
    },
    {
      "accepted": true,
      "final": false,
      "reason_codes": [
        "RC_REPRODUCIBILITY_MANIFEST_VALID"
      ],
      "status": "PASS"
    },
    {
      "accepted": true,
      "final": false,
      "reason_codes": [
        "RC_REPRODUCIBILITY_MANIFEST_VALID"
      ],
      "status": "PASS"
    }
  ],
  "run_validation_code_context": "HASH_VERIFIED_ORIGINAL_GIT_BLOBS_NO_EXECUTION",
  "skill_version": "0.2.0-competition-rc5",
  "source_manifest_hashes": {
    "RUN-BASELINE_RULE_ROTATION-104729": "921dc61b3129a68a29c5df773878d53ba6ba7025f8c3ab45425c8dbf235740a2",
    "RUN-BASELINE_RULE_ROTATION-130363": "a958aa38e8c3d91b9668c99c10a977b9770ed82ec183430b8218c3526e84166a",
    "RUN-PRIMARY_RISK_GREEDY-104729": "9c651819b573598d2f9020d4f7b1cb7b0a2d1f8d4150fb990a890e6a1a244a9d",
    "RUN-PRIMARY_RISK_GREEDY-130363": "90cde5445db52a2dd0ac23d0ca6b9be5f87d2f6df498f32d442c072b852f7e26"
  },
  "source_state": "REJECTED",
  "source_state_sha256": "f3644552aa1c8bdd23236a74d5d1dd3037f21f95395fb87ab4f9ec7f41c64232",
  "source_tree_sha256": "e7bb19c9acab80ab5c601ca5fbde08f38acf46037f1082866cbe55628dba8fdd",
  "stage_history": [
    "CREATED",
    "INTAKE_COMPLETE",
    "REQUIREMENTS_VALIDATED",
    "SOURCES_PLANNED",
    "DATA_AUDITED",
    "MODELS_PROPOSED",
    "EXPERIMENT_PLAN_VALIDATED",
    "RUNNING",
    "RUN_COMPLETED",
    "RUN_VALIDATED",
    "ROBUSTNESS_VALIDATED",
    "FINAL_CANDIDATE",
    "REJECTED"
  ],
  "status": "PASS"
}

Classification: POST_VALIDATION_DIAGNOSTIC_REPLAY. Six requirements pass derived Claim and handoff; original state REJECTED and verdict C_TARGET_VALIDATION_EVIDENCE_INSUFFICIENT remain unchanged. No model Run, code mutation, answer access or independent Validation credit. The initial handoff rejection was preserved and closed only through the prospective neutral formula-lineage repair.
