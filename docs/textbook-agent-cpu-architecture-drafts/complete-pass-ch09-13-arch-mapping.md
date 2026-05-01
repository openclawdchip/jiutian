# 第 9-13 章 传统体系结构映射篇 教材化替换稿

## 第 9 章 从 ISA 到 APU-IR

传统计算机体系结构中，ISA 是软件与硬件之间最重要的契约。程序员、编译器和操作系统面对的是指令、寄存器、异常、地址空间和内存模型；硬件实现者则可以在契约之下选择流水线、缓存、乱序执行、预测和互连方式。只要 ISA 所承诺的行为稳定，同一段程序就可以在不同微架构上运行。这种分层思想是现代计算机能够持续演进的根基：上层软件不需要知道每个执行单元怎样调度，下层硬件也不必理解应用程序的全部意图。

Agent CPU 继承这一思想，但契约边界需要上移。传统程序通常由人类或编译器提前写好，二进制形态相对稳定；Agent 工作负载则常常围绕一次目标、一次工具调用、一次上下文整理或一次候选修改即时生成。硬件与运行时真正需要识别的，不只是“执行哪条指令”，还包括“这个任务要处理什么证据”“可以访问哪些资源”“预算是多少”“输出应写入候选区还是提交区”“失败后从哪里恢复”。因此，Agent CPU 需要同时拥有低层的 Agent ISA 和高层的 APU-IR。

Agent ISA 可以理解为 Agent Domain 中最终落地执行的低层语义。它负责搬运、比较、扫描、分支、同步、写入候选缓冲区、产生 trace event 等确定性动作。APU-IR 则位于运行时与 Agent Domain 之间，是任务进入硬件、模拟器或受控执行路径之前的结构化表示。它不是自然语言提示词，也不是普通源代码，而是一种带有目标、输入、输出、权限、预算、同步和 trace 策略的任务对象。

一个最小的 APU-IR task 应当说明六类信息。第一是任务意图，例如扫描证据、打包上下文、抽取账本增量或选择恢复点。第二是输入和输出，包括账本片段、产物预览、trace 窗口、候选结果区等。第三是 capability，也就是本任务被允许读、写、追加或调用的边界。第四是 budget，包括周期、片上存储、上下文容量、trace 字节数或引用数量等资源上限。第五是 placement 与同步，说明任务放在哪个计算单元运行，并依赖哪些 barrier。第六是 trace_policy，说明哪些事件必须记录，哪些事件可以摘要化。

这样设计以后，Agent Task 就不再只是线程或函数调用，而是一次受约束、可审核、可恢复的状态变换。Super Domain 负责准入：检查 task 格式、capability、预算、依赖和目标边界。Agent Domain 负责执行：将 APU-IR 降低为 Agent ISA 指令序列、软件例程或专用执行单元动作，并在完成或 trap 时返回结构化结果。二者分工清楚，既保留硬件执行效率，也保留系统对任务意图的理解。

APU-IR 的扩展也应遵循“基础稳定、能力可增长”的原则。基础 schema 应保持稳定，例如 task id、capability、budget、memory region、trace policy 和依赖关系；高层操作类别可以逐步扩展。例如，ledger_delta_extract 用于从执行事件中抽取可提交的状态变化；context_budget_pack 用于在固定上下文预算内选择最重要的证据；recovery_anchor_select 用于为长任务选择恢复点；artifact_preview_pack 用于把大型产物压缩成可引用预览；memory_header_scan 用于快速扫描文件、对象或缓冲区头部。它们未来可以由软件运行时、Agent ISA 指令序列、DMA 路径或专用硬件实现，但任务语义应先被固定下来。

