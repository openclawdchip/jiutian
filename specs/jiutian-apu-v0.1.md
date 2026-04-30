# 九天 APU v0.1 规格草案

状态：种子草案

## 1. 目标

本规格定义一个最小 Agent 原生架构目标，用于模拟器与早期 RTL 探索。

## 2. 最小目标

- 1-2 个超大核。
- 8-16 个 Agent 核。
- 每个 Agent 核 2 个硬件线程。
- 每个 Agent 核拥有 SPM。
- 共享 Cluster SRAM。
- 显式 DMA。
- 显式 Barrier。
- 运行时强制的任务 capability。

## 3. 执行域

### Super Domain

Super Domain 运行特权软件、操作系统和 APU 运行时。它拥有任务准入、
内存 capability、调度和异常恢复的控制权。

### Agent Domain

Agent Domain 运行生成代码片段。Agent 任务不假设具备 POSIX 进程语义、
标准 ABI 语义或全局缓存一致内存语义。

## 4. 必需操作

v0.1 模型应包含以下操作：

- 本地 SPM load/store。
- Cluster SRAM load/store。
- DMA enqueue。
- DMA wait。
- Barrier arrive/wait。
- Flush。
- Invalidate。
- Yield。
- Trap。

## 5. APU-IR 契约

APU-IR 是机器指令之上的稳定接口。它必须表达：

- 任务图拓扑。
- 内存区域与访问模式。
- 放置偏好。
- 同步。
- DMA 搬运。
- 运行时 capability。
- 预期资源预算。

## 6. Benchmark 分类

- Agent 生成规则执行。
- 结构化数据转换。
- 图遍历。
- 短生命周期 JIT 片段。
- 工具调用编排逻辑。
- 非规则内存微基准。

## 7. 开放问题

- v0.1 Agent 核应采用顺序执行、弱乱序，还是类似 VLIW 的结构？
- 最小有用 SPM 容量是多少？
- 单个集群内部需要多少一致性能力？
- 为了调试生成代码，需要多精确的异常语义？
- Agentic 工作负载的第一个公平 baseline 应该是什么？
