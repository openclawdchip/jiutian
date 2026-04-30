# 九天 Agent ISA v0.1

状态：种子草案

本文件定义功能模拟器必须支持的最小 Agent 指令语义。v0.1 不是最终硬件 ISA，而是用于验证执行模型的参考指令集。

## 1. 机器模型

每个 Agent hardware thread 拥有：

- 16 个通用寄存器：`r0` 到 `r15`。
- `pc` 程序计数器。
- `halted` 状态。
- 所属 Agent core 的 SPM 访问权。
- 所属 cluster 的 Cluster SRAM 访问权。
- 任务 capability 限制。

`r0` 固定为 0。写入 `r0` 被忽略。

## 2. 地址空间

v0.1 模拟器使用命名空间地址，而不是直接使用真实物理地址：

- `spm:<addr>`：当前 core 的 SPM。
- `cluster:<addr>`：当前 cluster 的共享 SRAM。
- `host:<addr>`：由 capability 授权的外部内存区域。

所有地址访问必须通过 capability 检查。

## 3. 指令格式

模拟器使用 JSON-like 汇编对象表达指令：

```json
{"op": "li", "dst": "r1", "imm": 42}
```

后续 RTL 可将这些语义降低为二进制编码。

## 4. 算术与控制

### `li`

立即数加载。

```json
{"op": "li", "dst": "r1", "imm": 1}
```

### `add`

整数加法。

```json
{"op": "add", "dst": "r3", "src1": "r1", "src2": "r2"}
```

### `sub`

整数减法。

```json
{"op": "sub", "dst": "r3", "src1": "r1", "src2": "r2"}
```

### `jmp`

无条件跳转到 label。

```json
{"op": "jmp", "label": "loop"}
```

### `beqz`

寄存器为 0 时跳转。

```json
{"op": "beqz", "src": "r1", "label": "done"}
```

### `halt`

任务正常结束。

```json
{"op": "halt"}
```

### `trap`

显式异常。

```json
{"op": "trap", "reason": "bad_state"}
```

## 5. 内存访问

### `load`

从 SPM 或 Cluster SRAM 加载 64-bit 整数。

```json
{"op": "load", "dst": "r1", "space": "spm", "addr": 0}
```

### `store`

向 SPM 或 Cluster SRAM 写入 64-bit 整数。

```json
{"op": "store", "src": "r1", "space": "spm", "addr": 8}
```

## 6. DMA

### `dma_copy`

在 `host`、`cluster`、`spm` 之间搬运连续字节。v0.1 模拟器允许同步完成，也可以用固定延迟建模。

```json
{
  "op": "dma_copy",
  "src_space": "host",
  "src": 0,
  "dst_space": "spm",
  "dst": 0,
  "bytes": 64
}
```

### `dma_wait`

等待当前任务发出的 DMA 完成。

```json
{"op": "dma_wait"}
```

## 7. 同步与一致性

### `barrier`

等待指定 barrier 的所有参与者到达。

```json
{"op": "barrier", "name": "stage0"}
```

### `flush`

发布指定空间的写入。

```json
{"op": "flush", "space": "cluster"}
```

### `invalidate`

丢弃指定空间的本地旧副本。v0.1 功能模拟器可只记录 trace，不建模 cache 副本。

```json
{"op": "invalidate", "space": "spm"}
```

### `fence`

约束 DMA 与内存副作用顺序。

```json
{"op": "fence"}
```

## 8. Trace 要求

模拟器必须记录：

- 每条指令执行。
- SPM load/store。
- Cluster SRAM load/store。
- DMA copy。
- Barrier 到达与释放。
- Trap 与 halt。
