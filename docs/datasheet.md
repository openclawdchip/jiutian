# 九天 APU v0.1 数据手册

状态：v0.1 种子版  
适用对象：架构研究、模拟器开发、运行时设计、后续 RTL 规划

本文档是九天 APU 的 v0.1 数据手册。它描述当前架构模型、执行域、存储系统、任务模型、调试 trace、最小外设规划和实现边界。v0.1 不是最终硬件承诺，而是用于规格收敛、模拟器验证和早期 RTL 拆分的共同技术基线。

## 1. 产品概述

九天 APU 是面向 Agent 生成代码的开源 Agent 原生处理器架构。它的核心目标不是替代传统 CPU、GPU 或 NPU，而是为 Agentic workload 建立一个新的执行层。

Agentic workload 具有以下特征：

- 代码片段由 Agent 动态生成或重写。
- 任务生命周期短，经常只执行一次或少数几次。
- 控制流分支复杂，难以映射为规整张量计算。
- 访存模式碎片化，传统 cache 命中率和一致性开销不可预测。
- 并发任务数量多，但单个任务不一定需要复杂 OoO 执行。
- 运行时需要严格安全边界，防止生成代码越权访问系统资源。

九天采用异构双平面架构：

- Agent 执行面负责低功耗常驻、环境监听、任务队列维护、上下文投影，以及运行经过 APU-IR 描述和授权的生成代码片段。
- 控制面负责按需唤醒后的操作系统、I/O、LLM 推理、编译、调度、安全、调试、异常处理和最终副作用提交。

这种分离让人类软件继续运行在兼容域中，同时让 Agent 生成代码获得更低抽象、更高执行密度和更可控的数据搬运路径。

v0.1 数据手册采用 Guardian-Execution（守护者-执行者）模式作为功耗与协作基线：Clawd-Agent 是 Always-On guardian，Clawd-Super 是 Strategic Coprocessor for High-Entropy Tasks。

## 2. 主要特性

### 2.1 控制面

控制面由少量高性能 Clawd-Super 核组成。v0.1 数据手册不强制定义具体微架构，但定义其职责：

- 启动系统。
- 运行操作系统或轻量 runtime。
- 被 Agent 域通过 `WAKE_UP_SUPER` 按需唤醒。
- 执行 LLM 推理、大规模编译、重度感知处理和复杂人类软件路径。
- 管理 Agent task admission。
- 分配 capability。
- 配置 DMA、barrier、trace 和 task doorbell。
- 处理中断、trap、timeout 和 kill。
- 执行真实外部副作用的最终提交。
- 汇总 benchmark 和 trace 结果。
- 任务完成后请求 clock-gated 或 power-gated 休眠。

控制面保留传统软件语义，是系统可靠性的锚点，但不再被假设为始终满功耗在线的主控核。

### 2.2 Agent 执行面

Agent 执行面由多个 Clawd-Agent 核组成。每个核运行轻量 Agent ISA 指令，并通过显式 SPM、Cluster SRAM、DMA 和 barrier 与其他任务协同。

v0.1 的最小模型支持：

- Always-On guard 语义。
- 低成本监听、心跳和意图分类。
- `WAKE_UP_SUPER` 唤醒请求和 handoff mailbox 语义。
- 多 task round-robin 调度。
- 每 core SPM。
- 每 cluster 共享 SRAM。
- host memory capability 检查。
- 同步完成的 DMA copy。
- barrier 阻塞、释放和 deadlock 检测。
- trace 输出。
- cycle budget 检查。

Agent 执行面默认不提供全局硬件缓存一致性。

### 2.3 Guardian-Execution 唤醒接口

v0.1 先定义唤醒接口的语义，不绑定最终寄存器编码：

| 信号或窗口 | 方向 | 语义 |
|---|---|---|
| `WAKE_UP_SUPER` | Agent -> Power/Super | 高熵任务唤醒请求 |
| `SUPER_READY` | Super -> Agent | Super 域已恢复并可读取 handoff |
| `HANDOFF_MAILBOX` | Shared | 任务指针、输入引用、capability 请求、上下文投影和恢复点 |
| `SUPER_SLEEP_REQUEST` | Super -> Power/Agent | Super 域完成任务并请求回眠 |
| `GUARD_HEARTBEAT` | Agent -> Trace/Power | Agent 常驻生命体征、队列深度和异常摘要 |
| `WAKE_REASON` | Agent/Super -> Trace | 唤醒原因，用于功耗和调度分析 |

### 2.4 APU-IR

