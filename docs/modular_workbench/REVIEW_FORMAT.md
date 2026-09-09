# 审查与反馈格式

`complete`读取prepare生成的`work-report.template.json`同结构报告。Codex填真实动作、引用、
核验、负结果、科学支持范围；case/module/request/revision/scope必须与当前请求一致。
报告中的artifact paths必须为case内安全相对路径；不得填凭据、隐藏认证文件或整个缓存。

审查包由REVIEW.md、manifest.json和必要views组成。manifest分别保留原文件hash与脱敏视图hash、
变换、实现身份、缺失项及实际生成时间。大文件或二进制材料需提供明确的精简派生文本，
缺失内容如实登记。上传行为由用户决定，CLI只生成本地目录或ZIP。

回传JSON示例（身份字段从实际manifest复制；本示例不是实际反馈）：

```json
{
  "schema_version": "web-feedback/v1",
  "case_id": "DEMO-WATER",
  "module": "M05",
  "revision": 1,
  "package_hash": "COPY_ACTUAL_PACKAGE_HASH",
  "reviewer": "网页审阅者（用户实际上传）",
  "visible_materials": ["REVIEW.md"],
  "executed_code": false,
  "findings": [{
    "finding_id": "F-001",
    "location": "REVIEW.md",
    "description": "缺失值处理后的样本分母未解释",
    "reason_or_counterexample": "报告列出一条剔除记录，但均值分母仍写原样本数。",
    "affected_scope": "REQ-A的均值及下游比较",
    "suggested_verification": "独立统计有效样本和求和，核对公式分母。",
    "confidence": "MEDIUM",
    "kind": "CALCULATION"
  }]
}
```

也可使用仅包含一个json代码块的Markdown。ZIP、可执行文件、额外字段、错身份、错hash、
越界路径、凭据、超长或畸形内容均拒绝。导入结果只为PENDING_VERIFICATION或STALE；
重复意见幂等，既有ID的不同内容冲突。网页给出的executed_code是来源自述，不是执行证明。

处置证据JSON包含 finding_key、method、rationale、observations、evidence_files。
method为INDEPENDENT_RECOMPUTATION、SCIENTIFIC_ARGUMENT或EVIDENCE_GAP_ANALYSIS。
CONFIRMED需实际复算或论证；缺证据不能确认反例。NEEDS_EVIDENCE、NOT_SUPPORTED和
ALTERNATIVE_DESIGN分别保留缺口、不支持理由和待验证设计。任何处置不触发正式Gate或后续模块。