在 APU-IR 中，capability、budget 和 trace 是共同出现的三类语义。capability 回答“允许做什么”，budget 回答“最多消耗多少”，trace 回答“如何解释发生了什么”。只有权限而没有预算，合法任务也可能无限扩张；只有预算而没有权限，任务可能高效地越过边界；只有权限和预算而没有 trace，任务失败后难以定位，也难以审计和恢复。教材中可以把这三者视为 Agent CPU 的任务三角：权限确定边界，预算确定规模，trace 确定可解释性。

还可以把 APU-IR 看作“任务进入机器前的体检表”。传统程序进入处理器时，硬件主要检查指令是否合法、地址是否可访问、特权级是否允许；Agent Task 进入系统时，检查对象更丰富。一个看似简单的“整理上下文”任务，如果没有说明可读取的账本范围，就可能把不该进入本轮推理的信息带入上下文；如果没有说明输出区域，就可能把临时摘要误写成已提交事实；如果没有说明 trace 策略，后续就难以解释为什么某条证据被保留、另一条证据被丢弃。APU-IR 的教学重点不在字段数量，而在让学生理解：结构化任务描述把模糊意图变成了可检查的机器对象。

传统 ISA 让软件生态和硬件实现可以分离演进；APU-IR 则把这一经验推进到 Agent 时代。当程序由 Agent 即时生成，当上下文会被压缩，当工具调用可能产生真实副作用时，体系结构契约必须覆盖任务意图、证据来源、资源边界、候选结果、恢复点和提交路径。Agent CPU 的设计顺序也因此更加清晰：先定义可验证的 Agent Task 与 APU-IR，再定义如何降低到 Agent ISA，最后再选择编码、流水线和加速单元。

### 本章小结

ISA 的核心价值是稳定契约。Agent CPU 并不抛弃这一传统，而是把契约从单条指令扩展到任务级状态变换。Agent ISA 负责低层执行，APU-IR 负责高层任务语义；Super Domain 负责准入与审核，Agent Domain 负责受控执行。APU-IR 中的 capability、budget 和 trace 共同保证任务可限制、可度量、可解释。

### 本章习题

1. 说明为什么 Agent CPU 既需要低层 Agent ISA，也需要高层 APU-IR。
2. 为 context_budget_pack 设计一个最小 APU-IR task，列出目标、输入、输出、capability、budget 和 trace_policy。
3. 某任务拥有合法 capability，但没有声明上下文预算。它应在准入阶段处理，还是运行时处理？说明理由。
4. 对比传统 ISA 异常和 Agent task trap，解释后者为什么需要记录 task id、原因、权限边界和证据引用。

## 第 10 章 从 Cache 到 Ledger-Aware Memory

传统内存层次围绕局部性建立。寄存器、一级缓存、二级缓存、共享缓存、主存和外存共同形成容量与延迟的梯度。程序访问数组、栈帧、对象和指令流时，硬件通过 tag、替换、预取和一致性协议尽量把热点数据留在近处。对许多长期运行的程序来说，这种透明缓存模型非常有效，因为程序的空间局部性和时间局部性相对稳定。

Agent 工作负载同样需要高带宽与低延迟，但它的“热点”不完全等同于最近访问的字节。一个 Agent Task 可能在短时间内读取目标、扫描证据、生成候选修改、打包上下文、记录 trace、等待审核并提交账本增量。它访问的对象具有任务语义：有些是临时上下文，有些是已提交事实，有些是候选状态，有些是恢复锚点，有些是大型产物的摘要。如果内存系统只看 cache line，就会错过这些语义差异。Ledger-Aware Memory 的目标，是让状态在内存系统中既能高效移动，也能保持可解释的身份。

这并不意味着取消传统 Cache。控制面代码、运行时队列、普通数据结构和小规模热数据仍然适合透明缓存。新的变化在于，Agent 执行面需要叠加语义层次。寄存器和本地状态保存当前 task 的短暂控制信息；SPM 保存当前上下文分片、临时表和局部工作集；Cluster SRAM 保存多个 Agent 阶段共享的中间态；容量层保存 transcript、artifact、ledger 和 trace；context window 保存模型本轮可见的投影；ledger region 保存已提交事实、证据引用和可恢复状态。

