# 环境与资产盘点

快照日期：2026-09-06。盘点只读取 allowlisted 包元数据、工具版本、Git 对象状态和已知目录是否存在；
没有输出 `pip freeze`、环境变量、认证配置、私有索引或凭据，没有遍历保留题目录，也没有安装、升级、
删除依赖或清理 cache。

## 版本面

| 项目 | 声明/可见值 | 来源 | 结论 |
|---|---|---|---|
| 正式 competition Project | `0.3.0-competition-rc7` | 根 [`VERSION`](../../VERSION)、RC7 manifest、state | 当前正式版本 |
| 正式 Skill | `0.2.0-competition-rc7` | [Skill `VERSION`](../../.agents/skills/cumcm-modeling-evidence/VERSION)、`SKILL.md` | 当前正式版本 |
| Python distribution metadata | `cumcm-skill-lab 0.2.3` | [`pyproject.toml`](../../pyproject.toml) | 与正式 competition Project 是不同版本面；同步规则 `NOT_VERIFIED` |
| 交接代码基线 | `f194c5c0e46708a4b084e63d0beab0ec05b21c09` | Git/PR #10 | 本次开始时等于 `origin/main` |

## Core 开发与检查依赖

| 依赖 | 用途 | 声明状态 | 当前可见版本 | 取得方式 | 缺失影响 | 核验方法 |
|---|---|---|---|---|---|---|
| CPython | 仓库脚本、tests、Skill CLI | `requires-python >=3.11` | `.venv` CPython `3.11.14` | `scripts/bootstrap_dev_env.sh` 可创建 `.venv` | 所有 Python 检查不可运行 | `.venv/bin/python --version` |
| PyYAML | YAML rules/manifest | `>=6.0,<7` | `6.0.3` | bootstrap 安装 `.[dev]` | 相关 validators/checkers import 失败 | `importlib.metadata.version('PyYAML')` |
| jsonschema | contracts validation | `>=4.23,<5` | `4.26.0` | 同上 | schema/strict checks 不可运行 | allowlisted metadata |
| pytest | test runner | optional dev `>=8.3,<9` | `8.4.2` | 同上 | full/targeted tests 不可运行 | allowlisted metadata |
| ruff | lint/format check | optional dev `>=0.9,<1` | `0.16.5` | 同上 | `scripts/ci.sh` 首两步不可运行 | allowlisted metadata |
| hatchling | build backend | build requirement `>=1.25` | 当前 `.venv`: `NOT_INSTALLED` | build frontend 可按 `pyproject` 建隔离环境；本轮未执行 | wheel/editable build 可能需要获取；现有源码检查不因此失效 | allowlisted metadata |

`scripts/bootstrap_dev_env.sh` 会创建/复用 `.venv` 并通过 `uv pip` 或 `pip` 安装 `.[dev]`，属于会修改
环境且可能联网的操作；它没有声明下面的 case numerical runtime 依赖。新机器应先审查网络/索引和版本
策略，不要把当前安装集合当成 lockfile。

## Case runtime 数值依赖

2017 C 的 tracked case code 静态 import 了 `numpy`、`pandas` 和 `scikit-learn`；读取 legacy `.xls`
需要 `xlrd`。formal Skill CLI 自身以标准库为主，但“能运行 CLI”不代表“能重跑具体 case”。

| 包 | 当前可见版本 | 声明状态 | 已知用途/来源 | 缺失影响 |
|---|---:|---|---|---|
| numpy | `2.4.6` | 未在 `pyproject` 声明/无 lock | 2017 pipeline 与 independent checks | 2017 数值代码不能运行 |
| pandas | `2.3.3` | 未声明/无 lock | 2017 preparation/pipeline 表格读取 | 数据准备/运行失败 |
| scikit-learn | `1.9.0` | 未声明/无 lock | Ridge、KernelRidge、Pipeline、StandardScaler | 候选模型不能运行 |
| scipy | `1.17.1` | 未直接声明；当前数值栈可见 | scikit-learn runtime stack | 数值栈可能 import/计算失败 |
| xlrd | `2.0.2` | 未在 `pyproject` 声明；历史 preparation 记录曾安装 | 读取官方 legacy `.xls` | 2017 raw workbook 不能由 pandas 读取 |
| openpyxl | `3.1.5` | 未声明；当前环境可见 | 当前仓库没有把它登记为 2017 `.xls` 必需项 | 对特定 `.xlsx` case 的影响需逐题核验 |

历史 freeze 的 environment 字段也绑定 runtime Python `3.11.14`、numpy `2.4.6`、pandas `2.3.3`、
scikit-learn `1.9.0`、xlrd `2.0.2` 与 `OFFLINE_DURING_FORMAL_RUN`，见
[`pre_run_validation_freeze.json`](../../evals/results/phase-004c4/fresh_validation/CUMCM-2017-C-VALIDATION-003F/pre_run/pre_run_validation_freeze.json)。
这证明当次环境记录，不证明新电脑可以按当前声明重建。数值依赖的可移植取得方法是
`NOT_DECLARED`；接手者不应凭猜测生成 requirements 或重跑 frozen case。

## 本地工具

