# 最小外设模型 v0.1

状态：种子草案

本文档定义九天 v0.1 需要预留的最小外设模型。v0.1 模拟器当前不实现 MMIO 外设，但 specs 应先明确未来边界。

## 1. 外设目标

九天的外设模型只服务于架构验证，不追求复刻完整 SoC。最小集合应覆盖：

- 任务派发。
- DMA。
- 计时。
- 中断。
- 调试。
- Trace。
- 基础串行输出。

## 2. Task Doorbell

Task doorbell 用于控制面向 Agent 执行面提交任务。

规划寄存器：

- `TASK_DESC_BASE`
- `TASK_DESC_SIZE`
- `TASK_SUBMIT`
- `TASK_STATUS`
- `TASK_KILL`

## 3. DMA 控制器

DMA 控制器用于显式数据搬运。

规划寄存器：

- `DMA_SRC`
- `DMA_DST`
- `DMA_BYTES`
- `DMA_CAP_ID`
- `DMA_START`
- `DMA_STATUS`

v0.1 模拟器的 `dma_copy` 可视为这些寄存器动作的抽象。

## 4. Barrier 单元

Barrier 单元用于跨 task 同步。

规划寄存器：

- `BARRIER_ID`
- `BARRIER_PARTICIPANTS`
- `BARRIER_ARRIVE`
- `BARRIER_STATUS`

## 5. Timer

Timer 用于 cycle budget、timeout 和 benchmark 时间基准。

规划寄存器：

- `TIMER_COUNTER`
- `TIMER_COMPARE`
- `TIMER_ENABLE`
- `TIMER_INTERRUPT_PENDING`

## 6. Interrupt Controller

中断控制器用于向控制面报告 Agent trap、DMA fault、timeout 和任务完成。

规划事件：

- task completed。
- task trapped。
- DMA fault。
- barrier deadlock。
- timeout。

## 7. Debug 与 Trace

调试与 trace 外设用于可观测性。

规划能力：

- trace buffer 读取。
- task 状态读取。
- trap buffer 读取。
- task kill。

## 8. Serial Output

最小串行输出仅用于 bring-up 和测试日志。Agent 执行面默认不直接访问串行输出，除非控制面授予 capability。
