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
- `memory_header_scan`
- `artifact_preview_pack`
- `context_budget_pack`
- `ledger_delta_extract`
- `recovery_anchor_select`

## 7. 长期记忆扩展草案

为了支持 Claude Code 类 Agent 的长期任务，APU-IR 后续需要能表达“记忆账本”投影任务。v0.1 不要求模拟器实现这些高级操作，但字段命名和任务模型应保持兼容。

### Ledger Region

```json
{
  "name": "plan_ledger",
  "space": "host",
  "base": 4096,
  "bytes": 8192,
  "access": "read_write",
  "kind": "ledger",
  "ledger_type": "plan"
}
```

`ledger_type` 可取：

- `goal`：目标、成功标准、禁止事项。
- `plan`：阶段、步骤、依赖和完成状态。
- `evidence`：文件、命令、测试、工具结果的引用。
- `decision`：路线选择和拒绝理由。
- `recovery`：last safe point、回滚引用和 dirty state。

### Context Budget Pack Task

```json
{
  "name": "pack_next_context",
  "placement": {"cluster": 0, "core": 0},
  "capabilities": [
    "transcript_window",
    "goal_ledger_read",
    "plan_ledger_read",
    "evidence_ledger_read",
    "artifact_previews",
    "context_out"
  ],
  "budget": {
    "cycles": 2000,
    "spm_bytes": 65536,
    "cluster_bytes": 65536,
    "token_budget": 50000,
    "max_refs": 64,
    "max_sections": 12
  },
  "op_class": "context_budget_pack",
  "context_pack": {
    "base_versions": {
      "goal": "goal:12",
      "plan": "plan:42",
      "evidence": "evidence:87",
      "decision": "decision:15",
      "recovery": "recovery:9"
    },
    "inputs": ["transcript_window", "goal_ledger_read", "plan_ledger_read", "evidence_ledger_read", "artifact_previews"],
    "include": ["active_goal", "current_phase", "pending_steps", "recent_evidence", "last_safe_point"],
    "must_keep": ["active_goal", "user_constraints", "unsafe_to_drop_refs"],
    "drop_policy": "oldest_low_confidence_first",
    "ordering": "goal_plan_evidence_recovery",
    "output_schema": "jiutian.context_projection.v0.1",
    "output": "context_out"
  },
  "program": []
}
```

该任务只产生模型可见投影和引用列表，不直接改写长期 memory。长期 ledger 的提交由 Super Domain 完成。

字段约束：

- `base_versions`：可选但推荐。出现时必须覆盖被读取的 ledger 类型，并指向已提交版本。
- `inputs`：只能引用 task capability 中授权的 transcript、ledger 或 artifact preview 区域。
- `include`：声明允许进入投影的语义段，未知段必须触发 `bad_context_section`。
- `must_keep`：声明预算不足时仍不可丢弃的语义段。若预算无法容纳，必须触发 `projection_budget_exhausted`。
- `drop_policy`：v0.1 支持 `oldest_low_confidence_first`、`lowest_priority_first`、`reject_on_overflow`。
- `ordering`：v0.1 支持 `goal_plan_evidence_recovery` 或 `source_order`。
- `output_schema`：必须是 `jiutian.context_projection.v0.1`。
- `output`：必须指向具备 `context_projection_write` 语义的候选输出区。

模拟器可先不执行自然语言压缩，但必须能验证字段、预算和 capability，并在 trace 中记录 `context_budget_pack_start` 与 `context_projection_emit`。

### Ledger Delta Task

```json
{
  "name": "extract_ledger_delta",
  "placement": {"cluster": 0, "core": 1},
  "capabilities": [
    "transcript_window",
    "artifact_previews",
    "plan_ledger_read",
    "ledger_delta_out"
  ],
  "budget": {
    "cycles": 4000,
    "spm_bytes": 65536,
    "cluster_bytes": 131072,
    "max_refs": 128,
    "max_ledger_delta_bytes": 32768
  },
  "op_class": "ledger_delta_extract",
  "ledger_delta": {
    "schema": "jiutian.ledger_delta.v0.1",
    "base_versions": {
      "goal": "goal:12",
      "plan": "plan:42",
      "evidence": "evidence:87",
      "decision": "decision:15",
      "recovery": "recovery:9"
    },
    "inputs": ["transcript_window", "artifact_previews"],
    "allowed_ledgers": ["goal", "plan", "evidence", "decision", "recovery"],
    "allowed_ops": ["append", "mark_done", "replace_summary", "add_ref", "drop_candidate"],
    "require_evidence_for": ["append", "mark_done", "replace_summary", "add_ref"],
    "conflict_policy": "reject_on_base_mismatch",
    "output": "ledger_delta_out"
  },
  "program": []
}
```

