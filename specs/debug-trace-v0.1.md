# 调试与 Trace v0.1

状态：种子草案

本文档定义九天 v0.1 的调试与 trace 语义。目标是让模拟器、测试和未来 RTL 拥有一致的可观测性模型。

## 1. 设计目标

- 记录 task 生命周期。
- 记录调度行为。
- 记录指令执行。
- 记录内存和 DMA 行为。
- 记录 barrier 阻塞、释放和 deadlock。
- 记录 trap 原因。

## 2. 事件类别

| 事件 | 含义 |
|---|---|
| `task_start` | task 被调度器接纳并开始运行 |
| `instruction` | 执行一条 Agent ISA 指令 |
| `memory_load` | 从 SPM 或 Cluster SRAM 读取 |
| `memory_store` | 写入 SPM 或 Cluster SRAM |
| `dma_copy` | 发生显式 DMA 搬运 |
| `dma_wait` | task 等待 DMA |
| `barrier_arrive` | task 到达 barrier |
| `barrier_release` | barrier 释放等待者 |
| `trap` | task 发生异常 |
| `deadlock` | 调度器检测到不可释放等待 |
| `halt` | task 正常结束 |

## 3. v0.1 Trace 格式

当前模拟器输出字符串 trace，后续应升级为结构化 JSON event：

```json
{
  "cycle": 12,
  "task": "producer",
  "event": "dma_copy",
  "detail": {
    "src": "host:0",
    "dst": "spm:0",
    "bytes": 8
  }
}
```

## 4. Trap 信息

trap 至少应包含：

- task。
- pc。
- reason。
- detail。

常见 reason：

- `bad_opcode`
- `bad_register`
- `bad_space`
- `memory_oob`
- `capability_violation`
- `cycle_budget_exhausted`
- `deadlock`
- `explicit_trap`

## 5. 调试控制规划

后续硬件阶段应考虑以下调试控制：

- 启停 trace。
- 按 task 过滤 trace。
- 按事件类型过滤 trace。
- 读取 task 状态。
- 注入 kill。
- 读取 trap buffer。

## 6. 兼容性

trace schema 一旦版本化，应保持向后兼容。新增字段可以加入 `detail`，但不应改变已有字段含义。
