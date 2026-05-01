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
| `ledger` | 长期任务账本视图与候选 delta | 控制面、受限 Agent task | 已规划 |
| `artifact` | 工具结果、日志、大型输出的引用化视图 | 控制面、受限 Agent task | 已规划 |
| `transcript` | 对话窗口、工具事件和 compact 边界的引用化视图 | 控制面、受限 Agent task | 已规划 |
| `context` | 下一轮上下文投影候选输出区 | 控制面、受限 Agent task | 已规划 |

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

长期记忆任务读取 trace 时只能读取事件 metadata、引用、reason code 和必要的计数摘要。若 task 请求未授权的 trace 正文窗口或已被裁剪的事件正文，运行时必须触发 `unauthorized_memory_source` 或返回带 reason 的 reject event。

## 8. ledger 空间

`ledger` 空间用于表达长期任务记忆的受控视图。它不是普通共享内存，也不是 Agent Domain 可以随意修改的全局状态。

规划中的 ledger 空间包含两类区域：

- 已提交 ledger view：由 Super Domain 维护，Agent Domain 只读。
- 候选 ledger delta buffer：由 Agent Domain 写入，Super Domain 审核后决定是否提交。

推荐 ledger 类型：

| 类型 | 用途 |
|---|---|
| `goal` | 用户目标、成功标准、禁止事项 |
| `plan` | 当前阶段、已完成步骤、待办步骤 |
| `evidence` | 文件、trace、artifact、测试结果等证据引用 |
| `decision` | 关键判断、被拒绝方案和原因 |
| `recovery` | 最近安全点、回滚依据、脏状态 |

访问原则：

- Agent task 默认无 ledger 权限。
- 读取已提交 ledger 需要 `ledger_read` capability。
- 写入候选 delta 需要 `ledger_delta_write` capability。
- 任何对已提交 ledger 的修改都必须由 Super Domain 完成。
- ledger 引用必须能回到 transcript、trace 或 artifact。

推荐 region 属性：

```json
{
  "name": "ledger_delta_out",
  "space": "ledger",
  "base": 0,
  "bytes": 32768,
  "access": "write",
  "kind": "ledger_delta",
  "schema": "jiutian.ledger_delta.v0.1",
  "candidate": true
}
```

已提交 ledger view 必须使用 `access: "read"`，且 `kind` 为 `ledger_view`。候选 delta buffer 必须使用 `access: "write"`，且 `candidate: true`。如果 `ledger_delta_extract.output` 指向 `ledger_view` 或任意非候选区域，运行时必须触发 `capability_violation`。

## 9. artifact 空间

`artifact` 空间用于大型工具输出、测试日志、文件快照、截图和其他不适合直接塞入模型上下文的数据。

Agent Domain 通常只读取 artifact 的 metadata 和 preview：

- artifact id。
- hash。
- byte size。
- MIME 或类型。
- 生成来源。
- 短 preview。
- 与 transcript/trace 的关联。

读取 artifact 正文应被视为高成本操作，必须由 Super Domain 授权。长期记忆投影任务优先处理 metadata 和 preview，只有在证据不足时才请求正文读取。

推荐 preview region 属性：

```json
{
  "name": "artifact_previews",
  "space": "artifact",
  "base": 0,
  "bytes": 65536,
  "access": "read",
  "kind": "artifact_preview",
  "body_allowed": false
}
```

当 `body_allowed` 为 `false` 时，`context_budget_pack`、`ledger_delta_extract` 和 `recovery_anchor_select` 都不得请求正文片段；违规时触发 `unauthorized_memory_source`。

## 10. transcript 空间

`transcript` 空间用于对话轮次、工具事件、compact boundary 和 parent 链的受控视图。Agent Domain 不直接修改 transcript，只能读取由 Super Domain 切出的窗口。

推荐 region 属性：

```json
{
  "name": "transcript_window",
  "space": "transcript",
  "base": 0,
  "bytes": 131072,
  "access": "read",
  "kind": "transcript_window",
  "boundary_ref": "compact:31",
  "parent_chain_required": true
}
```

访问原则：

- 读取 transcript 需要 `transcript_read` capability。
- `parent_chain_required` 为 true 时，运行时必须验证 boundary 和 parent 链连续。
- parent 链不连续时触发 `compact_boundary_mismatch`。
- transcript 引用必须使用稳定 ref，不能只保存自由文本摘要。

## 11. context 空间

