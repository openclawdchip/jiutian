# Trace 与波形

v0.1 优先使用 trace 描述行为。后续 RTL 阶段再补充波形约定。

## Trace 目标

trace 应回答：

- 哪个任务在何时执行了哪条指令。
- 哪些内存区域被读取或写入。
- DMA 发生在什么源和目的之间。
- barrier 是否阻塞或释放。
- trap 的原因和位置。

## 事件类型

- task_start
- instruction
- memory_load
- memory_store
- dma_copy
- dma_wait
- barrier_arrive
- barrier_release
- trap
- halt
- deadlock

## 稳定性要求

trace schema 一旦进入版本化规格，应避免破坏性变更。新增字段应保持向后兼容。
