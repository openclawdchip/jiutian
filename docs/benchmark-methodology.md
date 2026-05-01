# Benchmark 方法

九天 benchmark 的目标不是证明“所有场景都更快”，而是识别 Agent 原生架构真正具备结构性优势的工作负载。

## 基本原则

- 每个 benchmark 必须有清晰 workload 定义。
- 每个性能主张必须说明 baseline。
- 优先报告吞吐、延迟、内存流量和同步次数。
- 预估能耗时必须明确 proxy，例如访存次数、NoC flit 数或指令类别权重。
- 不把合成峰值 FLOPS 当作主要指标。

## v0.1 工作负载类别

### 规则执行

大量短分支、短生命周期的规则判断，例如策略过滤、权限检查、事件分类。

### 结构化数据流水线

JSON、日志、表格记录等结构化数据的解析、过滤、变换和聚合。

### 图遍历

依赖图、任务图、工具调用图和轻量知识图谱遍历。

### 短生命周期 JIT 片段

由 Agent 按任务生成、执行一次或少量次数后回收的逻辑片段。

### 工具调用编排

Agent 在多个工具、状态和约束之间做高并发调度的逻辑。

### 非规则内存微基准

测试 SPM、Cluster SRAM、DMA、barrier 与 flush/invalidate 的开销边界。

## Claude Code 类 Agent runtime 场景

已有 AI Brain 文档已经把 Claude Code 类 `src` 样本消化为数字 Agent runtime 工作负载。九天 benchmark 不复制该源码，也不把它作为依赖，而是吸收其负载形态：REPL、消息流、工具调用、权限判断、MCP、子进程、文件系统、diff/patch、会话恢复、compact 和子 Agent 协同。

这类软件对九天尤其重要，因为它把 Agentic workload 从抽象口号变成可测场景。

### 场景 A：ToolUse 批次预处理

输入是一批模型生成的 `ToolUse`：

- 多个 read-only 文件读取或搜索。
- 一个潜在写入动作。
- 若干路径、参数、权限 class 和 timeout。

九天路径：

1. Super Domain 接收 `ToolUse` 并构造 `CommandDescriptor`。
2. 只读批次降低为 APU-IR，进入 Agent Domain。
3. Clawd-Agent 并行执行 schema 检查、路径分类、风险标记和并发安全分组。
4. Super Domain 根据结果决定哪些工具可并发、哪些必须串行或询问用户。

指标：

- 每 1000 个 descriptor 的处理延迟。
- 每个 descriptor 的平均分支数和内存访问数。
- Agent Domain 与单线程 CPU 的吞吐比。
- capability 拒绝路径的 trace 完整性。

### 场景 B：工具结果投影与上下文预算裁剪

输入是一组 tool result、文件片段、搜索结果和 artifact pointer。目标是在有限上下文预算内生成模型可见投影视图。

九天路径：

1. Super Domain 将原始 tool result 存入 host 区域。
2. Agent Domain 对结果做摘要候选、去重、哈希、排序和引用关系整理。
3. 输出 compact 候选、保留引用、丢弃引用和风险标记。
4. Super Domain 写入 transcript，并决定是否触发 compact。

指标：

- 大结果外置后的摘要吞吐。
- host 到 SPM/Cluster SRAM 的 DMA 字节数。
- 去重和排序阶段的 barrier 次数。
- 同等预算下保留有效引用的比例。

### 场景 B2：Memory 召回与 compact 边界

输入是一组长期 memory header、session memory、recent transcript window、artifact pointer 和当前用户请求。目标是在固定预算内产生下一轮上下文投影。

九天路径：

1. Super Domain 提供 memory header manifest、最近 transcript window 和 artifact metadata。
2. Agent Domain 执行 header 扫描、mtime 排序、类型过滤、重复引用去重和预算 packing。
3. Agent Domain 输出 memory refs、artifact refs、compact 保留列表和丢弃列表。
4. Super Domain 决定是否读取 memory 正文、是否写 compact boundary、是否更新 session memory。

