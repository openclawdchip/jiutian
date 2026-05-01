# 架构概览

九天 APU 采用分离式执行模型。它不是把“大核”和“小核”简单堆叠在同一颗芯片上，而是把两种软件范式在硬件层面分开：控制面负责兼容、监管和系统稳定，Agent 执行面负责运行有边界、有预算、显式描述数据流的生成代码。

本文档解释九天 v0.1 的顶层架构边界。更细的指令、任务、地址空间和 trace 语义分别定义在 `specs/` 目录中。

## 设计目标

九天架构的第一目标是为 Agentic workload 定义一个可模拟、可讨论、可逐步硬化的执行层。这里的 Agentic workload 指由 Agent 生成或调度的短生命周期逻辑片段，通常具有以下特点：

- 控制流比矩阵乘法更复杂，难以完全映射到传统张量加速器。
- 任务数量多、生命周期短，启动和同步开销会显著影响吞吐。
- 数据局部性可以由生成端静态描述，但传统硬件缓存并不知道这些意图。
- 代码不一定需要稳定 ABI，也不一定需要面向人类长期维护。
- 安全边界必须由运行时和硬件共同强制，不能信任生成代码自觉守规矩。

因此，九天 v0.1 优先验证以下主张：

- Agent 任务可以通过 APU-IR 显式声明资源、数据流和同步点。
- Agent 核可以围绕 SPM、DMA、barrier 和弱一致性构建更简单的执行语义。
- 控制面可以在不参与每条指令执行的情况下，对 Agent 任务进行准入、隔离、kill、trace 和回收。
- 模拟器先建立功能正确性，再逐步加入延迟、队列、NoC 和能耗 proxy。

## 非目标

九天 v0.1 不试图一次性完成通用 CPU、GPU 或 NPU 的全部职责。以下内容不是 v0.1 的目标：

- 让所有 Agent 核运行完整 Linux、POSIX 进程或传统多用户环境。
- 在 Agent 域提供全局硬件缓存一致 SMP 语义。
- 复制既有 GPU 编程模型或把所有工作负载都转换成张量计算。
- 用传统单线程跑分定义成败。
- 在规格未稳定前直接进入复杂 RTL 大工程。

这些非目标很重要。九天要验证的是 Agent 原生执行层，而不是把旧系统完整搬进更多核心。

## 顶层分域

九天采用两个主要执行域：

- **Super Domain**：控制面与既有软件域。
- **Agent Domain**：Agent 原生执行域。

两个域可以共享某些物理内存资源，但它们不共享同一套软件假设。Super Domain 追求兼容性、精确异常和成熟工具链；Agent Domain 追求执行密度、显式数据搬运和有界并发。

```text
外部请求 / 人类软件 / Agent 平台
        |
        v
Super Domain
Linux / RTOS / runtime / scheduler / monitor
        |
        | APU-IR admission, capability, dispatch
        v
Agent Domain
Clawd-Agent cores / SPM / Cluster SRAM / DMA / barrier
        |
        v
Host memory / HBM / device windows / trace buffers
```

## 控制面

控制面运行在少量高性能超大核上。完整产品设想为 8 个 Clawd-Super 核，v0.1 模拟器可以用 1-2 个逻辑控制核建模。

控制面负责：

- 启动、固件、操作系统和基础运行时。
- 设备管理、I/O 中断、计时器和错误上报。
- Agent 任务准入控制。
- APU-IR 解析、验证和资源分配。
- capability 分配、撤销和审计。
- SPM、Cluster SRAM、DMA channel、barrier 和 trace buffer 的生命周期管理。
- Agent 任务派发、暂停、kill、回收和结果提交。
- 异常处理、任务重试策略和系统级降级。

控制面优先考虑兼容性、精确异常、成熟工具链和标准软件语义。它必须能够运行常规系统软件，并作为 Agent 执行面的可信监管者。

### Clawd-Super 的职责边界

