# Benchmark

Benchmark 应衡量 Agent 原生架构具备结构性优势的工作负载。

初始分类：

- 短生命周期生成代码片段。
- 规则引擎与决策树。
- JSON 或结构化数据流水线。
- 图与依赖遍历。
- Agent 工具调用编排。
- 非规则内存访问模式。

每个 benchmark 应报告：

- 工作负载定义。
- 输入规模与分布。
- Baseline 实现。
- 运行时配置。
- 吞吐。
- 延迟。
- 内存流量。
- 可用时提供能耗 proxy 或功耗测量。

## 已有样例

- [`long_task_memory.md`](long_task_memory.md) - 长期任务记忆 benchmark 定义，覆盖 compact、ledger delta、context projection 与 recovery anchor。
- [`long_task_memory_sample.json`](long_task_memory_sample.json) - 可作为模拟器扩展、trace 生成器或离线校验器输入的结构化样例。
