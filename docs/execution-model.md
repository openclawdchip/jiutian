# 执行模型

九天 v0.1 的执行模型围绕一个核心边界展开：控制面负责授权和监管，Agent 执行面负责运行有界的生成代码任务。

## 执行生命周期

1. Agent 或上层系统生成任务图。
2. 任务图被降低为 APU-IR。
3. 控制面运行时验证 APU-IR 的资源声明和 capability。
4. 运行时为任务分配 SPM、Cluster SRAM、DMA channel 和同步对象。
5. APU-IR 被降低为 Agent 指令片段。
6. Clawd-Super 将任务派发到一个或多个 Clawd-Agent 核。
7. Clawd-Agent 执行指令，并通过显式 DMA、barrier、flush、invalidate 管理数据。
8. 任务完成、trap、timeout 或被 kill 后，控制面回收资源并提交结果。

## 任务边界

Agent 任务是九天 v0.1 的最小调度单元。一个任务必须声明：

- 输入区域。
- 输出区域。
- 临时区域。
- 最大周期预算。
- 最大 SPM 使用量。
- 最大 Cluster SRAM 使用量。
- DMA 权限。
- 可用 barrier。
- 异常处理策略。

任务不能隐式访问控制面内存，也不能假设任意地址可读写。

## 内存可见性

Agent 执行面默认不提供全局硬件一致性。任务之间的数据交接必须通过以下动作建立：

- `dma_copy`：显式搬运数据。
- `flush`：发布本地写入。
- `invalidate`：丢弃本地旧副本。
- `barrier`：协调多个任务的顺序点。
- `fence`：约束 DMA 与内存副作用顺序。

## 异常语义

v0.1 不追求与传统 CPU 相同的精确异常模型。模拟器与后续 RTL 至少需要支持：

- 非法指令 trap。
- capability 越界 trap。
- SPM 越界 trap。
- DMA 越界 trap。
- 周期预算耗尽 trap。
- 显式 `trap` 指令。

控制面收到异常后可以终止任务、清理 SPM、记录 trace，并选择是否重试。

## 调度原则

v0.1 调度器优先保证可解释性，不追求最优性能。默认策略：

- 每个任务绑定到一个 Agent core。
- DMA 操作以固定延迟完成。
- Barrier 按名称聚合参与者。
- 周期预算按指令递减。
- 任务完成后释放本地资源。

这个模型足以支撑早期 benchmark 和架构讨论。