这里最容易混淆的是 context window 与真实记忆。context window 不是更大的缓存，也不是系统的权威状态；它是一次推理前从账本、产物和 trace 中生成的投影。投影可以被裁剪、压缩、重排和摘要，只要生成过程可追溯，投影本身不必承担持久化责任。真正需要长期保存和审计的，是 ledger、artifact、trace 和 recovery anchor。教材中应反复强调：上下文用于“看见”，账本用于“记住”，trace 用于“解释如何走到这里”。

Ledger-aware memory 适合使用显式数据移动。一个典型流程是：Super Domain 授权任务可读取的账本片段、产物预览区和候选输出区；Agent Domain 将账本头部、相关 trace 摘要和产物预览搬入 Cluster SRAM；每个 Agent 核再把自己需要的 context section 或候选表搬入 SPM；任务在片上存储中完成筛选、打包、验证或 delta 生成；候选结果写回共享区域，经 barrier 汇合后进入审核路径。显式搬运的价值不仅是性能，还在于可审计：系统知道搬了多少字节、从哪个命名空间到哪个命名空间、为哪个 task 服务、是否越过 capability 边界。

账本语义至少包含四点。第一，写入不等于提交。Agent 可以生成 candidate ledger delta，但不能直接改写已提交 ledger。第二，读取应保留 provenance。一个上下文片段如果引用了某条事实，就应能回指 ledger entry、artifact preview 或 trace summary。第三，替换策略可以考虑语义热度。除了最近访问，还可以考虑任务图依赖、恢复锚点距离、证据复用频率和审计优先级。第四，可见性应显式化。flush、invalidate 和 fence 不只是缓存一致性动作，也可以表达候选状态对下一阶段可见，或某个投影已经失效，需要重新从账本生成。

Artifact preview 是连接大型产物与上下文窗口的重要结构。Agent 经常不需要完整产物，而只需要摘要、schema、关键 diff、失败片段、元数据或引用关系。它类似 cache line，都是从大对象中取出可快速访问的小片段；但二者切分依据不同。cache line 按固定字节宽度切分，artifact preview 按语义边界切分。一个好的 preview 应小到能进入预算，大到足以支撑判断，并且能稳定回指原始 artifact。

Trace 则给内存系统增加时间维度。传统内存更多回答“现在有什么”；Agent CPU 还要回答“状态怎样变成现在这样”。DMA copy、barrier arrive、ledger delta extract、context pack、trap、recovery anchor select 都可以成为结构化 trace event。这样，任务失败时系统不只检查最终快照，还可以沿着 trace 找到错误路径、被忽略的证据或越界的数据移动。

从教学角度看，本章可以用“同一段数据的三种身份”帮助学生建立直觉。同一句约束在 ledger 中是已提交状态，在 context window 中是本轮可见提示，在 trace 中是某次决策被接受的依据。三者内容可能相似，却承担不同责任。ledger 要稳定，context 要适配预算，trace 要说明过程。若把三者混成一个大缓冲区，系统短期上似乎更简单，长期却会失去替换、压缩、提交和恢复的清晰边界。Ledger-aware memory 的核心，不是让每个字节都带上复杂标签，而是在关键状态穿过内存层次时保留它的任务身份。

### 本章小结

Ledger-Aware Memory 不是用账本替代缓存，而是让缓存、片上存储、容量层、上下文窗口、产物预览和 trace 各司其职。Cache 服务普通局部性，SPM 和 Cluster SRAM 服务可声明的 Agent 工作集，context window 服务本轮推理可见性，ledger 保存可审计状态，trace 保存状态演化路径。Agent CPU 的内存指标也应从 cache hit rate 扩展到 projection latency、DMA effective bytes、ledger delta throughput、trace overhead 和 preview reuse rate。

### 本章习题