该任务生成候选 delta。运行时验证时必须确认：

- `base_versions` 指向已提交 ledger。
- `output` 只指向候选 delta 区域。
- 输入 artifact 只能是授权 preview，除非 capability 显式允许正文片段。
- 每个新增 evidence 必须携带可解析引用。
- `allowed_ledgers` 只能包含已知 ledger 类型。
- `allowed_ops` 只能包含 v0.1 版本化操作。
- `require_evidence_for` 中列出的操作如果没有 evidence，必须触发 `missing_required_evidence`。
- 候选 delta 大小超过预算时必须触发 `ledger_delta_too_large`，不得截断后继续成功。
- `conflict_policy` 为 `reject_on_base_mismatch` 时，任何 base version 与提交版本不一致都必须触发 `ledger_base_version_mismatch`。

### Recovery Anchor Task

```json
{
  "name": "select_recovery_anchor",
  "placement": {"cluster": 0, "core": 2},
  "capabilities": [
    "trace_window",
    "artifact_previews",
    "ledger_read",
    "recovery_candidate_out"
  ],
  "budget": {"cycles": 2000, "spm_bytes": 32768, "cluster_bytes": 65536},
  "op_class": "recovery_anchor_select",
  "recovery": {
    "strategy": "minimal_replay",
    "base_versions": {
      "plan": "plan:42",
      "evidence": "evidence:87",
      "recovery": "recovery:9"
    },
    "inputs": ["trace_window", "artifact_previews", "ledger_read"],
    "include": ["latest_clean_diff", "last_valid_test", "active_goal"],
    "required_refs": ["transcript", "trace", "ledger"],
    "dirty_state_policy": "declare_or_reject",
    "next_action_policy": "single_deterministic_step",
    "output": "recovery_candidate_out"
  },
  "program": []
}
```

恢复点不是普通摘要。它必须能说明从哪个 transcript、artifact、trace 和 ledger 版本恢复，且恢复后下一步动作应保持确定。

字段约束：

- `strategy`：v0.1 支持 `minimal_replay`、`latest_verified`、`manual_checkpoint`。
- `base_versions`：必须覆盖恢复判断依赖的 ledger 类型。
- `inputs`：只能引用 task capability 中授权的 trace、artifact preview 或 ledger view。
- `include`：未知恢复段必须触发 `bad_recovery_section`。
- `required_refs`：v0.1 支持 `transcript`、`trace`、`artifact`、`ledger`。输出候选缺少必需引用时触发 `missing_recovery_ref`。
- `dirty_state_policy` 为 `declare_or_reject` 时，存在未提交候选、未验证文件状态或未完成工具结果却未声明，必须触发 `dirty_state_ambiguous`。
- `next_action_policy` 为 `single_deterministic_step` 时，输出必须给出唯一下一步动作；多分支或空动作触发 `ambiguous_next_action`。
- `output` 必须指向具备 `recovery_candidate_write` 语义的候选输出区。

## 8. 验证规则

运行时必须拒绝以下 IR：

- 任务访问未授权 memory region。
- DMA 源或目的越过 capability 边界。
- barrier 参与者数量与任务图不匹配。
- 预算缺失。
- 指令引用不存在的 label。
- 未知 op。
- ledger region 缺少 `ledger_type` 或访问权限过大。
- context projection 输出区域未授权。
- recovery anchor 指向不存在的 trace 或 artifact。
- ledger delta 直接写入已提交 ledger 区域。
- memory projection task 请求未授权 artifact 正文。
- context projection 中关键判断没有 evidence 或 ledger 回指。
- `context_budget_pack` 缺少 `budget.token_budget`。
- `context_budget_pack` 的 `must_keep` 段无法在预算内保留。
- `ledger_delta_extract` 的 `allowed_ops`、`allowed_ledgers` 或 delta `op` 不在 v0.1 集合内。
- `ledger_delta_extract` 引用的 `base_versions` 与当前已提交版本不匹配。
- `recovery_anchor_select` 输出缺少 `transcript`、`trace` 或 `ledger` 等必需恢复引用。
- `recovery_anchor_select` 不能给出唯一下一步动作。

## 9. 最小示例

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
