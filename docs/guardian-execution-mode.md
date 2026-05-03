# Guardian-Execution 模式

Guardian-Execution（守护者-执行者）模式是九天 APU 的非对称多核协作原则。它把 Clawd-Agent 定义为系统的常驻守护核心，把 Clawd-Super 定义为面向高熵任务的战略协处理器。二者不再是传统意义上的“大核主控、小核从属”，而是形成一种以能效为中心的按需唤醒关系。

## 设计动机

传统异构多核通常把高性能大核视为系统主控，小核负责低优先级后台任务。九天选择相反方向：Agentic 系统的大多数时间并不需要满功耗运行复杂 OS 路径，而是需要持续监听、维护记忆、筛选事件、整理上下文、执行简单自治逻辑，并在真正出现复杂人类任务时迅速唤醒高性能资源。

因此，九天把默认在线状态交给 Clawd-Agent，把爆发式高性能状态交给 Clawd-Super。这种模式的目标不是降低 Super Core 的重要性，而是让它只在值得消耗高功耗预算时出现。

## 角色分工

| 角色 | 默认状态 | 主要职责 | 能耗目标 |
| :--- | :--- | :--- | :--- |
| Clawd-Agent | Always-On | 后台心跳、环境监听、任务队列维护、简单意图识别、上下文投影、候选 delta 生成、内存与 trace 整理 | 极低电压/频率，维持机器最低生命体征 |
| Clawd-Super | Power-Gated / Clock-Gated | LLM 推理、大规模编译、复杂人类软件、重度感知处理、高风险副作用提交、系统级恢复 | 高性能爆发，任务完成后快速回到休眠 |

在这个模型中，Clawd-Agent 更像系统的管家核心，负责让机器持续“醒着”；Clawd-Super 更像高熵任务战略协处理器，只在需要复杂语义、强兼容性或重负载计算时被唤醒。

## 唤醒与交接协议

Guardian-Execution 模式定义一条硬件可实现的软件可观察路径：

1. **Listening Phase**：Clawd-Agent 拦截来自人类、传感器、网络 API、工具事件或定时器的输入。
2. **Intent Classification**：Agent 域中的微型意图识别单元、规则表或硬化匹配电路判断请求是否属于高熵任务。
3. **Wake Signal**：当请求需要自然语言深推理、传统软件栈、重负载数学运算或真实外部副作用时，Agent 域发出 `WAKE_UP_SUPER` doorbell。
4. **Context Handoff**：Agent 域把任务描述符、输入引用、capability 请求、上下文投影和恢复点写入共享 L3 slice、Cluster SRAM、HBM 或 host memory 中的 handoff mailbox。
5. **Execution Burst**：Clawd-Super 上电或解门控后读取任务指针，承担主要计算、模型调用、传统软件执行或最终提交。
6. **Background Guarding**：Clawd-Agent 退回后台，继续监控超时、温度、总线状态、trace 和异常。
7. **Return to Guard**：任务完成后，Clawd-Super 将结果、提交状态和错误信息写回 mailbox，随后进入 clock-gated 或 power-gated 状态。

## 高熵任务判定

以下请求通常触发 Super Core：

- 需要 LLM 推理、长上下文采样或复杂自然语言理解。
- 需要完整 OS、文件系统、网络栈、子进程或用户确认。
- 需要大规模软件编译、链接、测试或包管理。
- 需要重度感知数据处理、数学库、向量库或外部加速器编排。
- 需要真实外部副作用提交，例如写文件、发布、刷写固件或控制设备。
- Agent 域出现不可恢复 trap，需要系统级恢复或安全审计。

以下请求应尽量留在 Agent Core：

- 心跳、看门狗、低速传感器轮询和环境状态整理。
- 权限规则预筛、路径分类、命令风险标记。
- transcript、ledger、artifact preview、trace 的去重、索引和上下文预算裁剪。
- 简单事件响应、任务队列维护和恢复点候选生成。
- 已授权、无外部副作用、短生命周期的 APU-IR 任务。

## 硬件接口

v0.1 规格阶段只定义语义边界，不强制最终寄存器编码。后续 RTL 可把下列对象映射为 MMIO、mailbox、interrupt controller 或 power manager：

- `WAKE_UP_SUPER`：Agent 域向 power manager 发出的唤醒请求。
- `SUPER_READY`：Super 域完成上电、时钟稳定和最小 runtime 恢复后的确认。
- `HANDOFF_MAILBOX`：保存任务指针、输入引用、capability 请求和恢复点的共享窗口。
- `SUPER_SLEEP_REQUEST`：Super 域完成任务后请求重新门控。
- `GUARD_HEARTBEAT`：Agent 域持续写入的生命体征、队列深度和异常摘要。
- `WAKE_REASON`：记录唤醒原因，便于 benchmark 统计动态功耗收益。

## 软件栈适配

Guardian-Execution 要求编译器、runtime 和调度器共同支持任务分级：

- 编译器应把代码分为 Agent maintenance path 与 Super burst path。
- Runtime 应为每个任务标注 entropy class、side-effect class、latency budget 和 wake policy。
- Scheduler 应支持预测性唤醒：在人类输入尚未完成、但已经高度可能触发高熵任务时，提前预热 Super Core。
- Trace 应记录唤醒原因、门控延迟、handoff 延迟、Super 占空比和任务完成后的回眠时间。

## 架构收益

- **动态功耗范围更大**：无人交互时，九天可保持 Agent Core 低功耗在线；需要人类任务时，再释放 Super Core 的爆发性能。
- **系统寿命更长**：Super Core 低占空比运行可降低热密度，减缓器件老化，并减轻边缘机器人、商业航天和无人系统的散热压力。
- **安全隔离更强**：Agent Core 作为常驻安全堡垒，即使 Super Core 因复杂软件崩溃，也可以执行复位、回收和降级策略。
- **任务恢复更自然**：长期 ledger、artifact preview 和 recovery anchor 常驻在 Agent 域维护，Super Core 被唤醒时可以直接接手结构化上下文。

Guardian-Execution 模式让九天不只是拥有两类核心，而是拥有一套机器生命节律：低功耗守护、按需唤醒、高熵爆发、完成后回到守护。
