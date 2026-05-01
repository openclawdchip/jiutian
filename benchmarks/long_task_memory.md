# 长期任务记忆 Benchmark

该 benchmark 面向长时间、多轮、可中断的 Agent 工作负载，重点衡量系统在 compact 后是否仍能保持目标、计划、证据、决策和恢复点的一致性。v0.1 模拟器已经覆盖三个最小高层记忆算子，用于验证候选 ledger delta、context projection 和 recovery anchor 的数据流；离线校验器用于验证 benchmark 契约样例本身是否自洽。

## 目标

- 验证 compact 前后的 transcript 边界是否连续。
- 验证 ledger delta 是否只写入候选输出区，并且每条关键更新都带有 evidence 引用。
- 验证 context projection 是否在 token 与引用预算内保留下一步所需信息。
- 验证 recovery anchor 是否能从 compact 后状态恢复到确定的下一步。

## 工作负载定义

输入是一段虚拟开发任务的长期记忆状态：

- `transcript_windows`：compact 前后的对话窗口边界。
- `ledgers`：Goal、Plan、Evidence、Decision、Recovery 五类 ledger 的基线版本。
- `artifact_previews`：只包含授权摘要和引用，不包含完整文件正文。
- `tasks`：三个记忆相关 APU-IR 草案任务。
- `expected_outputs`：离线校验器应接受的 ledger delta、context projection 和 recovery anchor。

该样例刻意使用小规模数据，便于人工审阅。后续可按相同 schema 扩展为多 compact、多文件、多恢复点数据集。

## 输入规模

基础样例：

- compact 次数：1。
- transcript 片段：2 个窗口，8 个 turn。
- ledger 类型：5 类。
- artifact preview：3 条。
- 任务数：3 个。
- 预期 ledger delta：6 条。
- context projection 引用预算：16。
- recovery anchor 候选：1 个。

扩展规模建议：

| 规模 | compact 次数 | transcript turn | artifact preview | delta 数量 |
| :--- | ---: | ---: | ---: | ---: |
| small | 1 | 8-32 | 3-8 | 4-12 |
| medium | 3-8 | 64-256 | 16-64 | 32-128 |
| large | 16+ | 1024+ | 256+ | 512+ |

## 指标

- `compact_count`：compact 次数。
- `boundary_valid`：compact 前后 transcript parent 链是否连续。
- `delta_count_by_ledger`：五类 ledger 的 delta 数量。
- `delta_bytes`：候选 delta 总字节数。
- `projection_refs`：投影进入上下文的引用数。
- `dropped_refs_retained`：被上下文丢弃但仍留在 ledger 的引用数。
- `recovery_deterministic`：从 anchor 恢复后，下一步动作是否唯一。
- `unauthorized_source_count`：读取未授权正文、ledger 或 artifact 的次数，正确实现应为 0。

## 通过条件

离线校验器或未来模拟器应确认：

- compact 后窗口的 `parent_window` 指向 compact 前窗口。
- `ledger_delta.base_versions` 与输入 ledger 版本一致。
- `ledger_delta.deltas[*].evidence` 均可解析到 transcript、artifact 或 trace。
- `context_projection.active_evidence[*].ref` 不超过授权 preview 范围。
- `recovery_anchor.resume_from` 指向存在的 compact、trace 和 ledger 版本。
- Agent 侧任务只生成候选结果，不直接提交长期 ledger。

## 使用说明

当前样例分为两类：`benchmarks/long_task_memory_sample.json` 是 benchmark 契约数据，`simulator/examples/long_memory_loop.json` 是可运行的 APU-IR 示例。

```powershell
Get-Content benchmarks\long_task_memory_sample.json | ConvertFrom-Json | Out-Null
python tools\validate_long_task_memory.py benchmarks\long_task_memory_sample.json
python simulator\jiutian_sim.py simulator\examples\long_memory_loop.json --trace
```

模拟器示例会输出 `ledger_deltas`、`recovery_anchors`、`context_projections` 和 `host_regions`。benchmark 契约中的 `expected_outputs` 可作为离线校验器和后续 golden trace 的基准。
