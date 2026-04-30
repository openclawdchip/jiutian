# 任务模型 v0.1

状态：种子草案

## 1. Task

Task 是九天 v0.1 的最小调度、授权和异常边界。每个 task 包含：

- 名称。
- 放置位置。
- capability 集合。
- 资源预算。
- 指令程序。
- 运行状态。

## 2. Task 状态

```text
created -> admitted -> running -> completed
                         |     -> trapped
                         |     -> timed_out
                         |     -> killed
```

状态含义：

- `created`：IR 中声明，但尚未验证。
- `admitted`：通过控制面验证，资源已预留。
- `running`：已派发到 Agent core。
- `completed`：执行 `halt` 正常结束。
- `trapped`：非法访问、非法指令或显式 trap。
- `timed_out`：周期预算耗尽。
- `killed`：控制面主动终止。

## 3. Capability

Capability 是任务可执行动作的边界。v0.1 capability 至少包含：

```json
{
  "region": "input",
  "space": "host",
  "base": 0,
  "bytes": 64,
  "access": "read"
}
```

访问检查规则：

- `read` 允许 load 或 DMA 读取。
- `write` 允许 store 或 DMA 写入。
- `read_write` 允许读写。
- 访问范围必须完全落在 `[base, base + bytes)` 内。

## 4. Resource Budget

```json
{
  "cycles": 1000,
  "spm_bytes": 65536,
  "cluster_bytes": 4096,
  "dma_ops": 16
}
```

v0.1 模拟器必须执行 `cycles` 检查。其他预算可以先记录 trace，再逐步强制执行。

## 5. Placement

```json
{"cluster": 0, "core": 0, "thread": 0}
```

v0.1 允许省略 `thread`。如果省略，模拟器选择该 core 的第一个空闲 thread。

## 6. Exception

异常对象应包含：

```json
{
  "task": "worker0",
  "pc": 12,
  "reason": "capability_violation",
  "detail": "host write out of output region"
}
```

## 7. Cleanup

任务结束后，运行时必须：

- 标记状态。
- 完成或取消未完成 DMA。
- 释放 barrier 参与关系。
- 根据安全策略清理 SPM。
- 写入 trace。

## 8. v0.1 安全底线

任何 Agent task 都不得：

- 访问未授权 host region。
- 写入只读 region。
- 读取只写 region。
- 越过 SPM 或 Cluster SRAM 容量。
- 绕过周期预算。
- 创建未声明的外部副作用。
