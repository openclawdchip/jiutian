# 从 SPEC 到 Agentic Benchmark

## 1. Benchmark 是体系结构的语言

计算机体系结构不是只靠结构图前进的学科。一个新架构要被讨论，必须先说明它在什么工作负载上有意义，再说明如何测量这种意义。《Computer Architecture: A Quantitative Approach》建立的传统可以概括为四句话：定义 workload，选择 baseline，报告可测指标，解释性能与代价的取舍。

SPEC 的价值正在这里。它并不声称一个整数或浮点程序代表全部计算，而是用一组相对稳定、可复现、可比较的程序，迫使处理器设计者面对真实编译器、真实内存层次和真实控制流。后来 MLPerf 把这种思想带到机器学习系统：不仅测算子峰值，也测训练、推理、数据输入、精度约束和系统提交规则。

Agent CPU 也需要同样的纪律。不能只说“更适合 Agent”，而要回答：哪些 Agentic workload 被加速？哪些状态被保留？哪些错误被拦截？中断后能否恢复？安全边界是否可解释？

## 2. SPEC 与 MLPerf 的启发和局限

SPEC 提醒我们，benchmark 必须避免只优化一个微小内核。MLPerf 提醒我们，端到端任务、精度门槛和提交规则同样重要。但二者对 Agent CPU 都不够。

传统 SPEC 主要面对确定性程序：输入固定、输出可判等、进程生命周期清楚。Agent 任务则常常跨越多轮对话、工具调用、文件修改、权限询问和 compact boundary。MLPerf 虽然接近 AI 系统，但多数项目仍把模型调用作为中心事件，而 Agent CPU 的瓶颈常在模型外：工具事件扫描、ledger delta 生成、context projection、artifact preview、权限预筛和 recovery anchor 选择。

因此，Agentic Benchmark 不应替代 SPEC 或 MLPerf，而应继承它们的定量精神，并改变测量对象。

| 传统 benchmark 思想 | Agentic Benchmark 中的转化 |
|---|---|
| 固定输入程序 | 固定任务事件流、工具结果、ledger 和 artifact |
| 正确输出 | 可验证结论、证据引用、状态 delta 与提交记录 |
| 执行时间 | admission、projection、commit、recovery 分阶段延迟 |
| 吞吐 | 每秒处理 ToolUse、ledger delta、context section 的数量 |
| 精度约束 | evidence coverage、约束保留率、恢复准确率 |
| 提交规则 | capability trap、candidate-only side effect、可复现实验包 |

## 3. 微基准：隔离 Agent CPU 的机制

微基准用于测量单个结构是否值得存在。对 Agent CPU 而言，第一批微基准不应围绕 FLOPS，而应围绕任务状态流：

- `capability_check`：测 region lookup、权限判断、trap 定位精度。
- `ledger_delta_extract`：测从事件流中提取 Goal、Plan、Evidence、Decision 的吞吐。
- `context_budget_pack`：测在固定 token/ref 预算下保留关键约束的比例。
- `artifact_preview_scan`：测大量文件摘要、hash、mtime 和引用关系的扫描效率。
- `recovery_anchor_select`：测 compact 或中断后恢复点的选择质量。
- `candidate_patch_score`：测候选修改的风险分类与可解释性。

这些微基准的目标不是证明整个系统有用，而是像 cache miss latency、branch misprediction penalty 那样，给架构设计者一个可以定位瓶颈的尺子。

## 4. 宏基准：端到端的长任务

宏基准用于回答“这个架构是否真的服务 Agent”。一个合格的宏基准应包含长任务记忆，即 `long_task_memory` 类负载：用户目标会变化，工具调用会失败，文件会被部分修改，模型上下文会被 compact，系统必须在几小时甚至几天后恢复当前任务。

一个典型宏基准可以这样定义：输入包括 transcript window、artifact preview、已提交 ledger、compact boundary 和 trace window；输出包括 ledger delta、context projection、recovery anchor 和 candidate side effect。评价时不仅看最终答案是否正确，还要看是否重复尝试已拒绝方案，是否误删已完成步骤，是否保留关键用户约束，是否能解释每个提交的证据来源。

可将总时间拆成：

```text
T_total =
  T_admit
  + T_tool_event_scan
  + T_ledger_delta_extract
  + T_context_pack
  + T_super_review
  + T_recover_if_needed
  + T_model_wait
```

Agent CPU 未必能减少 `T_model_wait`，但它应降低模型外状态处理时间，并提高恢复确定性。

## 5. 指标：正确性、安全与恢复同等重要

Agentic Benchmark 的核心指标应分为三类：

| 类别 | 指标示例 | 含义 |
|---|---|---|
| 正确性 | output match、evidence coverage、constraint retention | 结果是否正确，是否能回指证据，是否保留关键约束 |
| 安全性 | capability violation recall、trap precision、bad commit rate | 越权是否被捕获，trap 是否定位到 task/region/reason，错误副作用是否提交 |
| 恢复性 | recovery success、anchor minimality、redo rejected path rate | compact、中断或失败后能否回到正确阶段，恢复集是否最小，是否重复旧错误 |

这意味着一个系统即使更快，如果 evidence coverage 下降、trap 不可解释、恢复后丢失用户目标，也不能被判定为更好的 Agent CPU。

## 6. 最小报告格式

每个 Agentic Benchmark 报告至少应给出：任务描述、输入规模、事件分布、baseline、Agent Domain 路径、正确性判定、权限模型、恢复场景、运行命令和失败样例。早期 baseline 可采用 Python reference、单线程 CPU、多线程 CPU 和九天功能模拟器。报告必须同时列出平均延迟和 tail latency，因为长任务中一次极慢的恢复可能破坏整个交互体验。

## 本章习题

1. 为什么 SPEC 的“可复现工作负载套件”思想对 Agent CPU 仍然重要？
2. 设计一个包含 1000 条 ToolUse、3 次 compact 和 1 次权限拒绝的宏基准，说明输入、输出和指标。
3. 如果某 Agent CPU 把 `context_budget_pack` 加速 5 倍，但 constraint retention 从 98% 降到 85%，应如何评价？
4. 用 Amdahl 定律分析：当 `T_model_wait` 占 70% 时，优化 `ledger_delta_extract` 和 `recovery_anchor_select` 仍有什么价值？