`context` 空间用于 `context_budget_pack` 的候选输出。它是下一轮模型上下文的候选视图，不是长期 ledger 本体。

推荐 region 属性：

```json
{
  "name": "context_out",
  "space": "context",
  "base": 0,
  "bytes": 98304,
  "access": "write",
  "kind": "context_projection",
  "schema": "jiutian.context_projection.v0.1",
  "candidate": true
}
```

访问原则：

- 写入 context 输出需要 `context_projection_write` capability。
- 输出必须是候选区，且 `candidate: true`。
- 输出 schema 必须是 `jiutian.context_projection.v0.1`。
- 预算不足时不得写入部分成功对象，应触发 `projection_budget_exhausted` 并写 reject trace。

## 12. recovery candidate 输出

恢复点候选可以映射在 `ledger` 空间的候选 recovery buffer，也可以映射在控制面单独分配的候选输出区。推荐使用 `ledger` 空间并声明 `kind: "recovery_candidate"`。

```json
{
  "name": "recovery_candidate_out",
  "space": "ledger",
  "base": 32768,
  "bytes": 16384,
  "access": "write",
  "kind": "recovery_candidate",
  "schema": "jiutian.recovery_anchor.v0.1",
  "candidate": true
}
```

访问原则：

- 写入恢复点候选需要 `recovery_candidate_write` capability。
- 候选必须包含 transcript、trace 和 ledger ref，除非策略明确不要求。
- 脏状态不明时必须触发 `dirty_state_ambiguous`，不能生成看似确定的恢复点。

## 13. 对齐规则

v0.1 的 `load` 和 `store` 以 64-bit word 为基本单位。

推荐规则：

- 64-bit load/store 地址应 8 字节对齐。
- `dump_words` 地址应 8 字节对齐。
- DMA 地址可以 byte 对齐，但性能模型可对非对齐访问加 penalty。

当前模拟器尚未强制 8 字节对齐。后续版本可加入 `misaligned_access` trap。

## 14. 错误条件

地址空间相关错误包括：

| 错误 | 条件 |
|---|---|
| `bad_space` | 指令引用未知空间 |
| `memory_oob` | 地址越过空间容量 |
| `capability_violation` | host 访问未授权或权限不足 |
| `misaligned_access` | 后续用于非对齐 word 访问 |
| `unauthorized_memory_source` | 未授权读取 transcript、ledger 或 artifact |
| `dangling_evidence_ref` | ledger delta 指向不存在的证据 |
| `projection_budget_exhausted` | context 输出预算不足且不能保留必需段 |
| `context_ref_limit_exceeded` | context 输出引用数超过预算 |
| `ledger_delta_too_large` | 候选 ledger delta 超过输出 region 或预算 |
| `ledger_ref_limit_exceeded` | 候选 ledger delta 引用数超过预算 |
| `bad_ledger_type` | ledger region 或 delta 引用未知 ledger 类型 |
| `bad_ledger_op` | ledger delta 操作不在 v0.1 集合内 |
| `ledger_base_version_mismatch` | 读取基线与当前已提交 ledger 版本不一致 |
| `missing_required_evidence` | delta 操作缺少必需 evidence |
| `bad_context_section` | context pack 请求未知语义段 |
| `bad_recovery_section` | recovery anchor 请求未知语义段 |
| `missing_recovery_ref` | recovery candidate 缺少必需恢复引用 |
| `dirty_state_ambiguous` | 恢复点无法判定脏状态 |
| `ambiguous_next_action` | 恢复点无法给出唯一下一步动作 |
| `recovery_candidate_too_large` | 恢复点候选超过输出 region 或预算 |
| `recovery_ref_limit_exceeded` | 恢复点候选引用数超过预算 |

## 15. 未来物理映射建议

后续硬件原型可采用以下物理区域规划：

| 区域 | 建议属性 |
|---|---|
| control DRAM window | cacheable, coherent |
| Agent host window | capability protected |
| Cluster SRAM window | low latency, local |
| SPM window | core local, non-coherent |
| MMIO window | strongly ordered |
| Trace window | read-mostly, debug only |
| Ledger delta window | append-only candidate buffer |
| Artifact preview window | read-mostly, capability protected |
| Transcript window | read-mostly, capability protected |
| Context projection window | write-only candidate buffer |
| Recovery candidate window | write-only candidate buffer |

物理映射必须保持与 APU-IR 的逻辑空间兼容。