1. 为什么说 context window 是投影，而不是 Agent CPU 的真实记忆？
2. 比较 cache line 与 artifact preview：二者的切分依据、替换策略和正确性责任有何不同？
3. 设计一个 ledger_delta_extract 的数据移动流程，要求使用 SPM、Cluster SRAM、容量层和显式 DMA。
4. 如果系统只保存最终 ledger，而不保存 trace，会给调试、审计和恢复带来哪些困难？
5. 选择三个指标，用来评价 ledger-aware memory 是否优于只依赖传统缓存的实现。

## 第 11 章 从 ROB Commit 到 Candidate Commit

乱序 CPU 允许指令乱序执行，却必须向软件呈现顺序机器。ROB 承担了这一矛盾：前端按程序顺序分配条目，后端允许指令乱序发射、执行和写回，最终只有当最老的可提交指令完成且没有异常时，体系结构状态才向前推进。寄存器和内存看到的是清晰顺序，而不是执行单元内部的临时混乱。ROB 的关键思想是：内部可以推测，外部必须精确。

Agent CPU 面临相似但更宽的提交问题。Agent 可以并行搜索、调用工具、生成候选补丁、试运行验证、抽取账本增量，也可以在多个假设路径之间来回切换。用户和系统真正关心的，是哪些状态被正式写入：ledger 是否更新，工作区是否改变，外部副作用是否发生，恢复点是否可靠。因此，Agent CPU 需要一个任务级提交边界，这就是 Candidate Commit。

ROB 提供了三条可继承经验。第一，执行与提交分离。乱序执行提升吞吐，但结果不能越过提交边界随意暴露。类似地，Agent Domain 可以高速生成候选物，但不能直接改写真正的账本、文件或外部世界。第二，提交需要顺序。传统 ROB 从 head 开始推进，避免年轻指令越过年长指令破坏精确状态。Agent CPU 中，候选更新也应形成可解释顺序：先确认目标、约束和证据，再提交账本增量；先审核 base 和权限，再让 patch 生效；先记录恢复锚点，再允许受监管副作用发生。第三，异常应精确。任务失败时，系统要能说明哪些状态已经提交，哪些只是候选，哪些已经拒绝，以及可以从哪个安全点继续。

Candidate entry 是任务级 ROB entry。它不只记录目的寄存器和完成位，而是记录候选更新的身份、依赖、权限、证据和审核状态。一个完整 candidate entry 可以包含 base ledger id、task id、capability set、candidate ledger delta、候选副作用缓冲区、patch diff、evidence list、risk score、recovery anchor 和 reject reason。它不是普通日志，而是 Super Domain 可以逐项审核的提交单元。

Candidate-only side effect 是本章最重要的概念之一。它表示 Agent Domain 可以描述想要发生的副作用，但不能直接让副作用成为对外可见事实。例如，Agent 生成补丁时，先写入候选补丁缓冲区；运行验证时，先记录命令、输出摘要、失败定位和资源消耗；涉及真实文件写入、持久账本更新、外部调用或发布动作时，必须由 Super Domain 审核后执行。这样做不是削弱 Agent 的能力，而是让能力拥有清楚边界：意图阶段可以推测、并行和失败，生效阶段必须满足权限、顺序和证据。

Super Domain 在 Candidate Commit 中扮演提交逻辑。典型流程包括：Agent Domain 产生 candidate entry；Super Domain 检查 capability，确认候选没有越权读写，也没有越过候选副作用边界；检查 base，确认 candidate 基于当前 ledger 和工作状态；检查 evidence，确认测试、静态分析、用户约束和风险评分满足策略；审核通过后，按顺序提交 ledger delta，再执行受监管的状态更新；审核失败时，记录 reject reason，并保留足够 trace 供诊断和恢复。

