# 术语表

本文档定义九天 APU 项目中的核心术语。后续 specs、simulator 与 RTL 应优先使用这里的命名，避免同一概念多套说法。

## APU

Agent Processing Unit，Agent 处理单元。九天中的 APU 指面向 Agent 生成代码与 Agentic 逻辑工作负载的异构处理器，不等同于传统 CPU、GPU 或 NPU。

## 九天

项目与产品名。九天强调面向 Agent 原生计算的新执行层。

## Honeycomb

九天 APU 的架构代号，指由多个 Agent 集群、分布式 SRAM、显式 SPM 和 Mesh NoC 构成的蜂窝式执行结构。

## Control Plane / 控制面

由 Clawd-Super 超大核、操作系统、运行时和监管逻辑构成的执行域。控制面负责兼容性、安全、调度、I/O、异常处理、资源授权和最终副作用提交。在 Guardian-Execution 模式中，控制面可作为高熵任务协处理器按需唤醒。

## Agent Plane / Agent 执行面

由 Clawd-Agent 核组成的执行域。Agent 执行面运行生成代码片段，不默认提供 POSIX 进程语义、标准 ABI 语义或全局硬件缓存一致性。在 Guardian-Execution 模式中，它也是 Always-On 守护面，负责监听、心跳、意图分类、上下文投影和唤醒 Super 域。

## Clawd-Super

九天控制面的高性能超大核。目标是承载传统软件栈、高熵任务爆发、复杂推理、重负载计算、系统恢复和最终副作用提交。它可被视为 Strategic Coprocessor for High-Entropy Tasks。

## Clawd-Agent

九天 Agent 执行面的轻量执行核。目标是高吞吐、低控制开销、显式内存管理、可预测本地执行和低功耗常驻守护。

## Guardian-Execution

守护者-执行者模式。Clawd-Agent 作为 Always-On guardian 维持机器最低生命体征，处理监听、分类、上下文投影和短任务；Clawd-Super 作为高熵任务战略协处理器，在复杂人类任务、LLM 推理、编译、真实副作用或系统恢复时被 `WAKE_UP_SUPER` 唤醒。

## Strategic Coprocessor for High-Entropy Tasks

高熵任务战略协处理器。对 Clawd-Super 在 Guardian-Execution 模式中的定位：它不是持续在线的唯一主控，而是面向复杂、不可压缩、需要强兼容性或高性能爆发的任务按需工作。

## WAKE_UP_SUPER

Agent 域向电源管理器或 Super 域发出的唤醒语义。它表示当前任务超过 Agent 域的低功耗处理边界，需要 Super Core 上电或解门控。

## Handoff Mailbox

Agent 域与 Super 域之间的共享交接窗口。它保存任务描述符、输入引用、capability 请求、上下文投影、恢复点和唤醒原因。

## SPM

Scratchpad Memory，显式管理的本地片上存储。SPM 不做 Cache Tag 比较，不执行自动替换策略，由编译器、运行时或 Agent 生成代码显式控制。

## Cluster SRAM

单个 Agent 集群内共享的近端 SRAM。它用于集群内部任务之间的数据复用、DMA 汇聚和低延迟通信。

## Distributed Shared SRAM

分布式共享 SRAM。九天不假设一个巨大的全局 L3，而是将 SRAM 切片分布在各集群附近，使数据尽可能靠近生产者和消费者。

## APU-IR

机器指令之上的任务图中间表示。APU-IR 描述任务、内存区域、数据搬运、同步、资源预算与 capability，是 Agent 生成逻辑进入硬件前的稳定契约。

## Bare-Instruction Stream

裸机指令流。指经过 APU-IR 与运行时验证后，在 Agent 执行面上运行的低抽象指令片段。它可以绕过传统 ABI，但不能绕过 capability 与硬件安全边界。

## Capability

运行时授予任务的权限对象。Capability 定义任务可访问的内存区域、DMA 权限、最大周期数、最大内存占用和可用同步对象。

## AGE

Agent Fetch Engine，Agent 引导预取引擎。AGE 根据 APU-IR 或指令 hint 提前搬运数据，目标是把远端访问隐藏在执行之前。

## Hybrid Coherency

混合一致性。控制面保留传统硬件一致性；Agent 面默认采用显式 flush、invalidate、barrier 和 fence 管理可见性。
