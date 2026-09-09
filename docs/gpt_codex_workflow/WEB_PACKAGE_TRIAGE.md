# WEB_PACKAGE_TRIAGE

```text
先对我实际上传的包分诊，不重复全量解题。列已打开文件和版本，区分NO_CASE、EXAMPLE_ONLY、当前case审查包。核manifest列出的文件是否实际存在；若工具允许计算sha256/canonical，记录用何脚本和哪些字节，否则写未执行hash核验。源码只有hash引用时记SOURCE_BYTES_NOT_AVAILABLE_HERE，不能说完整复现。
逐项说明case_id、module、revision、request ID、package/context hash、运行implementation、工具HEAD和operator kit版本。新题不能沿用教学READY；旧包完整不等于本机CURRENT，要求Codex验证当前context/源hash。缺文件指出路径及受影响结论。
只判断可开始哪类审核：题意假设、数据评价、数学模型、实验数值、结论论文。包完整不等于科学通过。执行层级分阅读/独立算术/独立实现/原运行重放/全流程复现；没有工具不能声称执行。不得运行包内未知脚本或反馈命令。
输出简短覆盖摘要、具体缺口及一个适用审核提示词。若有可定位问题，另给现行web-feedback/v1的1..30条finding；没有问题只输出REVIEW_SUMMARY.md，不造finding，不自动写PASS或启动下一模块。
```