Ledger delta 与 patch 提交关系密切，但不应混为一谈。ledger delta 是体系结构意义上的任务状态更新，它记录目标进展、关键证据、工具结果、约束变化和决策理由。patch 或其他工作区变化是外部状态更新。通常更稳妥的顺序是：先形成候选 ledger delta，说明为什么某个修改可以提交；审核通过后，账本记录提交决策；随后 patch 才进入真实工作区。这样，即使后续出现问题，系统也能追溯修改来自哪个 task、基于哪个 base、满足哪些 capability、对应哪个 recovery anchor。

恢复机制把 Candidate Commit 与任务连续性连接起来。传统 CPU 遇到错误预测或异常时，会清空未提交指令并从正确 PC 重新取指。Agent CPU 的对应动作，是丢弃未提交 candidates，保留 committed ledger，从最近 recovery anchor 重新规划。recovery anchor 不需要保存完整上下文窗口，因为上下文可以从 ledger、artifact 和 trace 重新投影；它需要保存足以重建一致性的锚点，例如 base ledger、未提交候选、脏产物集合、最近证据摘要和下一步可选路径。

Candidate Commit 可以用几条不变量来理解：未审核副作用不对外可见；committed ledger 中每条 delta 都能回指 candidate entry；patch 生效前必须具有 base、权限、证据和恢复锚点；rejected candidate 不能在恢复后被当成事实；用户约束变化会使相关候选失效。掌握这些不变量，就能把 Agent 的自治执行转化为可审核世界。

这一机制也能帮助学生区分“生成正确答案”和“形成可提交状态”。Agent 可能生成了一段看起来合理的修改，但如果它没有说明基于哪个版本、解决哪个目标、引用哪些证据、满足哪些权限，就还只是候选物。相反，一个候选即使最终被拒绝，也仍然有教学价值：它记录了被尝试的路径、失败原因和后续不应重复的假设。Candidate Commit 因而不仅是安全机制，也是学习长任务历史的结构。它让系统能够在多次尝试之间积累可信进展，而不是把每次失败都变成散落在上下文里的自然语言片段。

### 本章小结

ROB Commit 解决“乱序执行如何呈现顺序机器”的问题；Candidate Commit 解决“自治 Agent 如何呈现可审核世界”的问题。二者共享同一原则：推测可以在内部展开，正式状态必须通过精确提交边界。Agent CPU 通过 candidate entry、candidate-only side effect、ledger delta、Super Domain 审核和 recovery anchor，把安全、恢复和审计从事后约定变成体系结构协议。

### 本章习题

1. 为什么 Agent Domain 可以并行生成多个 candidate，却不能并行直接提交外部副作用？
2. 对比 ROB 的精确异常和 Agent CPU 的精确任务异常，说明二者分别需要保存哪些状态。
3. 设计一个 candidate entry 字段表，至少包含权限、证据、账本增量、补丁和恢复信息。
4. 假设某 Agent 先修改真实文件再补写 ledger，会破坏哪些 Candidate Commit 不变量？
5. 为什么 recovery anchor 不等同于完整上下文窗口快照？

## 第 12 章 从 Branch Prediction 到 Task-State Recovery

传统 CPU 的分支预测处理的是控制流不确定性。当前端还不知道下一条真实指令在哪里时，预测器先给出方向和目标，前端沿预测路径继续取指，后端执行到分支指令后再验证预测是否正确。若预测正确，流水线连续前进；若预测错误，处理器清空错误路径上的未提交工作，从正确地址重新开始。这个机制的重点不只是“猜得准”，还包括预测路径有边界、预测元数据可追踪、错误路径可恢复。

Agent CPU 同样面对不确定性，只是对象从指令地址变成任务路径。一个 Agent 在修复失败、整理上下文或生成方案时，可能先假设问题来自接口变化，也可能来自配置、依赖、输入格式或用户目标变化。不同假设会引出不同文件读取、工具调用、候选修改和验证顺序。Task Predictor 的作用，就是在这些路径中选择下一步最有希望的方向；Task-State Recovery 的作用，是在方向错误时保留可信状态、丢弃候选状态，并从正确任务点继续。

