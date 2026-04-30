# 开发顺序

九天项目按“文档先行、规格收敛、模拟器验证、RTL 固化”的路径推进。

## 1. 文档层

目标是让概念可以被讨论。

- 白皮书定义愿景。
- 架构概览定义执行域。
- 术语表统一命名。
- 执行模型定义任务生命周期。
- Memory/NoC 文档定义数据移动。
- 安全文档定义不可跨越的边界。
- Benchmark 方法定义如何验证主张。

## 2. Specs 层

目标是让设计可以被实现。

- `jiutian-apu-v0.1.md` 定义总规格。
- `isa-v0.1.md` 定义最小指令集。
- `apu-ir-v0.1.md` 定义任务图 IR。
- `task-model-v0.1.md` 定义任务、capability、异常与资源预算。

## 3. Simulator 层

目标是让规格可以被执行。

- 先实现功能模拟器，不追求周期精确。
- 先实现单 cluster，不急于全 128 核。
- 先验证 SPM、Cluster SRAM、DMA、barrier、trap。
- 再加入 trace、benchmark harness 和多任务调度。

## 4. RTL 层

目标是把稳定下来的执行语义硬化。

- 从 SPM、DMA、barrier 等边界清晰模块开始。
- 再实现 Agent core 最小流水线。
- 最后实现 cluster 与 NoC。

## 当前优先级

1. 让 v0.1 spec 可被模拟器完整覆盖。
2. 让模拟器能运行 3-5 个最小 benchmark。
3. 用 trace 反推 ISA 和 APU-IR 是否过度复杂。
4. 在语义稳定后再进入 RTL。
