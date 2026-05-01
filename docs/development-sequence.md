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
- 长任务记忆文档定义 Agent 如何跨 compact、跨工具事件、跨恢复点保持任务连续性。

## 2. Specs 层

目标是让设计可以被实现。

- `jiutian-apu-v0.1.md` 定义总规格。
- `isa-v0.1.md` 定义最小指令集。
- `apu-ir-v0.1.md` 定义任务图 IR。
- `task-model-v0.1.md` 定义任务、capability、异常与资源预算。
- `memory-map-v0.1.md` 定义 ledger、artifact、trace 等长期记忆相关逻辑空间。
- `debug-trace-v0.1.md` 定义 ledger delta、context projection 和 recovery anchor 的可观测性。

v0.1 第一版规格的边界是“可执行参考语义”，不是完整硬件承诺。核心语义必须能落到 APU-IR、Agent ISA、任务模型、地址空间和 trace；长期记忆相关空间与事件先进入规格边界，具体实现按覆盖矩阵逐步推进。

## 3. Simulator 层

目标是让规格可以被执行。

- 先实现功能模拟器，不追求周期精确。
- 先实现单 cluster，不急于全 128 核。
- 先验证 SPM、Cluster SRAM、DMA、barrier、trap。
- 再加入 trace、benchmark harness 和多任务调度。
- 当前最小闭环是：APU-IR JSON 输入、任务准入、capability 检查、round-robin 调度、Agent ISA 执行、SPM/Cluster SRAM/host memory、同步 DMA、barrier、trap、字符串 trace 和结果导出。
- 长期记忆先保持无副作用边界：授权读取 ledger view、transcript window 和 artifact preview，生成候选 ledger delta、context projection 与 recovery anchor；提交、写文件、写 transcript 和读取大型正文仍由控制面审核。

## 4. RTL 层

目标是把稳定下来的执行语义硬化。

- 从 SPM、DMA、barrier 等边界清晰模块开始。
- 再实现 Agent core 最小流水线。
- 最后实现 cluster 与 NoC。

## 当前优先级

1. 让 v0.1 spec 可被模拟器完整覆盖。
2. 让模拟器能运行 3-5 个最小 benchmark。
3. 让长期任务记忆路径拥有最小可验证闭环：事件输入、ledger delta、context projection、恢复点。
4. 用 trace 反推 ISA 和 APU-IR 是否过度复杂。
5. 在语义稳定后再进入 RTL。

其中“完整覆盖”按阶段理解：已实现的基础 ISA、APU-IR、memory、barrier、trap 和 trace 先保持可运行；ledger、artifact、context projection 和 recovery anchor 先保持规格一致，再逐步补模拟器事件、测试和 benchmark。