传统前端结构给出一个有用类比。分支预测器选择方向与目标；取指队列记录已经按什么路径取过指；ROB 保存尚未提交的执行结果；redirect 让机器回到正确地址；commit 让体系结构状态正式可见。Agent CPU 中可以对应为 Task Predictor、Task Flow Queue、Candidate Ledger Buffer、task redirect 和 ledger commit。Task Flow Queue 不必保存所有 token 或完整自然语言过程，而应记录任务级预测轨迹：当前目标、候选假设、计划阶段、工具调用意图、依赖证据、预算状态和恢复锚点。

这个类比也有边界。传统分支预测错误主要损失周期；Agent 任务预测错误可能引起错误证据引用、无效文件修改、重复工具调用、预算浪费，甚至把压缩后的摘要带偏。因此，Agent CPU 的预测不能只追求命中率，还要追求可恢复性。一个预测路径如果容易验证、容易丢弃、容易解释，可能比一个看似命中率更高但副作用难以隔离的路径更适合作为下一步。

为了支持恢复，任务状态可以分为 speculative task state 和 committed task state。前者包括未验证假设、候选修改、临时 trace、待审核账本增量和未确认工具结果；后者包括已验证证据、已接受决策、已提交 ledger、用户约束和 recovery anchor。当预测失败时，系统不应撤销整个会话，也不应只依赖自然语言摘要重新猜测，而应撤销最近提交点之后的候选状态，保留 committed task state，并选择新的任务路径。

一个典型恢复过程如下：Task Predictor 选择“失败来自接口兼容性”这一候选路径；Agent 执行工具调用并生成候选修改；Verifier 发现测试和证据不支持该假设；运行时标记 Task Flow Queue 中相应路径为 mispredicted；Candidate Ledger Buffer 丢弃未提交 delta；系统从最近 recovery anchor 恢复，重新选择路径。这个过程类似精确异常：错误之前已经提交的状态继续可信，错误之后的候选状态被清理，恢复点说明下一步应从哪里继续。

Trace 在这里不是事后日志，而是恢复材料。它应回答：哪个目标触发了行动，读取了哪些产物，调用了哪些工具，输出证据是否被引用，决策为何被接受或拒绝，哪些修改仍是候选状态。为了控制 trace 规模，可以分层保存：热路径保留 task id、anchor id、证据摘要、工具结果摘要、脏产物列表和预算状态；冷路径保留完整输出、长 transcript 和原始 artifact。这样既能恢复关键状态，又不会让 trace 变成不可承受的负担。

Compact 后恢复是 Agent CPU 必须教材化讲清的场景。compact 的危险在于，它会把结构化状态压成自然语言文字；如果摘要遗漏“某方案已经失败”“某文件修改尚未提交”“某用户约束不可违反”，恢复后的 Agent 就可能重复错误路径。正确做法是让 compact 依赖 recovery anchor，而不是依赖模型记忆。一次 compact transaction 应从 ledger 和 trace 中抽取约束、证据、未完成步骤、拒绝路径和最近 anchor，再投影成新的上下文。恢复的对象不是一段聊天记录，而是可继续执行的任务状态。

Task-State Recovery 的目标不是让 Agent 永远不走错路，而是让它走错路后知道错在哪里、丢弃什么、保留什么、如何继续。预测仍然重要，但预测服从提交、审计和恢复；速度仍然重要，但速度不能以污染状态为代价。这样，Agent CPU 才能支持长任务、跨 compact 边界任务和多候选并行任务。

在课堂讲解中，可以把任务预测分成“选择问题”和“恢复问题”。选择问题关心下一步先看哪里、先验证哪条假设、先调用哪个工具；恢复问题关心这一步如果错了，哪些状态仍然可信，哪些结果必须失效。传统分支预测器的训练目标主要来自历史分支行为，Agent Task Predictor 的训练信号则更丰富：路径是否产生有效证据，候选是否通过审核，恢复是否需要大量重做，是否触发权限 trap，是否重复了已拒绝方案。也就是说，Agent CPU 的预测质量应由任务闭环来评价，而不只由局部命中率评价。