指标：

- 每 200 个 memory header 的扫描和排序延迟。
- 在 50K token 等价预算内的引用选择吞吐。
- artifact pointer 去重率。
- compact 前后 transcript 链可恢复性。
- session memory delta 提取的误删率和重复率。

### 场景 B3：长任务账本更新与断点恢复

输入是一段跨越多个 compact boundary 的长任务事件流，包括用户目标修正、工具调用、文件修改、测试输出、失败重试、被拒绝方案和子 Agent 结果。目标是验证九天能否在模型上下文被压缩后，仍然恢复出正确的当前任务状态。

九天路径：

1. Super Domain 提供 transcript window、artifact preview、已提交 ledger 版本和 compact boundary。
2. Agent Domain 执行 `ledger_delta_extract`，生成 Goal/Plan/Evidence/Decision/Recovery 的候选 delta。
3. Agent Domain 执行 `recovery_anchor_select`，选择最小可恢复证据集。
4. Agent Domain 执行 `context_budget_pack`，生成下一轮 `ContextProjection`。
5. Super Domain 审核 delta、提交 ledger，并把投影送回模型。

指标：

- compact 后当前阶段恢复准确率。
- 已完成步骤误删率。
- 被拒绝方案重复尝试率。
- evidence ref 可解析率。
- recovery anchor 可恢复率。
- 每 1000 条工具事件的 ledger delta 生成延迟。
- projection 在固定 token 预算下保留关键约束的比例。

### 场景 C：权限规则与危险命令预筛

输入是 shell、文件写入、网络或 MCP 调用 descriptor。目标是先给出 allow、ask、deny 或 passthrough 建议。

九天路径：

1. Super Domain 保留最终权限权力。
2. Agent Domain 对字符串、路径、命令模式、规则表和历史拒绝记录做快速匹配。
3. 输出 `PermissionDecision` 候选与 reason code。
4. Super Domain 根据策略、用户模式和 UI 状态做最终决策。

指标：

- 规则表规模变化下的延迟。
- deny/ask/allow 三类路径的分支失败 proxy。
- 错误分类可解释性。
- 恶意或格式错误 descriptor 的 trap 覆盖。

### 场景 D：子 Agent 结果归约

输入是多个 sidechain worker 的结构化结果、trace、usage 和 recovery entry。目标是合并成主 turn 可消费的结果。

九天路径：

1. Super Domain 管理 worker 生命周期和 transcript。
2. Agent Domain 并行检查 worker 输出 schema、状态 delta、冲突字段和恢复引用。
3. 输出合并后的 `ExecutionResult`、冲突列表和建议恢复入口。
4. Super Domain 决定提交、重试、询问用户或终止 worker。

指标：

- worker 数量增长时的归约延迟。
- 冲突检测覆盖率。
- trace 与恢复入口的完整性。
- Agent Domain deadlock 和 timeout 处理。

## 最小报告格式

每个 benchmark 文件应包含：

- 任务描述。
- 输入规模。
- 数据分布。
- 九天实现路径。
- baseline 实现路径。
- 指标定义。
- 运行命令。
- 结果解释。

## v0.1 Baseline

早期 baseline 可以先采用：

- Python reference：验证语义正确。
- 单线程 C/Rust：验证传统顺序执行基线。
- 多线程 CPU：验证传统共享内存并发基线。
- 九天模拟器：验证 Agent plane 执行模型。

等模拟器稳定后，再引入更具体的 CPU/GPU/NPU 对比。

## 长期任务记忆报告格式

涉及长期记忆的 benchmark 还应额外报告：

- compact 次数和每次 compact 前后的 transcript 边界。
- ledger 基线版本和提交后的版本。
- Goal/Plan/Evidence/Decision/Recovery 五类 ledger 的 delta 数量。
- 被投影进上下文的引用数量。
- 被丢弃但保留在 ledger 中的引用数量。
- 恢复测试：从任意 compact 后启动，是否能继续执行正确下一步。
