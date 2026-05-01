# 从 Branch Prediction 到 Task-State Recovery

## 1. 从控制流预测到任务流预测

传统 CPU 的分支预测解决一个朴素问题：当前端还不知道下一条真实指令在哪里时，是否可以先猜一个方向继续取指？现代高性能处理器通常由 BPU 给出方向与目标，FTQ 保存已经预测过的取指块，后端执行到分支指令后再验证预测是否正确。若预测正确，流水线几乎无感继续前进；若预测错误，机器清空错误路径上的指令，从正确 PC 重新取指。

这个机制的本质不是“猜得准”四个字，而是三件事：第一，预测必须有边界；第二，预测路径必须留下足够元数据；第三，错误预测必须能恢复到架构上正确的状态。Agent CPU 面临的不是指令地址选择，而是任务路径选择。例如，Agent 在修复一个测试失败时，可能先判断是接口变更、配置错误、依赖版本问题，还是测试本身过期。每一种判断都会引出不同的工具调用、文件读取和代码修改。这里同样需要预测，但预测对象从 branch direction 变成了 task direction。

## 2. FTQ/BPU 的可继承思想

FTQ 可以理解为前端对“我刚才按什么路径取过指”的顺序记录。它不保存全部执行结果，却保存恢复所需的前端轨迹：预测 PC、目标地址、分支类型、命中信息等。Agent CPU 中也需要类似结构，可称为 Task Flow Queue。TFQ 不记录每个 token 的全部内容，而记录任务级预测路径：当前目标、候选假设、计划阶段、工具调用意图、依赖证据和预算。

| 传统 CPU 机制 | 作用 | Agent CPU 对应物 |
|---|---|---|
| BPU | 预测分支方向与目标 | Task Predictor，预测下一步任务路径 |
| FTQ | 保存取指预测轨迹 | TFQ，保存任务流预测轨迹 |
| ROB | 支持乱序执行与顺序提交 | Candidate Ledger Buffer，保存候选状态增量 |
| redirect | 错误预测后重定向取指 | task redirect，回到可信任务状态 |
| commit | 架构状态正式可见 | ledger delta 提交 |

这个类比的边界也很重要。传统 BPU 的错误代价主要是周期损失；Agent 任务预测错误可能造成错误文件修改、错误证据引用、错误安全授权，甚至把 compact 后的摘要带偏。因此 Agent CPU 的预测不能只优化命中率，还必须优化可恢复性。

## 3. 错误预测恢复的任务化

在指令流水线中，错误预测恢复依赖清晰的架构状态：寄存器、内存顺序、ROB 提交点。Agent 的状态更复杂，至少包括用户目标、计划、证据、工具输出、候选代码、权限、trace 和 ledger。若这些状态被自然语言上下文混在一起，恢复就会退化成“重新读聊天记录”。这对长任务是不可靠的。

因此，Agent CPU 应把任务状态拆成两层：

1. **speculative task state**：尚未提交的假设、草稿修改、候选 ledger delta、临时 trace。
2. **committed task state**：已验证证据、已接受决策、已提交 ledger、可审计 recovery anchor。

当任务预测失败时，机器不应撤销整个会话，而应撤销最近一次提交点之后的候选状态。一个典型流程如下：

1. Task Predictor 选择候选路径，例如“失败来自 API 兼容性”。
2. Agent 执行若干工具调用，生成 trace 与候选修改。
3. Verifier 发现测试或证据不支持该假设。
4. Runtime 标记 TFQ 中对应路径为 mispredicted。
5. Candidate Ledger Buffer 丢弃未提交 delta。
6. 系统从最近 recovery anchor 恢复，并选择新路径。

这里的 recovery anchor 类似传统体系结构中的精确异常点：它必须说明“恢复到哪里”“哪些状态可信”“哪些副作用需要补偿或丢弃”。

## 4. Trace 不是日志，而是恢复材料

很多系统把 trace 当作事后调试日志。Agent CPU 中，trace 是恢复路径的一部分。它至少要回答：哪一个目标触发了这步行动？读取了哪些文件？调用了哪些工具？输出的证据是否被引用？决策为何被接受或拒绝？哪些修改仍是候选状态？

为了避免 trace 自身无限膨胀，trace 应分层保存。热路径只保存恢复必要字段，例如 task id、anchor id、evidence hash、tool result digest、dirty artifact 列表；冷路径可以保存完整 transcript、命令输出和 artifact。compact 发生时，系统不应只生成摘要，而应生成一次 compact transaction：从 trace 中抽取约束、证据、未完成步骤和最近 anchor，写入 RecoveryLedger，再投影成新的上下文。

## 5. Compact 后恢复

compact 的危险在于它会把“状态”伪装成“文字”。如果摘要遗漏了禁止事项、失败路径或未提交修改，Agent 可能在恢复后重复错误预测。正确做法是让 compact 依赖 recovery anchor，而不是依赖模型记忆。

一个 compact 后恢复协议可以包含四步：第一，加载最近已提交的 GoalLedger、PlanLedger、EvidenceLedger 和 RecoveryLedger；第二，检查 TFQ 中是否存在未闭合任务路径；第三，依据 recovery anchor 重建最小工作上下文；第四，将未提交候选状态显式标为 pending、discarded 或 need-verify。这样，Agent 恢复的不是一段聊天，而是一个可继续执行的任务状态。

从 Branch Prediction 到 Task-State Recovery 的关键转变是：预测仍然重要，但预测必须服从提交、审计和恢复。Agent CPU 不追求永远不走错路，而追求走错路后能够知道错在哪里、丢弃什么、保留什么，并从正确的任务状态继续前进。

## 本章习题

1. 传统 CPU 中 FTQ 与 ROB 的分工是什么？请说明它们分别给 Agent CPU 的 TFQ 与 Candidate Ledger Buffer 带来什么启发。
2. 为什么 Agent 任务预测错误的代价不能只用“浪费时间”衡量？请结合工具调用和文件修改举例。
3. 设计一个 recovery anchor 的最小字段集合，要求支持 compact 后恢复。
4. 若一次 compact 摘要遗漏了“某方案已被验证失败”的信息，系统应如何利用 trace 或 ledger 阻止 Agent 重复该路径？
