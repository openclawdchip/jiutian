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

九天中的 task 不只服务于算术或数据搬运。面向 Claude Code 类 Agent runtime 时，task 还承担长期任务记忆的结构化处理：从工具事件、transcript、artifact preview 和 compact 边界中提取可恢复的任务状态。

因此 v0.1 任务模型把 task 分成三类：

| 类别 | 作用 | 是否允许外部副作用 |
|---|---|---|
| `compute` | 普通计算、转换、过滤、聚合 | 否 |
| `memory_projection` | 长期记忆扫描、摘要候选、引用打包、上下文预算裁剪 | 否 |
| `control_assist` | 权限预筛、风险分类、恢复点候选选择 | 否 |

这三类 task 的共同边界是：Agent Domain 只能产生候选结果、结构化 delta、引用列表和 trace；最终写文件、写 transcript、提交 ledger 或执行真实外部副作用，必须由 Super Domain 完成。

## 2. Task 状态

```text
created -> admitted -> running -> completed
                         |  |
                         |  -> waiting -> running
                         |     -> trapped
                         |     -> timed_out
                         |     -> killed
```

状态含义：

- `created`：IR 中声明，但尚未验证。
- `admitted`：通过控制面验证，资源已预留。
- `running`：已派发到 Agent core。
- `waiting`：在 barrier、DMA 或未来同步对象上等待。
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

### Capability 类别

为长期记忆任务增加以下推荐 capability 类别：

| 类别 | 允许读取 | 允许写入 | 说明 |
|---|---|---|---|
| `transcript_read` | transcript window、compact boundary、parent 链 | 不允许 | 用于检查最近对话和工具事件结构 |
| `artifact_preview_read` | artifact metadata、preview、hash、size | 不允许 | 不直接读取大型 artifact 正文 |
| `trace_read` | trace window、trap 摘要、调度事件引用 | 不允许 | 用于恢复点选择和审计 |
| `ledger_read` | 已提交 Goal/Plan/Evidence/Decision/Recovery ledger | 不允许 | 用于增量更新前的状态对照 |
| `ledger_delta_write` | 不允许 | 候选 ledger delta buffer | Agent Domain 只写候选 delta |
| `context_projection_write` | 不允许 | 下一轮上下文投影候选 | 由 Super Domain 审核后送入模型 |
| `recovery_candidate_write` | 不允许 | 恢复点候选 buffer | 由 Super Domain 审核后写入 recovery ledger |

这些 capability 不要求 v0.1 模拟器立即实现专用命名空间，但规格层必须保留语义，避免长期记忆路径退化为任意 host 读写。

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

长期记忆类任务还应声明逻辑预算：

```json
{
  "token_budget": 50000,
  "max_refs": 128,
  "max_artifact_previews": 256,
  "max_ledger_delta_bytes": 32768,
  "max_recovery_candidates": 8,
  "max_context_sections": 12
}
```

逻辑预算由 Super Domain 在准入阶段检查。Agent Domain 不能为了生成更长摘要而越过预算；超出预算时应返回 `projection_budget_exhausted`、`ledger_delta_too_large` 或 `recovery_candidate_too_large`，而不是静默截断关键状态。

长期记忆 op 的预算解释：

| op_class | 必需预算 | 触发错误 |
|---|---|---|
| `context_budget_pack` | `cycles`、`token_budget`、`max_refs` | `projection_budget_exhausted`、`context_ref_limit_exceeded` |
| `ledger_delta_extract` | `cycles`、`max_refs`、`max_ledger_delta_bytes` | `ledger_delta_too_large`、`ledger_ref_limit_exceeded` |
| `recovery_anchor_select` | `cycles`、`max_refs`、`max_recovery_candidates` | `recovery_candidate_too_large`、`recovery_ref_limit_exceeded` |

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

长期记忆相关 reason 建议包括：

- `projection_budget_exhausted`：上下文投影超过预算。
- `ledger_delta_too_large`：候选 ledger delta 超过允许大小。
- `bad_ledger_type`：未知 ledger 类型。
- `dangling_evidence_ref`：候选 evidence 指向不存在的 transcript、artifact 或 trace。
- `compact_boundary_mismatch`：compact 边界与 transcript parent 链不一致。
- `unauthorized_memory_source`：task 请求了未授权 transcript、artifact 或 ledger 区域。
- `bad_context_section`：`context_budget_pack.include` 或 `must_keep` 中出现未知语义段。
- `context_ref_limit_exceeded`：上下文投影引用数超过 `max_refs`。
- `missing_required_evidence`：delta 操作缺少必需 evidence。
- `bad_ledger_op`：delta 操作不在 v0.1 允许集合内。
- `ledger_base_version_mismatch`：delta 基线版本与已提交 ledger 版本不一致。
- `ledger_ref_limit_exceeded`：候选 delta 引用数超过 `max_refs`。
- `bad_recovery_section`：恢复点选择请求未知语义段。
- `missing_recovery_ref`：恢复点候选缺少策略要求的 transcript、trace、artifact 或 ledger 引用。
- `dirty_state_ambiguous`：存在未声明的脏状态，恢复结果不可判定。
- `ambiguous_next_action`：恢复点无法给出唯一下一步动作。
- `recovery_candidate_too_large`：恢复点候选超过输出区域或预算。
- `recovery_ref_limit_exceeded`：恢复点候选引用数超过 `max_refs`。

## 7. Cleanup

任务结束后，运行时必须：

