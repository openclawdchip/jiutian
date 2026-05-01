# 发布说明

本文档记录九天项目各阶段的文档、规格、模拟器和测试变化。

## v0.1 种子阶段

### 新增能力

- 初始架构说明。
- 产品简介与 v0.1 数据手册。
- APU-IR v0.1 草案。
- Agent ISA v0.1 草案。
- 任务模型 v0.1 草案。
- 地址空间 v0.1 草案。
- 调试与 Trace v0.1 草案。
- 最小外设模型 v0.1 草案。
- 功能模拟器。
- 最小示例与单元测试。

### 已知限制

- 模拟器不是周期精确模型。
- DMA 延迟模型仍简化。
- 多 cluster 与 NoC 细节尚未稳定。
- RTL 尚处于规划阶段。

### 升级提示

任何影响 APU-IR、trace 或任务状态语义的变更，都应同步更新规格和覆盖矩阵。

## v0.1 发布检查清单

v0.1 的发布目标是形成一个可运行、可评审、可继续演进的最小架构基线。发布前应由维护者逐项确认下列内容。

### 第一版完成标准

- `README.md` 能说明项目定位、当前可运行路径、文档入口和仓库结构。
- `CONTRIBUTING.md` 能说明提交内容需要包含的问题、设计选择、替代方案和验证步骤。
- `specs/` 下 v0.1 规格入口齐全，至少覆盖架构、APU-IR、ISA、任务模型、地址空间、调试 Trace 和最小外设模型。
- `docs/` 下有快速开始、环境要求、模拟器指南、测试组织、benchmark 方法、故障排查和实现覆盖矩阵入口。
- `simulator/` 能运行最小 JSON 示例，能输出结果与可解释 trace。
- `benchmarks/` 能说明 workload 分类、baseline、指标、运行命令和结果解释要求。
- `specs/v0.1/implementation-coverage.md` 已同步记录规格与模拟器之间的已实现、部分实现、未实现和待定义项。
- `tools/` 当前没有发布必需脚本；若后续加入生成或检查工具，发布说明必须记录命令、输入、输出和失败处理方式。

### 测试命令

在仓库根目录执行：

```powershell
python simulator\jiutian_sim.py simulator\examples\copy_add.json
python simulator\jiutian_sim.py simulator\examples\copy_add.json --trace
python simulator\jiutian_sim.py simulator\examples\cluster_barrier.json --trace
python simulator\jiutian_sim.py simulator\examples\long_memory_loop.json --trace
python -m unittest discover simulator
```

通过标准：

- `copy_add.json` 输出中包含 `host_words`，地址 `8` 的结果为 `42`。
- trace 输出能看到任务调度、DMA、SPM/Cluster SRAM 访问、barrier 或异常事件。
- `long_memory_loop.json` 输出中包含 `ledger_deltas`、`recovery_anchors`、`context_projections` 和对应 `host_regions`。
- 单元测试全部通过。
- 若某项失败，发布说明应记录失败命令、失败原因、影响范围和是否阻塞 v0.1。

### 敏感字样检查

发布前必须扫描仓库文本，确认没有引入内部来源、私有路径、个人下载目录、未授权供应商标识或未清理的后台参考代号。禁用词表由发布负责人在本地或 CI 私密配置中维护，不写入仓库。

建议命令：

```powershell
$terms = $env:JIUTIAN_RELEASE_FORBIDDEN_TERMS -split ',' | Where-Object { $_ }
if (-not $terms) { throw 'JIUTIAN_RELEASE_FORBIDDEN_TERMS is empty' }
Get-ChildItem -Recurse -File |
  Where-Object { $_.FullName -notmatch '\\.git\\' } |
  Select-String -SimpleMatch -Pattern $terms
```

通过标准：

- 命令没有输出命中行。
- 若命中来自二进制、第三方公开规范镜像或历史归档，必须在发布记录中说明处置结论。
- 若命中来自项目文档、规格、示例、脚本或测试，必须先清理再发布。

### 文档、规格、模拟器和 benchmark 覆盖

- 文档覆盖：快速开始、环境、架构、执行模型、模拟器、测试组织、benchmark 方法、安全说明、故障排查和发布说明都应可从 README 或文档地图找到。
- 规格覆盖：每个 v0.1 规格文件应说明状态、范围、非目标、语义边界和与实现覆盖矩阵的关系。
- 模拟器覆盖：每个已实现 ISA 或 APU-IR 能力应至少有示例、测试或覆盖矩阵条目之一；影响 trace 的能力应能通过 `--trace` 观察。
- benchmark 覆盖：每个新增 workload 必须包含任务描述、输入规模、数据分布、九天实现路径、baseline、指标定义、运行命令和结果解释。
- 仓库卫生：发布前不提交缓存、临时日志、本地环境文件或生成中间产物；若必须保留生成物，应在对应文档说明来源和再生成方式。
