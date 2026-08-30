# gatecraft — provisional static review

1. **Identity:** `Crayonnan/dsh-math-modeling-skills-Gatecraft-`, `main@54d2742032f3337f9ecb07457b196b7607f5f7a7`, 2026-08-25.
2. **Claimed goal:** five-stage modeling/paper workflow with mechanical final-document gates.
3. **Skill structure:** nine Skills, YAML rules, `docgate.py`, OCR/conversion tools, one test.
4. **State/stages:** report handoffs exist; no formal persistent state or stale graph.
5. **Capabilities:** workflow, sensitivity/diagnosis, paper lint; no general solver runtime.
6. **Evidence chain:** numbers are claimed to come from reports, but claim-strength checks are textual markers and can fail open as WARN/SKIP.
7. **Multi-Agent:** primarily one-agent orchestration; independent reviewer contract not observed.
8. **Deterministic scripts:** parameterized 13-class DocGate is the strongest observed mechanism.
9. **Tests/CI:** one DocGate test; no CI observed.
10. **License:** root MIT; reference documents/templates need separate rights review; no NOTICE.
11. **Third-party resources:** Word reference and contest/writing guides have incomplete provenance.
12. **Network/services:** SiliconFlow or compatible OCR can upload images; document converters/parsers.
13. **Danger:** external data upload, DOCX/ZIP/XML parser surface, unconfined output path. Risk `HIGH`.
14. **Conflict:** paper scope, partial fail-open gates, real-case creation history, no Run/Source/hash chain.
15. **Dynamic-test candidates:** DocGate only, with malformed/archive bomb/path/marker/page-limit negative cases.
16. **Do not adopt:** OCR/network paths, real-case guides, DocGate as evidence approval.
17. **Unknown:** subresource rights, parser resilience, test outcome, claimed release cleanliness.
18. **Reuse:** `EVALUATE`; lint as auxiliary only after redesign.
