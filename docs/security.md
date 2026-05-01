# 安全模型

生成代码不应意味着不受限制的硬件访问。九天把每个 Agent 任务视为一个带显式 capability 的有界执行对象，并把安全边界放在运行时、指令语义和硬件检查的交界处。

本文档定义九天 v0.1 的安全目标、威胁模型、capability 规则、异常处理和资源清理要求。任务状态细节见 `specs/task-model-v0.1.md`，地址空间规则见 `specs/memory-map-v0.1.md`。

## 安全目标

九天 v0.1 的安全目标不是证明任意 Agent 代码正确，而是确保错误或恶意生成代码的影响被限制在授权边界内。

核心目标包括：

- Agent 任务不能访问未授权 host 内存。
- Agent 任务不能越界访问自己的 SPM 或 cluster 空间。
- Agent 任务不能无限占用计算资源。
- Agent 任务不能伪造其他任务的 capability。
- Agent 任务不能阻止控制面 kill、回收或审计它。
- 一个任务 trap 后，控制面能收集足够 trace 判断失败原因。

## 信任边界

九天架构中的信任级别从高到低如下：

| 层级 | 可信度 | 说明 |
| :--- | :--- | :--- |
| 控制面固件/内核 | 最高 | 建立启动、内存保护和 runtime 根信任 |
| APU runtime | 高 | 验证任务、分配 capability、调度和回收资源 |
| APU-IR 校验器 | 高 | 拒绝格式错误、资源声明不合法或权限不足的任务 |
| Clawd-Agent 硬件检查 | 高 | 在执行时强制边界、预算和 trap |
| Agent 生成代码 | 不可信 | 即使来源可靠，也必须按不可信代码处理 |
| 外部输入数据 | 不可信 | 可能诱导生成代码走向极端路径 |

Agent 生成代码永远不应被当作控制面的一部分。即使它由本机可信 Agent 生成，也必须通过相同准入和隔离流程。

## 故障模型

Agent 代码可能错误、恶意，或者只是被过度优化。架构应假设生成代码可能：

- 访问非法地址。
- 无限循环。
- 违反同步契约。
- 越界访问本地内存。
- 发出格式错误的 DMA descriptor。
- 读写未授权 host 区域。
- 在 barrier 上等待不存在的参与者。
- 产生过量 trace 或 DMA 请求。
- 尝试覆盖输出区域之外的数据。
- 利用未初始化 SPM 数据泄露前一个任务的状态。

硬件与运行时必须尽可能把这些故障限制在任务或集群边界内。

## Capability 模型

Capability 是控制面授予 Agent 任务的访问凭证。v0.1 中 capability 至少覆盖 host 内存访问：

```json
{
  "space": "host",
  "base": 0,
  "size": 64,
  "perms": ["read", "write"]
}
```

后续版本可扩展到 cluster slice、DMA channel、MMIO window、trace buffer 和 barrier 对象。

### 检查规则

每次访问必须满足：

- 访问空间与 capability 匹配。
- 起始地址不小于 `base`。
- `addr + size` 不超过 `base + size`。
- 访问方向包含在 `perms` 中。
- 长度为非负且不超过系统配置上限。

如果任一条件不满足，任务必须 trap。运行时不能把这类错误静默修正为截断访问，因为截断会隐藏生成代码错误。

## 必需控制

九天 v0.1 至少需要以下控制：

- 面向内存、DMA 和设备访问的 capability token。
- 对 SPM、Cluster SRAM 和 DMA descriptor 的边界检查。
- 每任务 cycle budget。
- 每任务 memory budget。
- 运行时授权的代码页。
- 快速任务 kill 与清理。
- 必要时对 SPM 进行 scrub。
- barrier deadlock 检测。
- trace 预算和 trace 截断策略。

## 任务预算

每个任务必须带有预算。预算不是性能提示，而是安全边界。

