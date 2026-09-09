# 当前依赖与冻结证据读取

本轮使用原有`.venv/bin/python`，Python3.11.14。2026-09-08T23:01:58Z实际核对
36个安装分发版本及Python字符串，均与RC8冻结环境一致；实际`pip check`返回
`No broken requirements found.`，exit0。未安装系统包、语言包、字体或工具链，
未改全局配置。新增配置仅两道新题目录各自的`.gitattributes`，用于保留CSV的CRLF。

下表来自本轮实际代码import与冻结环境，不是全新的安装验证：

| 范围 | 直接依赖及观察版本 |
|---|---|
| 通用CLI/合同 | PyYAML6.0.3、jsonschema4.26.0；根pyproject已有版本范围 |
| 2021采购运输模型/检查 | numpy2.4.6、scipy1.17.1、openpyxl3.1.5 |
| 2022分组统计/分类 | 上述三项及scikit-learn1.9.0 |
| 2016模型 | numpy、scipy、openpyxl；独立checker只需openpyxl及stdlib |
| 2015模型 | numpy、scipy；独立checker需numpy；下载器使用stdlib |
| Q4证书补充 | 构造器numpy/scipy；精确校验器Fraction/stdlib及openpyxl |
| 工程检查 | pytest8.4.2、ruff0.16.5；根pyproject已有dev范围 |

完整观察及传递依赖见`../qualification/environment.json`。根包声明0.2.3，既有
editable安装元数据0.1.0；本轮从仓库源代码执行，没有为对齐标签重新安装。
天文资料来自预登记NASA/JPL官方服务的理论计算记录，免费HTTP请求不等于付费API。
官方RAR的C文件提取使用既有libarchive.so.13；DOCX读取使用stdlib zip/XML。

不提供“复制缓存即可完整复现”的保证。官方原题、工作簿、NASA参考正文、绝对
机器路径及完整运行缓存保留在ignored目录；公开证据保留其hash、来源、派生数字、
代码和真实命令。相同URL将来可能返回不同字节，必须重新核验，不能静默改hash。
本轮未验证全新安装、离线重建所有外部资料、跨平台或独立宿主的数字一致性。

安全恢复顺序：

1. 读取`state/project_state.json`、当前活动计划、`../checkpoint.md`及每题的
   `terminal/decision.json`。区分终局冻结、候选包、原生CLI状态和工程CI。
2. 对照RC8subject`29cf1d7`和772文件映射，执行既有release checker。历史RC7使用
   原subject；不要用当前文件hash覆盖旧manifest。完整Git历史是历史解析前提。
3. 优先核对已保存的capture、checker、Final账本、独立audit及terminal绑定。
   已终局的新题不得重跑、重新取Final或调参。2015的READY只是保留的机器状态。
4. `scripts/finalize_fresh_c_validation.py --case-root CASE`是既有通用入口，但本轮
   2015未执行它；不得在已READY/终局的目录补调它制造事后成功回执。
5. 2021补充消耗本轮第9/9次Development数值尝试；2022仍为7/9。预算不因恢复
   重置。未来重现模型需要独立登记的新预算，不能覆盖v6或本轮首次终局。
6. 当前完整CI与候选subject已通过的CI分别查看。历史固定案例数/终局phase断言
   的修订影响受冻结的测试文件，须在未来明确的新受测subject处理；本说明不授权
   排除测试、隐藏新registry案例、修改旧hash或伪称当前CI通过。

根`qualification/RUNBOOK.md`是候选冻结时的指引；其中当时的预算与“下一步”不是
当前执行授权。当前恢复以本说明、活动计划和真实终局账本为准，不再启动本轮新题。