APU-IR 是 Agent 生成逻辑进入硬件前的任务图描述。它不是传统源代码格式，而是运行时可验证的执行契约。

APU-IR 至少描述：

- memory region。
- task 列表。
- placement。
- capability。
- budget。
- barrier。
- Agent ISA program。
- host 初始化和结果 dump。

### 2.5 显式 SPM

SPM 是 Agent core 本地 scratchpad。它不做 tag 比较，不执行自动替换策略，不参与默认硬件一致性。

SPM 的优势：

- 延迟可预测。
- 访问路径短。
- 编译器和运行时可显式安排数据生命周期。
- 易于做 task 级隔离和清理。

### 2.6 Cluster SRAM

Cluster SRAM 是同一 Agent cluster 内的共享近端 SRAM，用于 task 间交换数据和复用中间结果。

典型用途：

- producer/consumer 阶段交接。
- 多 task 共享 lookup table。
- DMA 汇聚缓冲。
- barrier 阶段之间的数据暂存。

### 2.7 显式 DMA

DMA 用于在 host、cluster 和 spm 空间之间搬运数据。v0.1 中 `dma_copy` 可按同步完成建模，未来版本将加入异步队列、延迟、带宽和 fault 语义。

DMA 操作必须经过 capability 检查。

### 2.8 混合一致性

九天采用混合一致性：

- 控制面可以维持传统硬件一致性。
- Agent 执行面默认使用显式 `flush`、`invalidate`、`fence`、`barrier` 管理可见性。

这种模型减少 Agent 域内的隐式协议开销，也让 trace 更容易解释。

## 3. 系统逻辑框图

```text
Agent 常驻守护面
  Clawd-Agent cores
  Listen / Heartbeat / Intent / Projection
        |
        | WAKE_UP_SUPER / HANDOFF_MAILBOX
        v
控制面 / 高熵任务协处理面
  Clawd-Super cores
  OS / Runtime / LLM / Compiler / Safety
        |
        | task admission / capability / dispatch
        v
APU-IR Runtime
        |
        | lowered Agent ISA
        v
Agent 执行面
  Cluster 0
    Core 0..N
    SPM per core
    Cluster SRAM
  Cluster 1
    ...
        |
        v
Honeycomb NoC / DMA / Trace / Interrupt
        |
        v
Host Memory / External Memory
```

## 4. 配置参数

v0.1 模拟器使用 APU-IR 顶层 `config` 字段描述运行实例。

| 参数 | 含义 | 当前默认 | 说明 |
|---|---|---:|---|
| `host_bytes` | host memory 字节数 | 4096 | 用于输入/输出缓冲 |
| `cluster_bytes` | Cluster SRAM 字节数 | 4096 | 当前模拟器为单 cluster 建模 |
| `spm_bytes` | 每 core SPM 字节数 | 65536 | 每个 `(cluster, core)` 独立 |

后续硬件配置还应包括：

- cluster 数量。
- 每 cluster core 数量。
- 每 core hardware thread 数量。
- DMA channel 数量。
- barrier 数量。
- trace buffer 容量。
- task queue 深度。
- interrupt source 数量。

## 5. 地址空间

九天 v0.1 使用命名空间地址，而不是固定物理地址。

| 空间 | 说明 | 当前状态 |
|---|---|---|
| `host` | 控制面与 Agent task 共享的外部缓冲 | 已实现 |
| `cluster` | Agent cluster 共享 SRAM | 已实现 |
| `spm` | 每 core 本地 scratchpad | 已实现 |
| `mmio` | 控制寄存器和外设窗口 | 已规划 |
| `trace` | trace buffer 与调试窗口 | 已规划 |

所有 host 访问必须通过 capability。SPM 和 cluster 访问当前由容量边界保护，后续会加入更细粒度授权。

## 6. Agent ISA v0.1 摘要

v0.1 ISA 是模拟器参考语义，不是最终硬件编码。

| 类别 | 指令 | 状态 |
|---|---|---|
| 算术 | `li`、`add`、`sub` | 已实现 |
| 控制流 | `label`、`jmp`、`beqz` | 已实现 |
| 内存 | `load`、`store` | 已实现 |
| DMA | `dma_copy`、`dma_wait` | 部分实现 |
| 同步 | `barrier` | 已实现 |
| 一致性 | `flush`、`invalidate`、`fence` | trace 实现 |
| 异常 | `trap` | 已实现 |
| 结束 | `halt` | 已实现 |

## 7. Task 模型

Task 是九天 v0.1 的最小调度、授权和异常边界。

每个 task 包含：

