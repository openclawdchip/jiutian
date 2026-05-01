# 模拟器指南

九天 v0.1 模拟器是功能模型，用于验证 APU-IR、Agent ISA、SPM、Cluster SRAM、DMA、barrier、capability 和任务边界。

## 当前支持能力

- 多任务 round-robin 调度。
- SPM 与 Cluster SRAM 读写。
- host memory capability 检查。
- DMA copy 与 DMA wait。
- barrier 阻塞、释放与 deadlock 检测。
- flush、invalidate、fence trace。
- cycle budget 检查。
- JSON trace 输出。
- host 文本与 byte 初始化。
- host region 文本导出。
- 长期任务记忆高层 op：`ledger_delta_extract`、`recovery_anchor_select`、`context_budget_pack`/`context_projection`。

## 运行命令

```powershell
python simulator\jiutian_sim.py simulator\examples\copy_add.json
python simulator\jiutian_sim.py simulator\examples\cluster_barrier.json --trace
python simulator\jiutian_sim.py simulator\examples\long_memory_loop.json --trace
python tools\validate_long_task_memory.py benchmarks\long_task_memory_sample.json
```

`long_memory_loop.json` 会运行三个无外部副作用的高层任务，并在输出中暴露：

- `ledger_deltas`：候选长期记忆 delta。
- `recovery_anchors`：候选恢复点。
- `context_projections`：下一轮模型上下文投影。
- `host_regions`：对应 host 输出区的原始 JSON 文本。

`tools\validate_long_task_memory.py` 是离线 benchmark 契约校验器，用于检查长期任务记忆样例中的 compact 链、ledger base version、delta evidence、context projection 引用预算和 recovery anchor 是否自洽。

## 设计边界

当前模型不是周期精确模型。DMA 可以先按同步完成处理；异步 DMA、队列深度、NoC 延迟和能耗 proxy 属于后续扩展。

长期任务记忆高层 op 用于验证 APU-IR 数据流和安全边界，不代表最终模型推理质量。它们只能生成 candidate/projection 输出，不提交 ledger，也不写真实 artifact。

## 正确性标准

一个示例至少应验证：

- 输出内存结果正确。
- 未发生非预期 trap。
- trace 中包含关键调度和数据搬运事件。