Clawd-Super 不应承担大量 Agent 原生指令的逐条解释，也不应成为所有数据搬运的瓶颈。它的核心职责是控制和授权：

- 对任务图进行 admission，而不是执行任务图中的每个算子。
- 为 Agent 核配置可访问区域，而不是让 Agent 核随意访问全局物理地址。
- 响应异常和 trace，而不是把异常恢复逻辑分散到每个生成代码片段中。
- 管理系统状态，而不是追求在 Agentic workload 中的峰值吞吐。

## Agent 执行面

Agent 执行面运行在大量更简单的 Agent 原生核上。完整产品设想为 128 个 Clawd-Agent 物理核，每核 SMT2，合计 256 个 Agent 硬件线程。v0.1 模拟器先覆盖 8-16 个 Agent 核即可。

Agent 执行面负责：

- 短生命周期的生成逻辑。
- 高并发任务图。
- 显式 SPM 分配。
- 显式 DMA 数据搬运。
- 显式同步。
- 弱一致性或软件管理一致性。
- 面向任务的 trace 事件生成。
- capability 检查失败时快速 trap。

Agent 执行面优先考虑执行密度、可预测的本地内存行为和低开销任务分发。它不假设每个任务都拥有完整进程语义，也不假设所有内存访问都自动被硬件一致性协议协调。

### Clawd-Agent 的职责边界

Clawd-Agent 核的最小职责是执行经过准入的 Agent ISA 指令片段。它应当具备：

- 本地寄存器与简单算术逻辑。
- SPM load/store。
- Cluster SRAM load/store。
- DMA descriptor 发起能力。
- barrier arrive/wait 能力。
- flush、invalidate、fence 等显式可见性操作。
- trap、yield、halt 等控制指令。

Clawd-Agent 不需要在 v0.1 中实现复杂乱序执行、庞大分支预测器、完整虚拟内存页表遍历或全局 cache snoop。后续硬件可以在不改变软件契约的前提下增强微架构。

## Cluster 组织

完整九天架构把 128 个 Agent 核划分为 16 个 cluster，每个 cluster 包含 8 个 Agent 核。Cluster 是 Agent 域最重要的局部性边界。

每个 cluster 至少包含：

- 8 个 Clawd-Agent 核。
- 每核私有 SPM。
- 一个共享 Cluster SRAM 或 L3 slice。
- 本地 barrier/sync 单元。
- DMA 入口。
- NoC 路由端口。
- trace 汇聚点。

Cluster 的设计目标是让常见数据生产者和消费者在物理上相邻，减少跨片访问。APU-IR 应允许任务声明放置偏好，使运行时能把共享数据的任务放在同一 cluster 内。

## 任务派发路径

一次典型 Agent 任务的派发路径如下：

1. 上层 Agent 或 runtime 生成任务图。
2. 任务图降低为 APU-IR。
3. 控制面解析 APU-IR，检查格式、资源预算和 capability 请求。
4. 控制面为任务分配输入、输出、临时区域、SPM 配额、Cluster SRAM 配额、DMA channel 和 barrier。
5. 控制面选择目标 cluster 与 core。
6. Agent 指令片段被装载到可执行任务槽。
7. Clawd-Agent 执行任务，按显式指令搬运数据、同步和提交结果。
8. 任务完成或 trap 后，控制面读取状态、收集 trace、回收资源。

这个路径的关键是：控制面只在边界处介入，Agent 核在边界内部高吞吐执行。

## 以 Claude Code 类 Agent runtime 为例

已有 AI Brain 分析把 Claude Code 类源码样本消化为一个数字 Agent 运行时状态机。该类系统的核心不是 CLI 或 UI，而是：

```text
输入/事件
-> 上下文投影
-> 模型决策循环
-> ToolUse / CommandDescriptor / TaskDescriptor
-> 权限判定
-> 工具调度
-> ToolResult / transcript / compact / recovery
-> 下一轮上下文
```

