# 数据手册框架

本文档定义九天 APU 数据手册应覆盖的内容。v0.1 阶段先作为目录与约束，后续随着 specs 和 RTL 完善逐步填实。

## 1. 产品概述

- 架构定位。
- 目标工作负载。
- 控制面与 Agent 执行面。
- 开源边界。

## 2. 主要特性

- Clawd-Super 控制核心。
- Clawd-Agent 执行核心。
- SPM。
- Cluster SRAM。
- Honeycomb NoC。
- 显式 DMA。
- 混合一致性。
- Capability 安全模型。

## 3. 系统框图

应至少包含：

- 控制面。
- Agent cluster。
- NoC。
- 外部内存接口。
- 调试与 trace 接口。
- 中断和异常路径。

## 4. 配置参数

- Agent cluster 数量。
- 每 cluster core 数量。
- 每 core thread 数量。
- SPM 容量。
- Cluster SRAM 容量。
- host memory 窗口。
- DMA channel 数量。
- barrier 数量。
- trace buffer 容量。

## 5. 地址空间

- host memory 区域。
- Cluster SRAM 区域。
- SPM 访问规则。
- MMIO 区域。
- 调试与 trace 区域。
- 保留区域。

## 6. 编程模型

- APU-IR。
- Agent ISA。
- 任务生命周期。
- Capability。
- 显式同步。
- 异常处理。

## 7. 中断与异常

- 控制面异常。
- Agent trap。
- DMA fault。
- barrier deadlock。
- cycle budget timeout。

## 8. 调试与 Trace

- trace 事件类别。
- trace 输出格式。
- 调试寄存器规划。
- 任务级别可观测性。

## 9. 电源与时钟

v0.1 暂不定义具体电源域，仅保留以下规划：

- 控制面时钟域。
- Agent cluster 时钟域。
- NoC 时钟域。
- 外设和调试时钟域。

## 10. 版本与兼容性

- 规格版本。
- 模拟器版本。
- APU-IR 版本。
- Trace schema 版本。
- 已知限制。