| 预算 | 目的 | 违反后的行为 |
| :--- | :--- | :--- |
| cycle budget | 防止无限循环或异常长路径 | `budget_exhausted` trap |
| SPM budget | 防止越界本地访问 | `spm_oob` trap |
| cluster budget | 防止污染共享近端空间 | `cluster_oob` trap |
| DMA budget | 防止过量搬运或 descriptor 风暴 | `dma_limit` trap |
| trace budget | 防止 trace 淹没控制面 | 截断并上报 |

v0.1 模拟器至少强制 cycle、SPM、cluster 和 host capability 边界。

## Trap 与 Kill

Agent 任务出现安全违规时应进入 `trapped` 状态。trap 记录至少包含：

- 任务名。
- 指令 PC。
- trap 原因。
- 相关地址或 descriptor。
- 当前 cluster/core。
- 最近若干 trace 事件。

控制面收到 trap 后可以：

- 终止任务。
- 清理资源。
- 将错误返回上层 Agent。
- 根据策略重试。
- 禁止同一代码片段再次提交。

Kill 是控制面主动终止任务的机制。kill 必须优先于普通数据流量，不能被 Agent 域拥塞长期阻塞。

## SPM 清理

SPM 可能残留前一个任务的输入、密钥片段、中间状态或输出。任务回收时必须选择一种清理策略：

- **eager scrub**：立即清零，安全性高，成本高。
- **lazy scrub**：下一次分配前清零，吞吐较好。
- **tagged ownership**：记录所有者，未匹配所有者访问直接 trap。

v0.1 模拟器可以采用逻辑隔离；RTL 方向需要明确 scrub 或 ownership 策略。

## DMA 安全

DMA 是最危险的操作之一，因为它跨越本地和远端空间。每个 DMA descriptor 必须检查：

- 源空间和目标空间是否合法。
- 源范围和目标范围都未越界。
- host 源需要 read capability。
- host 目标需要 write capability。
- SPM/cluster 范围在任务配额内。
- 长度不为负。

DMA 完成前，任务不应消费目标数据。`dma_wait` 是显式顺序点。后续异步 DMA 模型中，未等待就读取目标区域应在验证工具或调试模式中被标记为风险行为。

## Barrier 安全

Barrier 用于同步，也可能形成 deadlock。runtime 在准入阶段应检查：

- barrier 名称已声明。
- 参与者数量明确。
- 每个参与任务最多按声明次数进入 barrier。
- 没有明显无法满足的参与关系。

运行时检查不能发现所有动态 deadlock，因此模拟器和硬件 watchdog 仍应在所有活跃任务等待且无可释放事件时报告 deadlock。

## MMIO 与外设

v0.1 不允许 Agent 任务直接任意访问 MMIO。未来如果加入 `mmio_load` 或 `mmio_store`，必须满足：

- 设备窗口由控制面显式授权。
- 访问宽度和对齐受设备规格限制。
- side effect 必须可 trace。
- 默认禁止 Agent 域配置安全关键寄存器。

## Trace 与审计

安全模型依赖 trace。每个 trap 至少应能回答：

- 哪个任务失败？
- 失败前最后执行了哪些关键操作？
- 是否是 capability、越界、预算、同步或非法指令问题？
- 输出区域是否可能被部分写入？
- 是否需要 scrub 或撤销相关 capability？

trace 本身也要受预算限制。恶意任务不能通过制造海量 trace 让控制面失去响应。

## 与模拟器的关系

模拟器是安全模型的第一条可执行规格。任何安全规则如果不能在模拟器里表达，就不应急着进入 RTL。

v0.1 模拟器应覆盖：

- host capability 违规。
- SPM/cluster 越界。
- cycle budget 耗尽。
- barrier deadlock。
- 非法指令。
- 显式 trap。
- DMA descriptor 违规。

当模拟器行为和文档冲突时，应优先修正文档或测试，让规格重新一致。
