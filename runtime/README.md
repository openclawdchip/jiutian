# 运行时

本目录将存放 Agent 运行时与 APU-IR 原型。

运行时职责：

- 接收生成的任务图。
- 校验 capability。
- 分配 SPM 与 Cluster SRAM 区域。
- 调度 Agent 任务。
- 编程 DMA descriptor。
- 处理 trap、timeout 与任务清理。

APU-IR 应描述生成程序需要什么，而不是强迫它伪装成传统人类软件。
