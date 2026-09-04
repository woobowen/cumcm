# C-Target Batch Official Input Registration

Status: `INPUTS_REGISTERED_ANSWERS_SEALED`
Batch: `C-TARGET-BATCH-001`
Formal Skill: `0.2.0-competition-rc3`
Input registration artifact: `evals/results/phase-004c-c-batch/input_registration.json`
Input registration SHA-256: `ddde33d63548bc39c3594aec76840683a47d3bb07a9810c9b4240bd75dda9f2f`

## Registered cases

| Position | Case | Official title verified from C problem | Archive SHA-256 | Problem SHA-256 | Data files | Answer | Strict eligibility |
|---:|---|---|---|---|---:|---|---|
| 1 | `CUMCM-2022-C-DEVELOPMENT-BATCH-001` | 古代玻璃制品的成分分析与鉴别 | `c27eb1b665f070341e134f5dc13bb2af469230424ff2eedabf594eee708bfee4` | `573ee0f2865af13f8b2fbd12dab7f8efa68cf61ec6b8edf132a2120424480dbd` | 1 | `SEALED` | `ELIGIBLE_MODEL_PRIOR_UNVERIFIABLE` |
| 2 | `CUMCM-2021-C-DEVELOPMENT-BATCH-002` | 生产企业原材料的订购与运输 | `3391573f546fce4511e9a99c24c386e28203d8fee3d29bb2dccada5921cefe7b` | `4a592c20adad12d4f0678a783bfb47995bda03b1c7484adf254d96327f534056` | 4 | `SEALED` | `ELIGIBLE_MODEL_PRIOR_UNVERIFIABLE` |
| 3 | `CUMCM-2020-C-DEVELOPMENT-BATCH-003` | 中小微企业的信贷决策 | `04ea454f8a1559dac2dc5b7cf599bceb10cd6a0b6f2df55a35ca4450814239dd` | `d16b3e230eb616ac88ae5d5c172a4434d1814322d158e975c0959c95d49bb67d` | 3 | `SEALED` | `ELIGIBLE_MODEL_PRIOR_UNVERIFIABLE` |

The machine artifact contains the official page URL hash, archive URL hash, archive filename,
archive hash, every extracted C-file name/hash/MIME/size, and retrieval time. Raw archives, problem
statements, attachments, and page bodies remain ignored and untracked.

## Acquisition and extraction controls

- All three archives were retrieved from the predeclared official organizer endpoints.
- Each archive passed SHA-256 and `application/x-rar` type capture before extraction.
- Only the `C/` member subtree was extracted for 2021 and 2020. For 2022, only `C题.rar` was
  extracted from the outer archive, then its two C-only members were extracted.
- Path traversal and non-regular archive members were rejected by the local extraction procedure.
- The three case workspaces and search logs are isolated beneath their own ignored case roots.
- No solution, commentary, awarded paper, post-contest analysis, or third-party code was accessed.

## 2020 C contamination and fallback decision

The previously cached 2020 archive has the same SHA-256 as the fresh official download. Metadata
inspection found only an `A/` extraction in the prior 2020 A raw workspace; tracked-repository
search found no prior 2020 C registration, case, result, or model artifact. This supports
`COLOCATED_ARCHIVE_PREVIOUSLY_USED_FOR_2020A_NO_C_CONTENT_EXPOSURE_FOUND`, not proof of absent model
prior knowledge. Therefore 2020 C remains eligible as Development with
`MODEL_PRIOR_EXPOSURE_UNVERIFIABLE`, and the 2019 C fallback is `NOT_ACTIVATED` before any candidate
result.

## Boundary

Registration is not a modeling result and does not satisfy the batch pre-run freeze gate. No case
worker may start until `batch_pre_run_freeze.json` is checked, committed, pushed, and verified at
the designated remote SHA.
