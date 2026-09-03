<!-- GENERATED FILE — DO NOT EDIT -->
# Phase 002D-R2A-C1/C2 native Subagent audits

| Role | Read-only | Peer visibility | Output hash | Findings | Blockers | Verdict |
| --- | --- | --- | --- | ---: | ---: | --- |
| historical_freeze_semantics_auditor | true | NONE | 7c099ede53656ee8d0c8dce46af67bb717e57240561450c5fb1846e24d2d5a96 | 3 | 2 | RETEST |
| schema_version_compatibility_auditor | true | NONE | d568275c87e73b256d07d3340a9c633e92de1765a3476325635a211d69090d09 | 3 | 0 | RETEST |
| candidate_binding_prosecutor | true | NONE | 4b1a866d1d644f60b35c71a57fb68e486643c42b107253e71431b78cf9fc27b1 | 6 | 3 | ABSTAIN |
| candidate_binding_prosecutor | true | NONE | 3a55c2d234fd0dd553d0187620c3b91f99fa6bda919650f60db7315c83218afd | 6 | 4 | FAIL |
| final_shadow_authorization_auditor | true | FROZEN_PREDECESSORS_ONLY | 601f4b8a57aa2d08869906c8d6ce8454cebc4bacbf0fac4bdc616cbf41af5d10 | 1 | 1 | FAIL |
| candidate_binding_prosecutor | true | NONE | 7962f021aeff32540836b4b0529900a22bbbfe0c66b7f70fd474aeba6fdf6e26 | 0 | 0 | PASS |
| final_shadow_authorization_auditor | true | FROZEN_PREDECESSORS_ONLY | e33c59a489bbce09a4984c92a34812afc2d43c6ba10ee0c952f63178eb8ae125 | 0 | 0 | PASS |

All seven recorded native audit roles were identity-separated and read-only. They used no web,
MCP, external API, nested Codex, majority vote, or human technical override. Earlier RETEST,
ABSTAIN, and FAIL outputs remain preserved and are not relabeled as PASS.
