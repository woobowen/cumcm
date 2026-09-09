# 004C6 继续检查：预算解释与最小公共入口反例

这是原Goal的继续检查，不是新增修订/实验授权。受审HEAD为
`fb08bfed8a9a6edf6567a41461e70f068a3b36b9`；共享实现仍为
`10e8b038d571b88ce2b7f2388da00a618c774f69`。工程未闭合、RC9未获资格、两题FAILED、
旧Validation 0/2及新增独立Validation 0均不改变。本记录不取代原报告、终局或交付回执。

## 预算解释的独立复核

新的[原生只读审核](budget_audit/REVIEW.md)完成18次读取及31项字段比较，
明确区分用户原文、执行前预登记和主Agent解释：

- 用户原文没有逐字规定“初始共享候选计为revision1”。这是主Agent在结果前采用的具体口径，
  冻结协议限制总数2，r1/r2已分别登记1/2。不能把这一选择归因成用户直接指定。
- r1零数值启动不构成退款条款；r2实际改变了准备入口的注册身份校验，不只是报告更新。
- 每题确有4次外层模型CLI调用，2次因非法Run ID返回，2次产生数值子进程。
  ledger的2不能自动返还外层CLI额度。两种计数均保留。
- checker剩余1次不能重开已FAILED的episode；Final0也不能绕过“终局失败后不追加Final”。
- 再改共享实现、真实开发回归及候选接受的完整路径需要明确新增额度。
  原任务仍允许相关中立反例/恢复收口，因此“没有任何授权内工作可做”不是正确表述。

[原生回执](budget_audit/receipt.json)、[命令摘要](budget_audit/commands.summary.json)与
[发布映射](publication.json)保存实际调用和原始日志哈希。原生审计记录生成器的一个Path拼接错误亦保留；
它不是模型/checker/Final调用。此次审核不授予新权限。

## 新执行的最小中立反例

使用现有项目原创optimization fixture，预先登记仅2次synthetic模型CLI和1次公共完成调用。
在新fixture计划写入之前省略`scenario_hash`；输入、模型、checker和公共核心均使用原有冻结实现。
选择记录中的场景身份预先按执行器的默认公式绑定，没有事后改capture或回填计划。

两个模型CLI实际exit0，分数分别4和3。公共controller依次产生五个PASS，随后：

```text
GATE_COMPATIBILITY_PORTFOLIO -> BLOCK
RC_SELECTION_SCENARIO_NOT_CAPTURE_BOUND
```

计划哈希在模型前后完全一致，真实captures均含由输入SHA派生的场景哈希；controller仍把缺省值None传给Gate。
Final账本不存在，synthetic Final0。没有访问2016/2015原始数据，没有新增其模型/checker/Final，
没有新共享功能候选。这里的“复现成功”只表示负行为被证实，不能标成修复PASS或完整Development。

实际证据：[设计](reproduction/design.json)、[三条公共命令](reproduction/commands.json)、
[controller结果](reproduction/controller_result.json)、[原始Gate trace](reproduction/gate_execution_trace.json)、
[两条真实capture](reproduction/captures/RUN-BASE-20260906/execution_capture.json)与
[第二条capture](reproduction/captures/RUN-CAND-20260906/execution_capture.json)、
[核验回执](reproduction/receipt.json)。

首次复现脚本在公共命令全部执行后，误把Gate ID当作controller摘要的顶层内容检查，顶层退出1。
[执行源码v1](reproduction/executed_source_v1.py.txt)和[该错误](reproduction/initial_wrapper_error.json)原样保留。
v2改为读取摘要所绑定的trace；已通过语法检查及对现有记录的只读核验，未重执行模型/controller。
v2的完整生成模式没有再次执行，不能把v1顶层失败改称v2完整E2E通过。

后续可在实现仍匹配原subject的checkout中用新的忽略目录复现：

```sh
.venv/bin/python evals/results/phase-004c6/continuation_001/reproduction/reproduce_missing_scenario_v2.py.txt \
  --repo-root . --output-dir .cache/pr12-rc9/new-neutral-reproduction
```

该命令会执行新的synthetic模型和controller；不是零执行的哈希检查。已有目录会被拒绝覆盖。
程序首先核对792文件的原subject映射；未来功能修复后的新subject应登记自己的正负回归，
不能修改这份历史负复现的映射或期望来伪装旧结果已通过。

## 旧固定输出与新运行的比较补项

另已补齐[2016/2015固定输出只读比较](fixed_output_comparison/REPORT.md)，可仅用公开文件离线重放。
2016在相同9.765V起点的remaining误差及当前条件预测值新旧一致；旧两起点和新六起点均值不具直接改进可比性。
2015的99行条件时窗除Run ID外相同，168行参考残差重聚合与新摘要一致。
该补项不启动模型、注册checker或Final，也不宣称已修复公共流程。

## 真正继续开发所缺的授权

需要明确新增共享功能修订次数及每题新增CLI/checker/Final总额，并保留已经发生的4次CLI。
新episode须继承006/007的失败终局，使用新root、实际Run和事前设计；旧终局/预算/Hash不变。
本报告仅描述恢复条件，不自动创建新episode或重置额度。原7小时最晚时限未被本次继续检查延长。
