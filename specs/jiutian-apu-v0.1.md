# 九天 APU v0.1 规格草案

状态：种子草案

## 1. 目标

本规格定义一个最小 Agent 原生架构目标，用于模拟器与早期 RTL 探索。

## 2. 最小目标

- 1-2 个超大核。
- 8-16 个 Agent 核。
- Guardian-Execution 语义：Agent 核常驻守护，超大核按需唤醒。
- `WAKE_UP_SUPER` 与 handoff mailbox 的最小语义。
- 每个 Agent 核 2 个硬件线程。
- 每个 Agent 核拥有 64KB-256KB SPM。
- 每个 Agent cluster 拥有 512KB-4MB Cluster SRAM。
- 显式 DMA。
- 显式 Barrier。
- 运行时强制的任务 capability。
- 功能模拟器覆盖所有 v0.1 指令语义。
- 长任务记忆投影语义：ledger delta、artifact preview、context projection 和 recovery anchor。

## 3. 执行域

### Super Domain

Super Domain 运行特权软件、操作系统和 APU 运行时。它拥有任务准入、
内存 capability、调度和异常恢复的控制权。

在 Guardian-Execution 模式下，Super Domain 被定义为高熵任务战略协处理器。它可以处于 clock-gated 或 power-gated 状态，由 Agent Domain 在需要 LLM 推理、复杂 OS 路径、大规模编译、重度感知处理、真实外部副作用或系统级恢复时唤醒。

### Agent Domain

Agent Domain 运行生成代码片段。Agent 任务不假设具备 POSIX 进程语义、
标准 ABI 语义或全局缓存一致内存语义。

Agent Domain 同时承担 Always-On guard 职责：监听输入、维护心跳、执行轻量意图分类、整理上下文投影、生成候选 ledger delta，并在请求超过自身权限或计算能力时发起 `WAKE_UP_SUPER`。

## 3.1 Guardian-Execution 协议

v0.1 定义以下语义对象，具体 MMIO 地址和寄存器编码留给后续 RTL：

- `WAKE_UP_SUPER`：Agent Domain 发出的高熵任务唤醒请求。
- `SUPER_READY`：Super Domain 完成上电或解门控后的就绪确认。
- `HANDOFF_MAILBOX`：共享任务交接窗口，保存 task descriptor、input refs、capability request、context projection 和 recovery anchor。
- `SUPER_SLEEP_REQUEST`：Super Domain 完成任务后请求重新进入低功耗状态。
- `GUARD_HEARTBEAT`：Agent Domain 常驻写入的生命体征、队列深度和异常摘要。
- `WAKE_REASON`：用于 trace、benchmark 和能耗模型的唤醒原因。

高熵任务至少包括：自然语言深推理、大规模编译、复杂传统软件路径、重度感知处理、真实外部副作用提交和 Agent Domain 不可恢复 trap。

## 4. 必需操作

v0.1 模型应包含以下操作，详细语义见 `isa-v0.1.md`：

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

APU-IR 是机器指令之上的稳定接口，详细语义见 `apu-ir-v0.1.md`。它必须表达：

- 任务图拓扑。
- 内存区域与访问模式。
- 放置偏好。
- 同步。
- DMA 搬运。
- 运行时 capability。
- 预期资源预算。
- 长期记忆任务的输入引用、输出 delta、上下文预算和恢复点候选。

## 6. 长期任务记忆

九天 v0.1 把 Claude Code 类 Agent 的长任务记忆视为一等工作负载。目标不是让 Agent Domain 拥有系统所有权，而是让它高吞吐处理无副作用的状态提取和投影任务。

长期任务记忆路径包含：

- `GoalLedger`：目标、成功标准、禁止事项。
- `PlanLedger`：阶段、已完成步骤、待办步骤。
- `EvidenceLedger`：文件、trace、artifact、测试和工具结果引用。
- `DecisionLedger`：关键判断和被拒绝路径。
- `RecoveryLedger`：最近安全恢复点和回滚依据。
- `ContextProjection`：下一轮模型可见上下文。

分工规则：

- Super Domain 维护 transcript、artifact 正文、已提交 ledger 和最终权限。
- Agent Domain 读取授权视图，生成候选 delta、摘要、排序、引用和恢复点。
- compact 只压缩 `ContextProjection`，不压缩已提交 ledger。
- 任意关键 projection 判断都应能回指 evidence 或 ledger。

## 7. Benchmark 分类

- Agent 生成规则执行。
- 结构化数据转换。
- 图遍历。
- 短生命周期 JIT 片段。
- 工具调用编排逻辑。
- 非规则内存微基准。
- 长任务记忆、compact 和断点恢复。

## 8. 开放问题

- v0.1 Agent 核应采用顺序执行、弱乱序，还是类似 VLIW 的结构？
- 最小有用 SPM 容量是多少？
- 单个集群内部需要多少一致性能力？
- 为了调试生成代码，需要多精确的异常语义？
- Agentic 工作负载的第一个公平 baseline 应该是什么？
- 长期记忆 ledger 的最小稳定 schema 应该收敛到 JSON、CBOR，还是更硬件友好的定长记录？
- compact 后的恢复准确率应如何定义可复现实验？
- `WAKE_UP_SUPER` 的最小门控延迟、mailbox 格式和功耗 proxy 应如何建模？
- Agent 域的意图分类单元应采用微型 NPU、硬化匹配电路，还是纯 runtime 规则表？

## 9. v0.1 文件边界

- `isa-v0.1.md`：定义功能模拟器必须支持的最小指令集。
- `apu-ir-v0.1.md`：定义任务图、内存区域、DMA 与同步描述格式。
- `task-model-v0.1.md`：定义任务、capability、资源预算和异常。
- `../simulator/`：实现上述规格的可执行参考模型。
