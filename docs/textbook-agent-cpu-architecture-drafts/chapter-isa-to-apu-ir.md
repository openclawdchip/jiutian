# 从 ISA 到 APU-IR

## 1. ISA 作为软硬件契约

传统计算机体系结构中，ISA 是软件与硬件之间最重要的边界。编译器、操作系统和应用程序面对的是指令、寄存器、异常、内存模型和特权级；微架构则可以在这个边界之下自由选择流水线、乱序执行、缓存层次和预测机制。只要 ISA 语义不变，同一二进制程序就可以在不同实现上运行。

RISC-V 的启发尤其清楚：一个好的 ISA 不只是指令表，而是一套可扩展、可验证、可教学的公共契约。基础整数指令集保持小而稳定，乘除法、原子操作、向量、压缩指令和自定义扩展则按需要组合。它把“什么必须稳定”和“什么可以扩展”分开，使学术原型、嵌入式小核和复杂 SoC 可以共享同一套思想。

Agent CPU 也需要类似契约，但契约边界发生了上移。Agent 生成的逻辑往往不是长期维护的二进制程序，而是围绕一次目标、一次工具调用批次或一次上下文投影生成的短生命周期任务。此时，硬件真正需要理解的不是单条加法或加载指令，而是：这个任务要访问哪些证据，能使用哪些 capability，预算是多少，输出会写到哪里，失败后如何解释。

## 2. 为什么仅有 Agent ISA 不够

可以把 Agent ISA 理解为 Agent Domain 中的低层执行语义：访存、拷贝、比较、分支、barrier、flush、trace event 等。它仍然重要，因为最终执行必须落到确定的机器步骤上。但是，如果只定义低层 ISA，就会丢失 Agent workload 最有价值的高层信息。

例如，一个 `context_budget_pack` 任务在低层看可能只是读取 ledger、筛选引用、拼接文本、写入缓冲区；在高层看，它其实是在给下一轮模型推理构造上下文投影。后者天然包含 token budget、证据优先级、引用上限、恢复点和 trace 策略。如果这些信息只藏在指令序列里，Super Domain 就很难在准入阶段判断任务是否越权、是否超预算、是否会破坏已提交 ledger。

因此，Agent CPU 需要两层契约：低层 Agent ISA 保证执行可落地，高层 APU-IR 保证任务可验证、可调度、可恢复。

## 3. APU-IR 的位置

APU-IR 是 Agent Runtime 与 Agent Domain 之间的任务图中间表示。它不是自然语言，也不是传统源代码；它是进入硬件或模拟器前必须被检查的结构化对象。

一个最小 APU-IR task 应描述：

- `goal` 或 `op_class`：任务意图，例如扫描、打包、抽取、选择恢复点。
- `inputs` 与 `outputs`：输入证据、memory region、artifact preview 或 trace window。
- `capability`：任务可读、可写、可执行、可追加的资源边界。
- `budget`：cycles、SPM bytes、cluster bytes、token budget、trace bytes 等。
- `placement` 与同步：运行在哪个 cluster/core，依赖哪些 barrier。
- `trace_policy`：哪些事件必须记录，哪些可以摘要化。

在这个模型中，Agent Task 不再只是一个线程或进程，而是带有权限、预算、证据和审计要求的状态变换。Super Domain 负责 admission：检查格式、capability、预算和依赖；Agent Domain 负责执行：按照降低后的 Agent ISA 或硬件单元完成任务，并在 trap 或完成时返回结构化结果。

## 4. 从 RISC-V 扩展思想到 APU-IR 扩展

RISC-V 通过标准扩展和自定义扩展解决“基础稳定、能力增长”的矛盾。APU-IR 也应采用类似思路。基础 task schema 必须稳定，例如 task id、capability、budget、memory region、trace 字段；高层 `op_class` 则可以持续扩展，例如：

- `ledger_delta_extract`：从执行结果中抽取可提交状态变化。
- `context_budget_pack`：在 token 或 byte 预算内生成上下文投影。
- `recovery_anchor_select`：从 trace 与 ledger 中选择恢复点。
- `artifact_preview_pack`：为模型构造受限 artifact 预览。
- `memory_header_scan`：快速扫描文件、对象或缓冲区头部。

这些高层操作未来可以降低为不同实现：软件 runtime、Agent ISA 指令序列、DMA 加速路径、专用硬件单元，甚至 RISC-V 自定义协处理器接口。关键不是一开始就固定二进制编码，而是先把任务语义固定下来。

| 传统体系结构概念 | Agent CPU 对应概念 | 设计关注点 |
|---|---|---|
| ISA | Agent ISA 与 APU-IR | 低层执行语义与高层任务契约分离 |
| ABI | Task schema | Runtime、模拟器、硬件之间交换任务对象 |
| 特权级 | Super Domain / Agent Domain | 准入、隔离、trap 和资源回收 |
| 地址空间 | capability-bounded memory region | 访问权由任务显式声明并被检查 |
| 性能计数器 | budget 与 trace | 资源消耗可解释，失败点可定位 |
| 异常 | task trap | 返回 task、pc、capability、reason 和证据引用 |

## 5. 预算、权限与 trace 的共同语义

在传统 CPU 中，权限主要围绕地址空间和特权指令；性能主要由计数器事后观察；调试依赖断点、异常和日志。Agent CPU 则应把三者前置到任务契约中。

`capability` 回答“允许做什么”。它可以限制某个 task 只能读取 ledger 摘要、只能向候选输出区追加、不能覆盖已提交 artifact。`budget` 回答“最多消耗多少”。它不仅包括 cycles 和内存，也包括 token、引用数量、trace 字节数。`trace` 回答“如何解释发生了什么”。一次正确输出如果无法回指证据和执行路径，在 Agent 系统中仍是不完整的输出。

三者必须同时出现。只有 capability 没有 budget，任务可能合法但失控；只有 budget 没有 capability，任务可能高效地越权；只有二者没有 trace，任务失败后无法恢复，也无法教学、调试或审计。

## 6. 小结

从 ISA 到 APU-IR，不是抛弃传统计算机体系结构，而是继承它最核心的分层思想。ISA 告诉我们：稳定契约使软件生态和硬件实现可以独立演进。APU-IR 则把这个思想推进到 Agent 时代：当程序由 Agent 即时生成时，契约必须覆盖任务意图、证据、权限、预算、恢复和 trace。

因此，Agent CPU 的设计顺序应当是：先定义 Agent Task 与 APU-IR 的可验证语义，再定义如何降低到 Agent ISA，最后再决定二进制编码、硬件流水线和专用加速路径。这样得到的机器不是“会运行更多指令”的 CPU，而是能理解、限制、审计和恢复 Agent 行为的计算平台。

## 习题

1. 解释为什么 RISC-V 的开放扩展思想适合启发 APU-IR，但 RISC-V 小核本身不能直接等同于 Agent Core。
2. 为 `recovery_anchor_select` 设计一个最小 APU-IR task，至少包含 capability、budget、输入、输出和 trace_policy。
3. 某 task 有合法 capability，但缺少 token budget。它应该在准入阶段被拒绝，还是运行时 trap？说明理由。
4. 对比传统 ISA 异常和 Agent task trap：为什么后者需要同时记录 task id、pc、reason、capability 和 evidence ref？
