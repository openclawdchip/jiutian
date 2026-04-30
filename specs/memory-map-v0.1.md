# 地址空间 v0.1

状态：种子草案

本文档定义九天 v0.1 的逻辑地址空间、访问权限、对齐规则和未来物理映射方向。当前模拟器使用命名空间地址，后续 RTL 可以把这些逻辑空间映射到真实物理地址。

## 1. 设计目标

九天地址空间必须满足四个目标：

- 明确区分控制面资源与 Agent 执行面资源。
- 让 Agent task 的访问权限可验证、可追踪、可撤销。
- 支持显式 SPM、Cluster SRAM 和 DMA 数据搬运。
- 为后续 MMIO、trace、debug 和 interrupt 预留稳定区域。

v0.1 不追求完整虚拟内存模型。Agent 执行面默认使用运行时授权后的逻辑地址空间。

## 2. 地址空间类别

| 空间 | 用途 | 访问者 | v0.1 状态 |
|---|---|---|---|
| `host` | 外部内存或控制面共享缓冲 | 控制面、授权 Agent task | 已实现 |
| `cluster` | Agent cluster 共享 SRAM | 同一 cluster 内 Agent task | 已实现 |
| `spm` | 每 core 本地 scratchpad | 当前 core 上的 Agent task | 已实现 |
| `mmio` | 控制寄存器与外设窗口 | 控制面，受限 Agent task | 已规划 |
| `trace` | trace buffer 与调试可观测性 | 控制面、调试工具 | 已规划 |

## 3. host 空间

`host` 空间用于输入、输出和跨执行域数据交换。它代表控制面可见的外部缓冲区。

### 访问规则

- Agent task 访问 host 空间必须具备 capability。
- 读操作要求 `read` 或 `read_write` 权限。
- 写操作要求 `write` 或 `read_write` 权限。
- DMA 源和目的都必须分别通过权限检查。
- 访问范围必须完整落在授权 region 内。

### 示例

```json
{"name": "input", "space": "host", "base": 0, "bytes": 8, "access": "read"}
```

该 region 允许 task 读取 host 地址 `[0, 8)`，不允许写入。

## 4. cluster 空间

`cluster` 空间是 Agent cluster 内共享 SRAM。它用于多个 Agent task 之间的局部数据交换。

### 典型用途

- producer/consumer 阶段交接。
- 多 task 共享 lookup table。
- DMA 中转缓冲。
- barrier 前后的中间结果保留。

### 当前规则

v0.1 模拟器允许 task 访问 cluster 空间，并检查容量边界。后续版本应加入 cluster-level capability，使 task 只能访问被授权的 cluster slice。

### 可见性

cluster 空间不自动提供跨 task 顺序保证。推荐使用：

1. producer 写入 cluster。
2. producer 执行 `flush`。
3. producer 和 consumer 在同一 barrier 同步。
4. consumer 执行 `invalidate`。
5. consumer 读取 cluster。

## 5. spm 空间

`spm` 空间是每个 Agent core 的本地 scratchpad。SPM 地址对当前 `(cluster, core)` 局部有效。

### 特性

- 无 tag。
- 无自动替换。
- 无默认硬件一致性。
- 延迟可预测。
- 适合短生命周期工作集。

### 当前规则

- v0.1 模拟器为每个 `(cluster, core)` 创建独立 SPM。
- task 在所属 core 上访问该 core 的 SPM。
- 跨 core 共享数据必须通过 cluster、host 或 DMA。

### 清理策略

后续 runtime 应提供 task 结束后的 SPM 清理策略：

- 不清理：适合性能测试。
- 清零：适合安全隔离。
- 按 region 清理：适合折中。

## 6. mmio 空间

`mmio` 空间用于控制寄存器和外设窗口。v0.1 模拟器尚未实现 MMIO 指令，但 specs 预留该类别。

规划的 MMIO 设备：

- Task doorbell。
- DMA controller。
- Barrier unit。
- Timer。
- Interrupt controller。
- Debug/trace unit。
- Serial output。

访问原则：

- 控制面拥有完整 MMIO 权限。
- Agent task 默认无 MMIO 权限。
- Agent task 如需 MMIO，必须由 capability 授权。

## 7. trace 空间

`trace` 空间用于可观测性。当前模拟器直接返回 JSON 输出，未来硬件可映射为 trace buffer。

trace 空间应支持：

- 读取事件。
- 清空事件。
- 配置过滤条件。
- 查询 overflow。
- 读取 trap buffer。

## 8. 对齐规则

v0.1 的 `load` 和 `store` 以 64-bit word 为基本单位。

推荐规则：

- 64-bit load/store 地址应 8 字节对齐。
- `dump_words` 地址应 8 字节对齐。
- DMA 地址可以 byte 对齐，但性能模型可对非对齐访问加 penalty。

当前模拟器尚未强制 8 字节对齐。后续版本可加入 `misaligned_access` trap。

## 9. 错误条件

地址空间相关错误包括：

| 错误 | 条件 |
|---|---|
| `bad_space` | 指令引用未知空间 |
| `memory_oob` | 地址越过空间容量 |
| `capability_violation` | host 访问未授权或权限不足 |
| `misaligned_access` | 后续用于非对齐 word 访问 |

## 10. 未来物理映射建议

后续硬件原型可采用以下物理区域规划：

| 区域 | 建议属性 |
|---|---|
| control DRAM window | cacheable, coherent |
| Agent host window | capability protected |
| Cluster SRAM window | low latency, local |
| SPM window | core local, non-coherent |
| MMIO window | strongly ordered |
| Trace window | read-mostly, debug only |

物理映射必须保持与 APU-IR 的逻辑空间兼容。