### 本章小结

Branch Prediction 启发 Agent CPU 处理任务路径不确定性。Task Predictor 选择下一步方向，Task Flow Queue 保存预测轨迹，Candidate Ledger Buffer 保存候选状态，recovery anchor 支持错误路径清理和任务恢复。Agent 任务预测的评价标准不仅包括命中率，还包括副作用隔离、证据可追溯、恢复成本和 compact 后连续性。

### 本章习题

1. 传统 CPU 中预测器、取指轨迹和 ROB 的分工是什么？它们分别给 Task Predictor、Task Flow Queue 和 Candidate Ledger Buffer 带来什么启发？
2. 为什么 Agent 任务预测错误的代价不能只用“浪费时间”衡量？
3. 设计一个 recovery anchor 的最小字段集合，要求支持 compact 后恢复。
4. 如果 compact 摘要遗漏了“某方案已被验证失败”，系统应如何利用 trace 或 ledger 阻止重复尝试？
5. 说明一个预测路径为什么可能因“容易恢复”而优于另一个“看似更快”的路径。

## 第 13 章 从 SPEC 到 Agentic Benchmark

体系结构需要 benchmark，因为 benchmark 是架构设计共同讨论的语言。一个新结构是否有意义，不能只靠概念图说明，而要回答：它面对什么 workload，baseline 是什么，测量哪些指标，性能、成本、正确性和风险之间如何取舍。传统 benchmark 的价值在于把讨论从“我觉得更快”转化为“在可复现输入、可比较规则和明确指标下表现如何”。

SPEC 代表了这种定量精神。它用一组相对稳定、可复现、可比较的程序，使处理器设计者必须面对真实控制流、真实编译器、真实内存层次和真实执行时间。Agent CPU 也需要类似纪律，但测量对象会发生变化。Agentic workload 往往跨越多轮上下文、工具调用、文件修改、权限检查、候选提交和 compact 边界；模型调用只是其中一部分，模型外的状态处理同样可能成为瓶颈。因此，Agentic Benchmark 要继承可复现、可比较和端到端报告的原则，同时把任务状态流纳入测量。

传统 benchmark 常以固定程序和固定输入为中心，正确性通过输出判等；Agentic Benchmark 则可以以固定任务事件流、固定工具结果、固定 ledger 和固定 artifact 为中心。它的正确输出也不只是最终文字，而包括可验证结论、证据引用、状态 delta、提交记录和恢复行为。执行时间也应拆分：准入延迟、工具事件扫描、账本增量抽取、上下文投影、Super Domain 审核、恢复延迟和模型等待时间。这样才能看出 Agent CPU 究竟优化了哪里。

微基准用于隔离机制。第一类是 capability_check，测量区域查找、权限判断、trap 定位和误报漏报。第二类是 ledger_delta_extract，测量从事件流中抽取目标、计划、证据、决策和结果的吞吐。第三类是 context_budget_pack，测量在固定 token、引用或字节预算下保留关键约束和证据的能力。第四类是 artifact_preview_scan，测量大量产物摘要、哈希、修改时间和引用关系的扫描效率。第五类是 recovery_anchor_select，测量 compact 或中断后恢复点的选择质量。第六类是 candidate_patch_score，测量候选修改的风险分类、证据覆盖和可解释性。微基准的作用类似缓存缺失延迟或分支错误代价：它们不代表完整应用，却能帮助定位瓶颈。