九天的价值正好落在这个状态机的中后段：当模型已经产生结构化 `ToolUse` 或 `CommandDescriptor` 后，传统软件栈会把它交给 TypeScript runtime、对象系统、权限函数、调度器、文件/网络/子进程接口和大量 JSON/string 状态机处理。九天则把其中可批量化、可声明资源、可并发执行的部分降低为 APU-IR，交给 Agent Domain。

### 哪些留在 Super Domain

Claude Code 类系统中的以下部分应继续运行在 Clawd-Super 上：

- CLI、TUI、IDE bridge、远程会话、MCP transport、插件装配。
- 操作系统、文件系统、网络栈、子进程、终端 I/O。
- 模型 API 调用、token stream、长上下文管理。
- 用户确认、权限 UI、审计策略和高风险动作最终授权。
- transcript 持久化、compact summary、artifact store 和会话恢复。

这些路径需要完整 OS、成熟 runtime、复杂 I/O、用户交互和稳定 ABI。把它们强行塞进 Agent 核没有意义。

### 哪些进入 Agent Domain

Claude Code 类系统中有大量“结构化、短生命周期、分支密集、数据局部性明确”的热路径，可以进入 Agent Domain：

- 工具调用批次的 schema 检查、参数规范化和静态风险标记。
- 权限规则匹配、路径 allow/deny/ask 分类、危险命令预筛。
- 多个只读工具候选的调度排序、依赖检查和并发安全分组。
- transcript、tool_result、JSON message 的过滤、摘要、哈希、索引和去重。
- compact 前的消息裁剪、artifact pointer 生成、引用关系整理。
- 子 Agent sidechain 的结果合并、状态 delta 检查和恢复入口选择。
- 大量小型状态机：任务状态、工具状态、错误分类、retry/abort 决策。

这些工作不是大矩阵算子，也不是传统意义上的长期进程。它们更像一批 `CommandDescriptor -> ExecutionResult` 的短图任务，非常适合被控制面验证后派发给 Clawd-Agent cluster。

### 降低路径

Claude Code 类 runtime 在九天上的降低路径如下：

```text
ToolUse / CommandDescriptor
        |
        v
Super Domain runtime
schema / policy / capability admission
        |
        v
APU-IR task graph
memory regions / budget / barriers / DMA plan
        |
        v
Agent Domain cluster
SPM-local rule execution / JSON field scan / dependency grouping
        |
        v
ExecutionResult / risk flags / state delta / trace
        |
        v
Super Domain commits result or asks user
```

关键点是：Agent Domain 不直接执行任意 shell、不直接写文件、不绕过用户确认。它执行的是已经被控制面切成有边界任务的逻辑核工作。真正有副作用的动作仍由 Super Domain 根据结果提交。

### 具体一轮执行

以“模型决定读取若干文件、搜索符号、再编辑一个文件”为例：

1. Super Domain 接收用户输入，构造上下文并调用模型。
2. 模型产生多个 `ToolUse`：读文件、搜索、编辑候选。
3. Super Domain 把这些工具调用转成 `CommandDescriptor`，标注 read-only、write、permission class、路径范围和超时预算。
4. 对只读工具批次，Super Domain 生成 APU-IR：路径规则检查、glob 结果过滤、搜索结果排序、上下文预算裁剪。
5. Agent Domain 在多个 cluster 上并行处理这些短任务，使用 SPM 保存热规则表和局部字符串窗口，使用 Cluster SRAM 交换中间结果。
6. Agent Domain 返回结构化结果：允许/拒绝/需要询问、候选文件列表、摘要、风险标记、trace。
7. Super Domain 对可能写文件的动作进行最终权限确认，并调用传统文件系统完成真实写入。
8. 写入结果、diff、测试输出进入 transcript，必要时触发 compact 或 recovery。

这就是九天的实际运行方式：Super Domain 保护世界边界，Agent Domain 加速结构化决策和数据整理。

### 长期任务如何不丢记忆