| 工具 | 当前版本 | 用途 | 必需程度 | 获取/缺失影响 |
|---|---|---|---|---|
| Git | `2.43.0` | commit/blob/freeze/replay、branch delivery | 多个历史 checker 必需 | 完整 Git 安装与完整 clone；缺失/浅克隆会阻止历史验证 |
| GitHub CLI | `2.98.0` | PR/check/merge 查询与受权交付 | 本地接手非必需；远端流程需要 | 缺失或无权限不等于不能本地接手 |
| Bash | `5.2.21` | bootstrap/CI wrapper | `scripts/ci.sh` 必需 | Windows 原生 shell 需兼容环境 |
| curl | `8.5.0` | 本次只用于官方公开页面的可访问性核验 | 核心离线 checks 非必需 | 缺失不影响读代码；实时网页核验另行完成 |

当前仓库 `git rev-parse --is-shallow-repository` 为 `false`；基线、RC7 implementation 和最新历史 CI
subject commit 对象均可见。ZIP 源码包或浅克隆不能未经验证替代完整 Git 仓库，因为部分 checker 会
执行 `git show <commit>:<path>` 或核对 tree/blob。

## 数据、缓存与可交付性

| 资产类别 | 当前可见性 | 来源/哈希证据 | 是否交付 | 缺失影响与核验 |
|---|---|---|---|---|
| tracked 源码、contracts、rules、reports、derived `evals/results/` | Git tracked，可公开 clone | Git commit/tree；各 machine record 内 SHA-256 | 是，通过 Git/PR | 是只读状态、回放和交接的核心；`git fsck`/checker 核验 |
| 当前 `.venv/` | 本机存在且被 `.gitignore` 排除 | 安全包元数据见上 | 否 | 缺失时只能先读代码；重建需审查 bootstrap 和网络，不复制旧 `.venv` |
| 2018 C ignored official input cache | 精确已知目录当前存在；未遍历正文 | [`2018_input_preflight.json`](../../evals/results/phase-004c4/fresh_validation/2018_input_preflight.json)，archive SHA-256 `dc2db8a...5865e` | 否，不打包 raw | 缺失不影响已跟踪 preflight；原 archive 缺五项 named attachments，不能完成该 episode |
| 2017 C ignored official input/workspace | 精确已知目录当前存在；本轮未重读 raw | pre-run freeze；archive SHA-256 `c4461c47...758`，problem/data hashes 在 freeze 中 | 否，不打包 raw/workspace | 缺失不影响读 tracked terminal truth，但不能做 raw-dependent 重算；同题 Validation 本来也禁止重跑 |
| `.cache/upstream/` | 本机目录存在、ignored | 第三方 static-audit cache；具体内容本轮未盘点 | 否 | 缺失不影响当前 RC7 交接；不得执行其中 unaudited code |
| `.pytest_cache/`、`.ruff_cache/` | 本地 diagnostic cache | tool-generated、ignored/非权威 | 否 | 缺失只增加检查时间；不影响 truth |
| 2025 C reserve | 正式 state 为六项访问 false；本轮未做 filesystem probe | [`project_state.json`](../../state/project_state.json) | 禁止读取/交付 | 必须继续封存；缺失不构成当前阻断 |
| secrets、credential helper、token、`.env*`、个人代理/索引/配置 | 未读取、不得盘点具体值 | `.gitignore` 与安全规则 | 绝不交付 | 缺失只影响相应远端认证；不得写入文档或 Git |

Tracked derived results 可以交付，但“历史只读 replay 可通过”不等于重新数值执行。ignored raw input、
workspace 或 cache 消失后，应报告复现边界，不能用 tracked hashes 冒充仍拥有原数据。

## 获取与新电脑核验顺序

1. 从 [`rules/workflow_rules.yaml`](../../rules/workflow_rules.yaml) 的 `git_delivery` 唯一真源读取 remote，
   从授权来源完整 clone；不要只取 ZIP，并核验 origin、HEAD、non-shallow 与工作区 clean。
2. 先读 [`HANDOVER.md`](../../HANDOVER.md) 和项目启动 truth chain，不访问 raw/cache。
3. 只需读代码/状态时，不必重建 numerical runtime；CLI help 也只依赖标准库。
4. 需要 core checks 时，先审查 `scripts/bootstrap_dev_env.sh`。运行它会创建/修改 `.venv` 并安装包，
   应记录网络、版本和安装日志。
5. 需要具体 case 数值执行时，必须先为该新开发任务冻结并审查明确的 numerical dependency contract；
   当前仓库没有足够声明让接手者承诺可重复安装。
6. 任何 ignored official input 只能从授权官方来源重新获取并校验 tracked SHA-256；不要从其他队员私人
   打包或公开仓库猜测补齐。

## 明确限制

- `.venv` 不能通过复制到另一台电脑就承诺可用；绝对路径、ABI、平台和 interpreter 都可能变化。
- cache 缺失不一定影响读代码或轻量 checks，但会限制 raw-dependent replay。
- read-only historical checker 不等于重新数值运行模型。
- repository-relative layout 是当前 Skill/controller/checker 的实际依赖；单独复制 Skill 文件夹不承诺
  可用。
- 项目许可证为 `PROJECT_LICENSE_UNDECIDED`；交接不自动选择许可证。
- 本次没有新增系统包、语言包、toolchain 或配置文件；现有 `xlrd` 安装来自历史 episode，不是本轮
  安装。
