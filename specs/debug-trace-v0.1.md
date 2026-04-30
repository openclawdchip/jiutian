# 调试与 Trace v0.1

状态：种子草案

本文档定义九天 v0.1 的调试与 trace 语义。目标是让模拟器、测试、benchmark、runtime 和未来 RTL 拥有一致的可观测性模型。

## 1. 设计目标

Trace 的目的不是输出越多越好，而是回答架构验证中最关键的问题：

- 哪个 task 在何时运行？
- 执行了哪条指令？
- 数据从哪里搬到哪里？
- 哪个 barrier 阻塞了 task？
- 哪个 barrier 释放了 task？
- 异常发生在什么 pc，原因是什么？
- 调度器是否发生 deadlock？

调试系统必须服务于可复现性。任何 benchmark 结论都应能通过 trace 找到行为依据。

## 2. 当前实现

当前模拟器输出字符串 trace。例如：

```text
producer pc=6 {'op': 'barrier', 'name': 'stage0'}
producer barrier stage0 arrived=2/2
barrier stage0 release consumer,producer
```

字符串 trace 便于早期阅读，但不适合长期工具化。v0.1 后续应升级为结构化 JSON event。

## 3. 事件类别

| 事件 | 含义 | 关键字段 |
|---|---|---|
| `task_start` | task 被调度器接纳并开始运行 | task, cluster, core |
| `instruction` | 执行一条 Agent ISA 指令 | task, pc, op |
| `memory_load` | 从 SPM 或 Cluster SRAM 读取 | task, space, addr, bytes |
| `memory_store` | 写入 SPM 或 Cluster SRAM | task, space, addr, bytes |
| `dma_copy` | 发生显式 DMA 搬运 | task, src, dst, bytes |
| `dma_wait` | task 等待 DMA | task |
| `barrier_arrive` | task 到达 barrier | task, barrier, arrived, participants |
| `barrier_release` | barrier 释放等待者 | barrier, tasks |
| `flush` | 发布写入 | task, space |
| `invalidate` | 丢弃旧副本 | task, space |
| `fence` | 建立顺序点 | task |
| `trap` | task 发生异常 | task, pc, reason, detail |
| `deadlock` | 调度器检测到不可释放等待 | waiting_tasks |
| `halt` | task 正常结束 | task, pc |

## 4. 结构化 Trace Schema

推荐 JSON event 格式：

```json
{
  "schema": "jiutian.trace.v0.1",
  "seq": 12,
  "cycle": 12,
  "cluster": 0,
  "core": 1,
  "task": "consumer",
  "pc": 2,
  "event": "memory_load",
  "detail": {
    "space": "cluster",
    "addr": 0,
    "bytes": 8,
    "value": 9
  }
}
```

字段说明：

- `schema`：trace schema 版本。
- `seq`：全局递增事件序号。
- `cycle`：模拟周期或调度步。功能模拟器可令 `cycle == seq`。
- `cluster`：事件所在 cluster，可为空。
- `core`：事件所在 core，可为空。
- `task`：事件所属 task，可为空。
- `pc`：事件发生时的指令位置，可为空。
- `event`：事件类型。
- `detail`：事件特定字段。

## 5. Trap 记录

trap event 至少包含：

```json
{
  "event": "trap",
  "task": "worker0",
  "pc": 12,
  "detail": {
    "reason": "capability_violation",
    "message": "write host:16+8"
  }
}
```

常见 reason：

- `bad_opcode`
- `bad_register`
- `bad_space`
- `memory_oob`
- `capability_violation`
- `cycle_budget_exhausted`
- `deadlock`
- `explicit_trap`
- `misaligned_access`

## 6. 调试控制

后续硬件或 runtime 应提供以下调试控制能力：

### Trace Enable

控制 trace 是否开启。关闭 trace 时仍应保留 trap 摘要。

### Event Filter

按事件类型过滤。例如只记录 DMA 和 barrier。

### Task Filter

按 task 名称或 task id 过滤。

### Trap Buffer

保存最近 N 个 trap，供控制面读取。

### Kill Control

控制面可终止指定 task。kill 应产生 trace event。

### Snapshot

读取 task 状态、pc、寄存器摘要、budget 剩余值和等待对象。

## 7. Trace 与 Benchmark

benchmark 结果应能关联 trace：

- 总指令数。
- DMA 次数和总字节数。
- barrier 次数。
- waiting 步数。
- trap 次数。
- task 完成数。

这些指标可以作为早期能耗 proxy 和瓶颈分析依据。

## 8. 兼容性规则

一旦 trace schema 进入版本化状态，应遵守：

- 不删除已有字段。
- 不改变已有字段含义。
- 新增字段放入 `detail` 或作为可选顶层字段。
- 工具必须忽略未知字段。

## 9. v0.1 到 v0.2 的演进

建议下一步：

- 把字符串 trace 改为结构化 event。
- 增加 `--trace-format text|json`。
- 增加 trace summary。
- 增加 benchmark counters。
- 增加 deadlock 诊断详情。
