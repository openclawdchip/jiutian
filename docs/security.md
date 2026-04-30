# 安全模型

生成代码不应意味着不受限制的硬件访问。

九天把每个 Agent 任务视为一个带显式 capability 的有界执行对象。

## 必需控制

- 面向内存、DMA 和设备访问的 capability token。
- 对 SPM、Cluster SRAM 和 DMA descriptor 的边界检查。
- 每任务 cycle budget。
- 每任务 memory budget。
- 运行时授权的代码页。
- 快速任务 kill 与清理。
- 必要时对 SPM 进行 scrub。

## 故障模型

Agent 代码可能错误、恶意，或者只是被过度优化。架构应假设生成代码可能：

- 访问非法地址。
- 无限循环。
- 违反同步契约。
- 越界访问本地内存。
- 发出格式错误的 DMA descriptor。

硬件与运行时必须尽可能把这些故障限制在任务或集群边界内。
