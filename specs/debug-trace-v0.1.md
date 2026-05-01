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
| `ledger_read` | 读取已提交长期任务账本视图 | task, ledger_type, version |
| `context_budget_pack_start` | 开始生成上下文预算投影 | task, token_budget, max_refs, include |
| `ledger_delta_emit` | 生成候选账本增量 | task, ledgers, bytes, evidence_refs |
| `ledger_delta_reject` | 候选账本增量被运行时拒绝 | task, reason, base_versions |
| `context_projection_emit` | 生成下一轮上下文投影候选 | task, tokens_estimate, refs |
| `context_projection_reject` | 上下文投影候选被运行时拒绝 | task, reason, tokens_estimate |
| `artifact_preview_read` | 读取 artifact metadata 或 preview | task, artifact_ref, bytes |
| `compact_boundary_check` | 检查 compact 边界和 transcript 链 | task, boundary_ref, status |
| `recovery_anchor_select_start` | 开始选择恢复点候选 | task, strategy, required_refs |
| `recovery_anchor_emit` | 生成恢复点候选 | task, recovery_ref, evidence_refs |
| `recovery_anchor_reject` | 恢复点候选被运行时拒绝 | task, reason, missing_refs |

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
- `projection_budget_exhausted`
- `context_ref_limit_exceeded`
- `ledger_delta_too_large`
- `ledger_ref_limit_exceeded`
- `bad_ledger_type`
- `bad_ledger_op`
- `ledger_base_version_mismatch`
- `missing_required_evidence`
- `dangling_evidence_ref`
- `compact_boundary_mismatch`
- `unauthorized_memory_source`
- `bad_context_section`
- `bad_recovery_section`
- `missing_recovery_ref`
- `dirty_state_ambiguous`
- `ambiguous_next_action`
- `recovery_candidate_too_large`
- `recovery_ref_limit_exceeded`

## 6. 长期记忆事件 detail

长期记忆事件必须只记录可审计元数据，不默认记录大段正文。

### `context_budget_pack_start`

```json
{
  "event": "context_budget_pack_start",
  "task": "pack_next_context",
  "detail": {
    "token_budget": 50000,
    "max_refs": 64,
    "include": ["active_goal", "current_phase", "pending_steps"],
    "must_keep": ["active_goal", "user_constraints"],
    "base_versions": {"goal": "goal:12", "plan": "plan:42"}
  }
}
```

### `context_projection_emit`

```json
{
  "event": "context_projection_emit",
  "task": "pack_next_context",
  "detail": {
    "output": "context_out",
    "schema": "jiutian.context_projection.v0.1",
    "tokens_estimate": 42000,
    "token_budget": 50000,
    "refs": 32,
    "dropped_candidates": 7,
    "base_versions": {"goal": "goal:12", "plan": "plan:42"}
  }
}
```

### `ledger_delta_emit`

```json
{
  "event": "ledger_delta_emit",
  "task": "extract_ledger_delta",
  "detail": {
    "output": "ledger_delta_out",
    "schema": "jiutian.ledger_delta.v0.1",
    "base_versions": {"plan": "plan:42", "evidence": "evidence:87"},
    "ledgers": ["plan", "decision"],
    "ops": ["mark_done", "append"],
    "bytes": 8192,
    "evidence_refs": ["trace:seq:188", "artifact:test-log:sha256:abcd"]
  }
}
```

### `recovery_anchor_emit`

```json
{
  "event": "recovery_anchor_emit",
  "task": "select_recovery_anchor",
  "detail": {
    "output": "recovery_candidate_out",
    "schema": "jiutian.recovery_anchor.v0.1",
    "strategy": "minimal_replay",
    "recovery_ref": "recovery-candidate:0",
    "refs": {
      "transcript": "transcript:turn:19",
      "trace": "trace:seq:188",
      "ledger": ["plan:42", "evidence:87"]
    },
    "dirty_state": "clean",
    "next_action_kind": "run_test"
  }
}
```

### `*_reject`

拒绝类事件的 `detail` 至少包含：

```json
{
  "reason": "ledger_base_version_mismatch",
  "message": "plan base version is stale",
  "output": "ledger_delta_out",
  "base_versions": {"plan": "plan:41"},
  "current_versions": {"plan": "plan:42"}
}
```

`reason` 必须来自 Trap 记录中的 reason 集合。拒绝类事件可以与 `trap` 同时出现；如果 task 因候选无效而终止，必须同时写入 `trap`。

## 7. 调试控制

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

## 8. Trace 与 Benchmark

benchmark 结果应能关联 trace：

- 总指令数。
- DMA 次数和总字节数。
- barrier 次数。
- waiting 步数。
- trap 次数。
- task 完成数。
- ledger delta 数量和大小。
- context projection 的引用数和预算使用率。
- context projection 被拒绝次数与拒绝原因分布。
- artifact preview 读取次数与正文读取请求次数。
- compact boundary 检查成功率。
- recovery anchor 数量和可解析率。
- recovery anchor 被拒绝次数与拒绝原因分布。

这些指标可以作为早期能耗 proxy 和瓶颈分析依据。

## 9. 长期记忆 Trace 约束

长期记忆 trace 的目标不是泄露完整用户内容，而是让恢复和审计可解释。推荐规则：

- trace 中记录引用、hash、byte size 和 reason code，默认不记录大型正文。
- `ledger_delta_emit` 必须包含 `base_versions` 和 `evidence_refs` 摘要。
- `context_budget_pack_start` 必须记录 token 预算、引用预算、include 和 must_keep 摘要。
- `context_projection_emit` 必须记录 token 预算估计、实际引用数和被丢弃候选数。
- `ledger_delta_reject`、`context_projection_reject` 和 `recovery_anchor_reject` 必须记录 reason code。
- `compact_boundary_check` 必须能说明 parent 链是否连续。
- `recovery_anchor_emit` 必须能指向可恢复的 transcript、artifact、trace 或 ledger 位置。
- `recovery_anchor_emit` 必须记录 `dirty_state` 和 `next_action_kind`，用于判断恢复后动作是否确定。
- 如果 trace 因隐私策略被裁剪，必须保留可诊断的 event id 和错误原因。

## 10. 兼容性规则

一旦 trace schema 进入版本化状态，应遵守：

- 不删除已有字段。
- 不改变已有字段含义。
- 新增字段放入 `detail` 或作为可选顶层字段。
- 工具必须忽略未知字段。

## 11. v0.1 到 v0.2 的演进

建议下一步：

- 把字符串 trace 改为结构化 event。
- 增加 `--trace-format text|json`。
- 增加 trace summary。
- 增加 benchmark counters。
- 增加 deadlock 诊断详情。
- 增加长期记忆投影任务的 trace counters。