- `name`。
- `placement`。
- `capabilities`。
- `budget`。
- `program`。
- 运行状态。

状态机：

```text
created -> admitted -> running -> completed
                         |
                         -> waiting -> running
                         -> trapped
                         -> timed_out
                         -> killed
```

当前模拟器直接从 APU-IR 加载 task，并进入 running。后续 runtime 会显式区分 created、admitted 和 dispatched。

## 8. Capability 模型

Capability 定义 task 可访问的外部资源。v0.1 主要保护 host memory。

```json
{
  "name": "input",
  "space": "host",
  "base": 0,
  "bytes": 8,
  "access": "read"
}
```

访问规则：

- `read` 允许 load 或 DMA 读取。
- `write` 允许 store 或 DMA 写入。
- `read_write` 允许读写。
- 访问范围必须完整落在 `[base, base + bytes)`。

违反 capability 会触发 `capability_violation`。

## 9. 同步模型

Barrier 是 v0.1 的主要同步机制。

APU-IR 中声明：

```json
{"name": "stage0", "participants": 2}
```

指令中使用：

```json
{"op": "barrier", "name": "stage0"}
```

语义：

1. task 到达 barrier 后进入 waiting。
2. 调度器记录该 barrier 的到达者。
3. 到达者数量达到 `participants` 后，释放所有等待 task。
4. 被释放 task 的 PC 推进到 barrier 后一条指令。
5. 如果所有活跃 task 都在 waiting 且没有 barrier 可释放，报告 `deadlock`。

## 10. DMA 模型

当前 DMA 是同步拷贝模型：

```json
{
  "op": "dma_copy",
  "src_space": "host",
  "src": 0,
  "dst_space": "spm",
  "dst": 0,
  "bytes": 8
}
```

语义：

- 检查源 capability。
- 检查目的 capability。
- 检查源/目的空间边界。
- 执行 byte copy。
- 写入 trace。

`dma_wait` 当前立即完成。后续版本会加入：

- DMA descriptor。
- 队列深度。
- 固定延迟模型。
- 带宽模型。
- fault 状态。
- 中断或 completion event。

## 11. Trace 与调试

v0.1 模拟器输出字符串 trace。trace 记录：

- task start。
- 每条指令。
- DMA copy。
- DMA wait。
- flush/invalidate/fence。
- barrier arrive/release。
- task completed。
- trap 和 scheduler trap。

未来 trace 会升级为结构化 JSON event，并加入 cycle、task、core、event、detail 字段。

## 12. 最小外设规划

v0.1 暂不实现 MMIO，但保留以下外设模型：

- Task doorbell。
- DMA controller。
- Barrier unit。
- Timer。
- Interrupt controller。
- Debug/trace unit。
- Serial output。

这些外设的具体寄存器规划见 `specs/peripheral-model-v0.1.md`。

## 13. 异常与错误

当前定义的异常：

| reason | 说明 |
|---|---|
| `bad_opcode` | 未知指令 |
| `bad_register` | 非法寄存器 |
| `bad_space` | 非法地址空间 |
| `memory_oob` | 访问越界 |
| `capability_violation` | capability 违规 |
| `cycle_budget_exhausted` | 周期预算耗尽 |
| `deadlock` | barrier 等待无法释放 |
| `explicit_trap` | task 显式 trap |

异常处理原则：

- 当前 task 标记为 trapped。
- 调度器记录 trace。
- 后续 runtime 决定是否 kill、retry 或上报控制面。

## 14. 当前实现边界

已实现：

- APU-IR JSON 输入。
- host/spm/cluster memory。
- capability 检查。
- round-robin 调度。
- barrier 阻塞释放。
- deadlock 检测。
- 单元测试。

未实现：

- 异步 DMA。
- 多 cluster NoC 延迟。
- MMIO 外设。
- 结构化 trace schema。
- RTL 参数生成。
- 二进制 ISA 编码。

## 15. 合规和版本策略

v0.1 阶段所有规格均为草案。任何影响以下内容的变更都必须同步更新文档和测试：

- APU-IR 字段。
- Agent ISA 指令语义。
- Task 状态机。
- Capability 检查规则。
- Trace schema。
- 模拟器 CLI 输出。

## 16. 快速验证

运行最小示例：

```powershell
python simulator\jiutian_sim.py simulator\examples\copy_add.json
```

运行同步示例：

```powershell
python simulator\jiutian_sim.py simulator\examples\cluster_barrier.json --trace
```

运行测试：

```powershell
python -m unittest discover simulator
```