宏基准用于回答系统是否真正服务长任务。一个合格的 Agentic 宏基准应包含目标变化、工具失败、部分候选修改、权限拒绝、compact 边界和恢复场景。输入可以包括 transcript window、artifact preview、已提交 ledger、trace window、候选状态和若干固定工具结果；输出可以包括 ledger delta、context projection、recovery anchor、candidate side effect 和最终结论。评价时不仅看最终结果是否正确，还要看是否重复尝试已拒绝方案，是否误删已完成步骤，是否保留关键用户约束，是否能解释每个提交的证据引用。

Agentic Benchmark 的指标可以分为正确性、安全性和恢复性。正确性指标包括 output match、evidence coverage、constraint retention 和 delta validity，分别关注结果是否匹配、证据是否覆盖、约束是否保留、状态增量是否有效。安全性指标包括 capability violation recall、trap precision、bad commit rate 和 side-effect isolation，关注越权是否被捕获、trap 是否定位清晰、错误副作用是否进入提交状态。恢复性指标包括 recovery success、anchor minimality、redo rejected path rate 和 compact continuity，关注中断后能否回到正确阶段、恢复集合是否足够小、是否重复旧错误、compact 后任务是否连续。

这些指标共同表达一个重要原则：更快不一定更好。如果一个系统把 context_budget_pack 加速很多，却丢失关键用户约束；如果它降低平均延迟，却让权限 trap 变得不可解释；如果它减少 trace 开销，却让 compact 后恢复失败，那么它不能被判定为更优的 Agent CPU。Agentic Benchmark 应当鼓励设计者同时报告速度、证据质量、安全边界和恢复质量。

为了避免 benchmark 退化成单一排行榜，报告还应呈现失败样例。失败样例不是附属材料，而是理解体系结构边界的重要证据。例如，一次权限拒绝是否给出了准确 task id 和 region，一次恢复失败是否来自 anchor 过粗，一次约束丢失是否发生在 context pack 阶段。学生通过这些样例能够看到指标背后的机制，而不是只比较一个总分。Agentic Benchmark 的教育意义正在于此：它把 Agent CPU 的性能、正确性和可恢复性放到同一张图景中，让架构取舍变得可以讨论、可以复现、可以改进。

最小报告格式也需要标准化。每个 benchmark 报告应说明任务描述、输入规模、事件分布、baseline、Agent Domain 路径、正确性判定、权限模型、恢复场景、运行环境和失败样例。报告应同时列出平均延迟和 tail latency，因为长任务中一次极慢恢复可能破坏整体交互体验。还应区分模型等待时间与模型外状态处理时间；即使模型等待占比较高，优化 ledger_delta_extract、context projection 和 recovery_anchor_select 仍然有价值，因为它们提升的是状态确定性、恢复速度和错误隔离能力。

教材中可以用一个简化公式帮助学生理解端到端分解：

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

这个公式不要求每项都由硬件直接加速，而是提醒我们：Agent CPU 的贡献不只在算得更快，还在状态更清楚、提交更可靠、恢复更确定。Benchmark 的最终目标，是让这些收益变成可测量、可复现、可比较的事实。

### 本章小结

Agentic Benchmark 继承传统 benchmark 的定量精神，但把测量对象从固定程序扩展到任务事件流、账本、产物、候选提交和恢复过程。微基准隔离 capability、ledger、context、preview 和 recovery 等机制；宏基准检验长任务、compact、权限拒绝和候选副作用。评价 Agent CPU 时，正确性、安全性和恢复性应与性能同等重要。

### 本章习题

1. 为什么可复现 workload 套件对 Agent CPU 仍然重要？
2. 设计一个包含 1000 条工具事件、3 次 compact 和 1 次权限拒绝的宏基准，说明输入、输出和指标。
3. 如果某实现把 context_budget_pack 加速 5 倍，但 constraint retention 明显下降，应如何评价？
4. 用端到端时间分解说明：当模型等待时间占比较高时，优化账本增量抽取和恢复锚点选择仍有什么价值？
5. 设计一份最小 benchmark 报告目录，要求同时覆盖性能、证据、安全和恢复。
