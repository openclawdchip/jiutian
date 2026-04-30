# APU-IR v0.1

状态：种子草案

APU-IR 是 Agent 生成逻辑进入九天硬件前的稳定契约。它不是人类长期维护的源代码格式，而是运行时可验证、可调度、可降低的任务图描述。

## 1. 设计目标

- 明确任务图依赖。
- 明确内存区域和访问权限。
- 明确 DMA 搬运计划。
- 明确 barrier 和数据可见性。
- 明确资源预算。
- 允许降低到 Agent ISA v0.1。

## 2. 顶层结构

```json
{
  "version": "0.1",
  "name": "example_pipeline",
  "memory": [],
  "barriers": [],
  "tasks": []
}
```

## 3. Memory Region

```json
{
  "name": "input",
  "space": "host",
  "base": 0,
  "bytes": 64,
  "access": "read"
}
```

字段：

- `name`：区域名。
- `space`：`host`、`cluster` 或 `spm`。
- `base`：区域起始地址。
- `bytes`：区域大小。
- `access`：`read`、`write` 或 `read_write`。

## 4. Barrier

```json
{
  "name": "stage0",
  "participants": 2
}
```

## 5. Task

```json
{
  "name": "worker0",
  "placement": {"cluster": 0, "core": 0},
  "capabilities": ["input", "output", "scratch"],
  "budget": {"cycles": 1000, "spm_bytes": 65536, "cluster_bytes": 4096},
  "program": []
}
```

字段：

- `name`：任务名。
- `placement`：建议或强制放置位置。
- `capabilities`：任务可访问的 memory region 名称。
- `budget`：资源预算。
- `program`：Agent ISA v0.1 指令列表。

## 6. 降低规则

v0.1 中，APU-IR 的 `program` 可以直接包含 Agent ISA JSON 指令。后续版本会引入更高层级操作，例如：

- `map_records`
- `filter_rules`
- `scatter_gather`
- `prefetch_hint`
- `task_spawn`

## 7. 验证规则

运行时必须拒绝以下 IR：

- 任务访问未授权 memory region。
- DMA 源或目的越过 capability 边界。
- barrier 参与者数量与任务图不匹配。
- 预算缺失。
- 指令引用不存在的 label。
- 未知 op。

## 8. 最小示例

```json
{
  "version": "0.1",
  "name": "copy_add",
  "memory": [
    {"name": "input", "space": "host", "base": 0, "bytes": 8, "access": "read"},
    {"name": "output", "space": "host", "base": 8, "bytes": 8, "access": "write"}
  ],
  "barriers": [],
  "tasks": [
    {
      "name": "add_one",
      "placement": {"cluster": 0, "core": 0},
      "capabilities": ["input", "output"],
      "budget": {"cycles": 64, "spm_bytes": 1024, "cluster_bytes": 0},
      "program": [
        {"op": "dma_copy", "src_space": "host", "src": 0, "dst_space": "spm", "dst": 0, "bytes": 8},
        {"op": "dma_wait"},
        {"op": "load", "dst": "r1", "space": "spm", "addr": 0},
        {"op": "li", "dst": "r2", "imm": 1},
        {"op": "add", "dst": "r3", "src1": "r1", "src2": "r2"},
        {"op": "store", "src": "r3", "space": "spm", "addr": 0},
        {"op": "dma_copy", "src_space": "spm", "src": 0, "dst_space": "host", "dst": 8, "bytes": 8},
        {"op": "dma_wait"},
        {"op": "halt"}
      ]
    }
  ]
}
```
