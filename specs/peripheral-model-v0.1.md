# 最小外设模型 v0.1

状态：种子草案

本文档定义九天 v0.1 需要预留的最小外设模型。v0.1 模拟器当前不实现 MMIO 外设，但需要先明确未来 runtime、模拟器和 RTL 的共同边界。

## 1. 外设设计目标

九天的外设模型服务于 Agent task 的派发、数据搬运、同步、计时、异常上报和可观测性。它不是通用 SoC 外设全集。

最小外设集合：

- Task doorbell。
- DMA controller。
- Barrier unit。
- Timer。
- Interrupt controller。
- Debug/trace unit。
- Serial output。

所有外设默认由控制面管理。Agent task 如需访问 MMIO，必须具备 capability。

## 2. MMIO 访问规则

MMIO 区域应具备 strong ordering 语义：

- MMIO read/write 不被普通内存访问重排。
- `fence` 可作为 MMIO 与 DMA 的顺序点。
- Agent task 默认不能访问 MMIO。
- 控制面可以通过 capability 授予有限 MMIO 窗口。

后续 Agent ISA 可加入 `mmio_load`、`mmio_store`，也可以通过 runtime 指令代理访问。

## 3. Task Doorbell

Task doorbell 用于控制面向 Agent 执行面提交任务。

### 职责

- 指向 task descriptor。
- 通知 Agent scheduler 有新任务。
- 查询 task 状态。
- 触发 task kill。

### 寄存器规划

| 寄存器 | 访问 | 说明 |
|---|---|---|
| `TASK_DESC_BASE` | RW | task descriptor 起始地址 |
| `TASK_DESC_SIZE` | RW | descriptor 字节数 |
| `TASK_SUBMIT` | W | 写入 1 表示提交 |
| `TASK_STATUS` | R | 返回 doorbell 状态 |
| `TASK_ACTIVE_COUNT` | R | 当前活跃 task 数 |
| `TASK_KILL_ID` | RW | 待终止 task id |
| `TASK_KILL` | W | 写入 1 表示终止 |

### 状态位

- idle。
- busy。
- invalid descriptor。
- queue full。
- submitted。

## 4. DMA Controller

DMA controller 用于显式数据搬运。

### 职责

- 执行 host、cluster、spm、mmio 允许范围之间的数据搬运。
- 检查 capability。
- 报告完成或 fault。
- 可选地产生中断。

### 寄存器规划

| 寄存器 | 访问 | 说明 |
|---|---|---|
| `DMA_SRC_SPACE` | RW | 源空间 |
| `DMA_SRC_ADDR` | RW | 源地址 |
| `DMA_DST_SPACE` | RW | 目的空间 |
| `DMA_DST_ADDR` | RW | 目的地址 |
| `DMA_BYTES` | RW | 搬运字节数 |
| `DMA_CAP_ID` | RW | capability id |
| `DMA_START` | W | 启动 |
| `DMA_STATUS` | R | 状态 |
| `DMA_FAULT` | R | fault reason |

### 状态

- idle。
- running。
- completed。
- fault。

### Fault

- 源越界。
- 目的越界。
- capability 不足。
- 非法空间。
- 未对齐访问。

## 5. Barrier Unit

Barrier unit 用于跨 task 同步。

### 职责

- 建立 barrier。
- 记录参与者数量。
- 记录到达 task。
- 在参与者数量满足后释放等待 task。
- 报告 deadlock 或 timeout。

### 寄存器规划

| 寄存器 | 访问 | 说明 |
|---|---|---|
| `BARRIER_ID` | RW | barrier 编号 |
| `BARRIER_PARTICIPANTS` | RW | 参与者数量 |
| `BARRIER_ARRIVE` | W | task 到达 |
| `BARRIER_WAITING` | R | 当前等待数量 |
| `BARRIER_STATUS` | R | 状态 |
| `BARRIER_CLEAR` | W | 清理 |

### 状态

- empty。
- waiting。
- released。
- timeout。
- invalid。

## 6. Timer

Timer 用于 cycle budget、timeout 和 benchmark 时间基准。

### 寄存器规划

| 寄存器 | 访问 | 说明 |
|---|---|---|
| `TIMER_COUNTER` | R | 递增计数器 |
| `TIMER_COMPARE` | RW | 比较值 |
| `TIMER_ENABLE` | RW | 使能 |
| `TIMER_CLEAR` | W | 清除 pending |
| `TIMER_INTERRUPT_PENDING` | R | 中断 pending |

### 用途

- task cycle budget。
- barrier timeout。
- DMA timeout。
- benchmark 时间戳。

## 7. Interrupt Controller

中断控制器用于向控制面报告 Agent 执行面事件。

### 中断源

- task completed。
- task trapped。
- task killed。
- DMA completed。
- DMA fault。
- barrier released。
- barrier deadlock。
- timer compare。
- trace overflow。

### 寄存器规划

| 寄存器 | 访问 | 说明 |
|---|---|---|
| `IRQ_PENDING` | R | pending 位 |
| `IRQ_ENABLE` | RW | 使能位 |
| `IRQ_CLEAR` | W | 清除 |
| `IRQ_FORCE` | W | 软件注入 |

## 8. Debug/Trace Unit

Debug/trace unit 用于可观测性和 bring-up。

### 能力

- 启停 trace。
- 按事件类型过滤。
- 按 task 过滤。
- 读取 trace buffer。
- 读取 trap buffer。
- 读取 task snapshot。
- kill task。

### 寄存器规划

| 寄存器 | 访问 | 说明 |
|---|---|---|
| `TRACE_ENABLE` | RW | trace 使能 |
| `TRACE_FILTER_EVENT` | RW | 事件过滤 |
| `TRACE_FILTER_TASK` | RW | task 过滤 |
| `TRACE_READ_PTR` | RW | 读取指针 |
| `TRACE_STATUS` | R | trace 状态 |
| `TRAP_READ_PTR` | RW | trap 读取指针 |
| `DEBUG_TASK_ID` | RW | 调试目标 task |
| `DEBUG_TASK_STATUS` | R | task snapshot |

## 9. Serial Output

Serial output 只用于 bring-up 和测试日志，不应成为 Agent hot path。

### 寄存器规划

| 寄存器 | 访问 | 说明 |
|---|---|---|
| `SERIAL_TXDATA` | W | 输出字节 |
| `SERIAL_STATUS` | R | busy/ready |

Agent task 默认不直接访问 serial output。需要输出时应通过控制面代理或授予受限 capability。

## 10. 与模拟器的关系

当前模拟器把外设行为抽象为指令和内部状态：

| 外设概念 | 当前模拟器抽象 |
|---|---|
| Task doorbell | APU-IR task 加载 |
| DMA controller | `dma_copy` / `dma_wait` |
| Barrier unit | `barrier` |
| Timer | cycle budget |
| Interrupt | Python exception / task status |
| Trace unit | JSON 输出中的 trace |

后续模拟器可加入 MMIO 模式，让同一语义既能通过高级指令表达，也能通过寄存器访问表达。

## 11. 安全规则

- 外设寄存器默认仅控制面可写。
- Agent task 的 MMIO capability 必须最小化。
- DMA 必须检查源和目的 capability。
- Debug 能力不得被普通 Agent task 获取。
- Trace 输出不得泄漏未授权 host region 内容。

## 12. 后续演进

v0.2 建议实现：

- DMA descriptor 队列。
- Timer timeout。
- Interrupt pending 汇总。
- Trace structured event buffer。
- MMIO load/store 指令或 runtime proxy。