Claude Code 类 Agent 的真实痛点是：任务时间一长，消息、工具结果、文件片段、测试输出和用户约束很快填满上下文窗口。compact 后如果只剩自然语言摘要，Agent 会丢失“做到哪一步”“哪些证据已验证”“哪些方案被否决”“下一步为什么要这样做”，于是开始重复读文件、重复搜索、重复规划。

九天把长任务状态从上下文窗口里剥离出来，变成一组可持续更新的 ledger：

```text
GoalLedger      用户目标 / 成功标准 / 禁止事项
PlanLedger      当前阶段 / 待办步骤 / 依赖关系
EvidenceLedger  文件、命令、测试、工具结果的证据引用
DecisionLedger  已作出的路线选择和拒绝理由
RecoveryLedger  last safe point / dirty output / rollback refs
```

Super Domain 持久化这些 ledger，Agent Domain 在每轮结束时并行整理候选更新，在每轮开始时把 ledger 投影成新的 `ContextProjection`。这样模型看到的是“当前任务恢复包”，而不是一段模糊的长摘要。

```text
长任务第 N 轮
  tool_result / diff / test / user note
        |
        v
Agent Domain: 证据去重、计划归约、风险分类、恢复点选择
        |
        v
Super Domain: 提交 ledger + transcript + artifact
        |
        v
compact 只压缩模型视图，不压缩任务真状态
        |
        v
长任务第 N+1 轮
  从 ledger 重建目标、当前阶段、已证据、下一步
```

这就是九天与 Claude Code 类 Agent 的配合方式：Agent runtime 负责生成事件和执行工具，九天负责把事件固化成可恢复任务状态，并用 Agent 核高速生成下一轮上下文投影。任务不再依赖模型“记住全部历史”，而依赖硬件辅助的结构化记忆账本。

## 资源与隔离

九天把 Agent 任务视为有界对象。每个任务必须有资源声明，至少包括：

- 可读 host 区域。
- 可写 host 区域。
- SPM 使用上限。
- Cluster SRAM 使用上限。
- DMA 权限。
- barrier 参与权限。
- 最大周期预算。
- trace 预算。

控制面负责把这些声明转化为可检查的 capability。Agent 核或本地硬件单元负责在执行时强制检查。任务越界时必须 trap，而不是继续执行。

## 与 RISC-V 的关系

九天控制面优先兼容 RISC-V 软件生态。Agent 面可以复用 RISC-V 的若干思想和编码空间，但 v0.1 的 Agent ISA 首先以 JSON 参考语义表达，目的是让模拟器和规格先稳定。后续再决定是否将 Agent ISA 固化为 RISC-V 自定义扩展、协处理器接口或独立微指令流。

这种顺序避免过早绑定二进制编码。v0.1 的核心问题不是指令如何编码，而是任务、内存、DMA、同步和安全边界是否成立。

## 为什么要分离执行面？

人类编写的软件需要兼容性、可调试性和稳定接口。Agent 生成的软件可以把数据流、生命周期和内存放置信息直接暴露给运行时与硬件。

传统 CPU 把很多不确定性留给硬件动态推断：分支、缓存、预取、一致性、上下文切换。九天的假设是：当代码由 Agent 生成时，很多信息可以在任务图和 APU-IR 中提前表达。硬件不必猜测所有意图，而可以执行已经显式化的意图。

九天把这种差异作为一条一等架构边界。

## v0.1 收敛标准

架构概览文档只有在下列条件满足时才算进入 v0.1 可实现状态：

- `specs/jiutian-apu-v0.1.md` 能从本文件追溯每个顶层概念。
- `docs/execution-model.md` 解释任务生命周期。
- `docs/memory-noc.md` 解释数据移动和一致性。
- `docs/security.md` 解释 capability、trap 和资源回收。
- 模拟器至少覆盖 SPM、Cluster SRAM、DMA、barrier、trap 和 trace。
- README 中的对外叙事不与 specs 中的实现边界冲突。
