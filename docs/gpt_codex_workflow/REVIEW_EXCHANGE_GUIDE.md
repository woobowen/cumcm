# 导出、审核、保存与反馈处置

NO_CASE或本操作资料的问题没有合法case身份，只记录独立OPERATOR_REVIEW_SUMMARY.md，不用web-feedback/v1。

审查包由公共 `complete` / `review-export` 在本地生成，包含 `REVIEW.md`、`manifest.json`、`views/`。网页不能靠本机路径访问；用户需实际上传。审查前先用[分诊提示词](WEB_PACKAGE_TRIAGE.md)。工具会拒绝被改过的派生文件；附页放外层支持资料，不能塞入旧manifest却声称原hash。

版本有六种，不能互换：工具HEAD（仓库提交）、受测subject（历史资格对象）、implementation_sha256（当前运行内容集合）、operator kit版本/hash、case revision、review package/context hash。source_sha256是原件字节，view_sha256是脱敏文本；有转换时两者可能不同。仅有源码hash不支持离线复算。旧context需要本地context-verify，不能以包完整代替CURRENT。

当前 web-feedback/v1 只接受下列九个顶层字段和八个finding字段。下面是**填写模板，不能直接导入**；实际可导入的本轮实例在新演练反馈记录中，身份由真实manifest生成。不能把这里的文字占位符当成有效hash。

```json
{
  "schema_version": "web-feedback/v1",
  "case_id": "从本次manifest读取",
  "module": "M05",
  "revision": 1,
  "package_hash": "从本次manifest读取64位hash",
  "reviewer": "实际审阅来源及执行范围",
  "visible_materials": ["REVIEW.md"],
  "executed_code": false,
  "findings": [{
    "finding_id": "F-001",
    "location": "REVIEW.md",
    "description": "填实际发现",
    "reason_or_counterexample": "填有定位的理由或反例",
    "affected_scope": "字符串形式的实际影响范围",
    "suggested_verification": "填具体核验动作",
    "confidence": "MEDIUM",
    "kind": "EVIDENCE"
  }]
}
```

`visible_materials` 和 `location` 必须属于内层 manifest.files；不能写包外附页路径。revision 是正整数。finding 必须1..30条，kind为CALCULATION/EVIDENCE/SCIENTIFIC/ALTERNATIVE，confidence为HIGH/MEDIUM/LOW/UNKNOWN。JSON不夹额外字段或说明；executed_code只是来源自述，要结合脚本/输入/输出才有执行证据。

两种保存方式均可用：

1. 编辑器新建 UTF-8 `feedback/review.json`，只粘贴JSON对象，去掉所有围栏和外部解释。先用 `python -m json.tool` 检查语法；这不替代导入器合同验证。
2. 新建 UTF-8 `feedback/review.md`，完整内容只能是一个以三个反引号加json开头、独立结束围栏结尾的代码块；不能在前后加摘要、嵌套围栏或第二块。摘要保存为另一个文件。

两者复制后都由Codex核真实包索引，公共 `feedback-import` 不执行意见内容。正确意见登记PENDING_VERIFICATION；重复同内容幂等；旧源hash变化时REGISTERED_STALE，不能处置成当前意见。wrong case/hash、未知字段、命令注入会拒绝，不能修改身份或伪造索引来“兼容”。

没有问题时保存 **REVIEW_SUMMARY.md**，写实际可见文件和版本、读了/执行了什么、覆盖范围、未验证项及“本范围未发现问题”。独立支持receipt记NON_AUTHORITATIVE_NO_FINDING；不调用feedback-import，不造finding，不自动认为科学通过。

导入之后先核查，再处置。证据文件的字段恰为：finding_key、method、rationale、observations、evidence_files。method仅INDEPENDENT_RECOMPUTATION、SCIENTIFIC_ARGUMENT、EVIDENCE_GAP_ANALYSIS。核查真实反例才CONFIRMED；无依据NEEDS_EVIDENCE；被证据否定NOT_SUPPORTED；合法替代ALTERNATIVE_DESIGN。处置不会自动修复代码或改任何技术接受。

若旧case政策禁止追加，记录NATIVE_IMPORT_NOT_RUN_IMMUTABLE_SOURCE，将原反馈和核查放独立记录树。此举不允许改旧M14/Final或迁移package hash。只有允许新增反馈记录时，追加后context会变化，须导出新context；旧context保留。数值修正需合法新scope/subject，阅读附页无需重启Final。

运行命令与变量初始化见[手册](OPERATOR_PLAYBOOK.md)，回交使用[CODEX_REVIEW_FOLLOWUP](CODEX_REVIEW_FOLLOWUP.md)。