- 标记状态。
- 完成或取消未完成 DMA。
- 释放 barrier 参与关系。
- 根据安全策略清理 SPM。
- 写入 trace。

对于 `memory_projection` 和 `control_assist` task，cleanup 还必须：

- 丢弃未被 Super Domain 提交的候选 delta。
- 标记候选 `ContextProjection` 的审核状态。
- 标记候选 `RecoveryAnchor` 的审核状态。
- 保留最小 trace，以解释保留或丢弃了哪些引用。
- 清理 SPM 中的 transcript 片段、artifact preview 和 ledger 摘要。

## 8. v0.1 安全底线

任何 Agent task 都不得：

- 访问未授权 host region。
- 写入只读 region。
- 读取只写 region。
- 越过 SPM 或 Cluster SRAM 容量。
- 绕过周期预算。
- 创建未声明的外部副作用。

长期记忆路径还不得：

- 直接修改已提交 ledger。
- 直接写入 transcript JSONL 或长期 memory 文件。
- 在未授权情况下读取 artifact 正文。
- 伪造不存在的 evidence、trace 或恢复点引用。
- 把被用户明确禁止的目标改写为新的默认目标。

## 9. Ledger Delta

Ledger delta 是 Agent Domain 生成、Super Domain 审核提交的长期记忆更新候选。推荐最小格式：

```json
{
  "schema": "jiutian.ledger_delta.v0.1",
  "task": "extract-memory-delta",
  "base_versions": {
    "plan": "plan:42",
    "evidence": "evidence:87"
  },
  "deltas": [
    {
      "ledger": "plan",
      "op": "mark_done",
      "path": "/steps/3",
      "evidence": ["trace:188", "artifact:test-log:sha256:abcd"]
    },
    {
      "ledger": "decision",
      "op": "append",
      "value": {
        "summary": "拒绝修改公共 API，因为用户目标要求保持兼容。",
        "evidence": ["transcript:turn:17"]
      }
    }
  ]
}
```

规则：

- `base_versions` 中每个版本必须指向 Super Domain 已提交版本。
- `evidence` 必须可解析，不能是自由文本。
- `op` 必须来自版本化集合，v0.1 推荐 `append`、`mark_done`、`replace_summary`、`add_ref`、`drop_candidate`。
- Agent Domain 不能直接提交 delta，只能把它写入候选输出区。

## 10. Context Projection

Context Projection 是 `context_budget_pack` 生成、给下一轮模型推理看的“工作台视图”，不是长期记忆本体。推荐最小格式：

```json
{
  "schema": "jiutian.context_projection.v0.1",
  "producer_task": "pack_next_context",
  "base_versions": {
    "goal": "goal:12",
    "plan": "plan:42",
    "evidence": "evidence:87",
    "decision": "decision:15",
    "recovery": "recovery:9"
  },
  "goal": "修复指定 bug，禁止无关重构。",
  "current_phase": "补充边界条件并运行回归测试。",
  "active_evidence": [
    {"ref": "artifact:test-log:sha256:abcd", "reason": "最近失败断言"},
    {"ref": "file:src/runtime/state.ts#L120", "reason": "状态初始化入口"}
  ],
  "rejected_paths": [
    "不修改公共 API。"
  ],
  "next_actions": [
    "检查状态初始化分支。",
    "补最小测试。",
    "运行目标测试。"
  ],
  "budget": {
    "token_budget": 50000,
    "tokens_estimate": 42000,
    "refs": 32,
    "dropped_candidates": 7
  }
}
```

规则：

- Projection 可以被 compact、重排和重写。
- Ledger 不能因为 Projection 被压缩而丢失。
- Projection 中的每个关键判断都应能回指 ledger 或 evidence。
- `producer_task` 必须等于生成该候选的 task 名称。
- `base_versions` 中列出的版本必须与准入时读取的已提交 ledger 一致。
- `budget.tokens_estimate` 不得超过 `budget.token_budget`。
- `active_evidence.ref` 必须可解析，且数量不得超过 task `max_refs`。
- `dropped_candidates` 大于 0 时，trace 必须保留丢弃原因计数。

## 11. Recovery Anchor

Recovery Anchor 是 `recovery_anchor_select` 生成的恢复点候选。它描述重新接续长期任务时的最小可信入口，而不是普通摘要。推荐最小格式：

```json
{
  "schema": "jiutian.recovery_anchor.v0.1",
  "producer_task": "select_recovery_anchor",
  "strategy": "minimal_replay",
  "base_versions": {
    "plan": "plan:42",
    "evidence": "evidence:87",
    "recovery": "recovery:9"
  },
  "refs": {
    "transcript": "transcript:turn:19",
    "trace": "trace:seq:188",
    "ledger": ["plan:42", "evidence:87"],
    "artifact": ["artifact:test-log:sha256:abcd"]
  },
  "dirty_state": {
    "status": "clean",
    "pending_candidates": []
  },
  "next_action": {
    "kind": "run_test",
    "summary": "运行目标回归测试确认修复。"
  }
}
```

规则：

- `schema` 必须是 `jiutian.recovery_anchor.v0.1`。
- `refs.transcript`、`refs.trace` 和 `refs.ledger` 必须按策略要求出现并可解析。
- `dirty_state.status` 只能是 `clean`、`declared_dirty` 或 `unknown_rejected`。
- 当策略要求确定恢复时，`dirty_state.status` 不得为 `unknown_rejected`。
- `next_action` 必须是单个动作对象，不能是自由文本数组。
- Agent Domain 只能写候选恢复点，不能直接提交 recovery ledger。
