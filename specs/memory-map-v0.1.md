# 地址空间 v0.1

状态：种子草案

本文档定义九天 v0.1 的逻辑地址空间。当前模拟器使用命名空间地址，后续 RTL 可将这些区域映射到真实物理地址。

## 1. 地址空间类别

| 空间 | 用途 | 访问者 |
|---|---|---|
| `host` | 外部内存或控制面共享缓冲 | 控制面、授权 Agent task |
| `cluster` | Agent cluster 共享 SRAM | 同一 cluster 内 Agent task |
| `spm` | 每 core 本地 scratchpad | 当前 core 上的 Agent task |
| `mmio` | 控制寄存器与外设窗口 | 控制面，受限 Agent task |
| `trace` | trace buffer 与调试可观测性 | 控制面、调试工具 |

## 2. host 空间

`host` 空间用于输入、输出和跨执行域数据交换。Agent task 访问 host 空间必须具备 capability。

访问规则：

- 只读 capability 不允许写入。
- 只写 capability 不允许读取。
- DMA 源或目的必须完整落在授权范围内。

## 3. cluster 空间

`cluster` 空间是同一 Agent cluster 内共享的近端 SRAM。v0.1 模拟器默认允许同一任务访问 cluster 空间，但后续应引入 cluster-level capability。

用途：

- task 间共享中间结果。
- DMA 汇聚。
- barrier 阶段之间的数据交接。

## 4. spm 空间

`spm` 空间是每个 Agent core 的本地 scratchpad。它不参与自动缓存一致性。

规则：

- SPM 地址对当前 task 的 core 局部有效。
- 跨 core 共享数据应通过 cluster、host 或显式 DMA。
- 后续安全模型可在 task 切换时清理 SPM。

## 5. mmio 空间

v0.1 暂不实现 MMIO 指令，但为后续控制寄存器和最小外设保留该类别。

规划区域：

- DMA 控制寄存器。
- barrier 控制寄存器。
- trace 控制寄存器。
- task doorbell。
- interrupt pending。

## 6. trace 空间

trace 空间用于调试和可观测性。v0.1 模拟器直接输出 JSON trace；未来硬件可提供环形 buffer 或流式 trace 端口。

## 7. 对齐要求

v0.1 load/store 以 64-bit word 为基本单位。所有 `load`、`store` 和 word dump 地址应按 8 字节对齐。当前模拟器尚未强制对齐，后续会补充 trap。
