# 从 ROB Commit 到 Candidate Commit

## 1. 为什么从提交机制开始

在乱序 CPU 中，指令可以乱序执行，却必须表现得像顺序执行。这一矛盾由 ROB（Reorder Buffer）承担：前端按程序顺序分配 ROB 项，后端允许指令乱序发射、执行和写回，但最终只有当最老指令完成且没有异常时，机器状态才按顺序提交。体系结构状态因此保持清晰：寄存器和内存看见的是一条严格顺序的历史，而不是执行单元内部的混乱过程。

Agent CPU 面临相似但更宽的问题。Agent 可以并行搜索、调用工具、生成代码、试运行补丁、构造 ledger delta，也可以在不同候选路径之间切换。但用户真正关心的不是“中间想过什么”，而是哪些状态被正式写入：ledger 是否更新，文件是否改变，patch 是否进入工作区，外部工具是否产生真实副作用。因此，Agent CPU 也需要一个提交边界。这个边界不是传统 ROB 的 register commit，而是 Candidate Commit。

## 2. ROB 提交的三条经验

传统 ROB 给 Agent CPU 至少留下三条经验。

第一，执行与提交必须分离。乱序执行提升吞吐，但不等于乱序暴露结果。类似地，Agent Domain 可以高速生成候选物，但不能直接改变真实世界。候选 patch、candidate ledger delta、artifact preview 和工具输出都应先进入候选区。

第二，提交必须有全局顺序。CPU 用 ROB head 决定哪条指令先提交，避免 younger instruction 越过 older instruction 破坏精确状态。Agent CPU 中，一个任务的多个候选更新也要有顺序：先确认 goal、约束和 evidence，再提交 ledger delta；先审核 patch 的 base 和权限，再落盘；先记录 recovery anchor，再允许外部副作用。

第三，异常必须精确。所谓精确异常，是异常发生时，异常之前的指令都已提交，异常之后的指令都没有提交。Agent CPU 的对应目标是精确任务异常：一旦权限、证据、测试或用户约束检查失败，系统应能说明哪些 ledger 已提交，哪些只是候选，哪些 patch 尚未生效，并能回退到 last safe point。

## 3. 从 ROB 项到 Candidate 项

ROB 项记录目的寄存器、完成位、异常位和结果位置。Candidate Commit 也需要显式记录，但对象变成任务状态和副作用意图。

| 乱序 CPU 机制 | Agent CPU 对应机制 | 关键语义 |
| --- | --- | --- |
| ROB entry | candidate entry | 保存一次候选更新的身份、依赖、结果和审核状态 |
| ready bit | evidence ready | 表示候选结果、测试证据、权限说明已经收齐 |
| exception bit | trap / reject reason | 标记权限失败、证据不足、patch 冲突或预算超限 |
| commit head | candidate commit pointer | 只从可提交边界向前推进 |
| architectural state | committed ledger / workspace | 只有提交后才成为对外可见状态 |
| flush | discard candidates | 丢弃未提交候选，并从 recovery anchor 重启 |

一个 candidate entry 至少应包含：base ledger id、task id、capability set、candidate ledger delta、candidate-only side effect buffer、patch diff、evidence list、risk score、recovery anchor 和 reject reason。它不是简单日志，而是 Super Domain 可以审核的结构化提交单元。

## 4. Candidate-Only Side Effect

Agent CPU 的重要原则是：Agent Domain 只能产生 candidate-only side effect。也就是说，它可以“描述想要发生的副作用”，但不能直接让副作用发生。

例如，Agent 生成补丁时，不应直接改写源文件，而是写入 candidate patch buffer。它运行测试时，可以生成测试命令、stdout 摘要、失败定位和资源消耗记录，但真实文件写入、网络访问、发布包、提交 Git 分支等动作必须由 Super Domain 审核后执行。这样做不是为了降低 Agent 的能力，而是为了让能力有可恢复、可解释、可度量的边界。

candidate-only side effect 的核心价值在于把“意图”和“生效”拆开。意图阶段允许推测、并行和失败；生效阶段要求权限、顺序和证据。传统 CPU 把 store buffer 中的写操作延迟到安全时刻对内存可见，Agent CPU 则把外部副作用延迟到 Super Domain 确认 candidate 可以提交。

## 5. Super Domain 审核与顺序提交

Candidate Commit 的提交者不是 Agent Domain，而是 Super Domain。它类似 ROB 的 commit logic，但审核对象更丰富。

一个典型提交流程如下：

1. Agent Domain 产生 candidate entry，包括 ledger delta、patch diff、evidence 和 recovery anchor。
2. Super Domain 检查 capability：候选是否试图越权读写、越过 candidate-only 边界或访问未授权资源。
3. Super Domain 检查 base：candidate 的 base ledger 与当前 committed ledger 是否一致，patch 是否基于当前工作区。
4. Super Domain 检查 evidence：测试、静态分析、用户约束、风险评分是否满足提交策略。
5. 若通过审核，按顺序提交 ledger delta，再提交 patch 或受监管副作用；若失败，记录 reject reason 并保留可诊断 trace。

这里的“顺序”不一定等于单线程。多个候选可以并行生成，甚至可以在不同 Agent cluster 中竞争。但进入 committed ledger 时必须形成可解释序列。否则，系统会出现类似乱序提交的错误：后一个 patch 依赖前一个未提交假设，某条 ledger delta 记录了并不存在的证据，或者 recovery anchor 指向一个无法重建的中间状态。

## 6. Ledger Delta 与 Patch 提交

ledger delta 是 Agent CPU 的体系结构状态更新。它记录任务进展、关键证据、约束变化、工具结果和决策理由。patch 提交则是外部工作区状态更新。两者关系密切，但不能混为一谈。

正确顺序通常是：先把“为什么可以提交”的证据写成候选 ledger delta，再由 Super Domain 审核；审核通过后，ledger 记录提交决策，patch 才进入真实工作区。这样，即使 patch 后续引发问题，系统仍知道它为何被允许提交、基于哪个 base、通过了哪些检查。

如果先改文件再补 ledger，就会形成不可解释状态：文件已经变化，但系统无法证明变化来自哪个任务、满足哪个 capability、对应哪个 recovery anchor。这等价于 CPU 绕过 ROB 直接写体系结构寄存器，短期看似更快，长期会破坏调试、恢复和安全。

## 7. Recovery：从 Flush 到任务回滚

乱序 CPU 遇到分支预测失败或异常时，会 flush younger instructions，并从正确 PC 重新取指。Agent CPU 的 recovery 更像任务级 flush：丢弃未提交 candidates，保留 committed ledger，恢复到最近的 recovery anchor，然后重新规划。

recovery anchor 至少要能回答三个问题：从哪个 base ledger 恢复，哪些候选副作用尚未提交，哪些上下文投影可以重新生成。它不要求保存全部上下文窗口，因为上下文只是 ledger、artifact 和 trace 的投影；它要求保存足够重建任务一致性的锚点。

一个良好的 Candidate Commit 设计应满足以下不变量：

- 未通过 Super Domain 审核的副作用不得对外可见。
- committed ledger 中的每条 delta 都能追溯到 candidate entry。
- patch 生效前必须有 base、权限、证据和 recovery anchor。
- recovery 后不得把 rejected candidate 当作已提交事实。
- 用户约束变化应使相关候选失效，类似分支预测失败后的 flush。

## 8. 小结

ROB Commit 解决的是“乱序执行如何呈现顺序机器”的问题；Candidate Commit 解决的是“自治 Agent 如何呈现可审核世界”的问题。二者共享同一条体系结构原则：内部可以推测，外部必须精确。Agent CPU 不应把安全、恢复和审计完全交给软件约定，而应把 candidate entry、candidate-only side effect、ledger delta、Super Domain 审核和 recovery anchor 变成硬件可见或运行时强约束的提交协议。

## 本章习题

1. 解释为什么 Agent Domain 可以并行生成多个 candidate，但不能并行直接提交外部副作用。
2. 对比 ROB 的精确异常和 Agent CPU 的精确任务异常。二者分别要求保存哪些状态？
3. 设计一个 candidate entry 字段表，至少包含权限、证据、ledger delta、patch 和 recovery 信息。
4. 假设某 Agent 先修改文件再写 ledger，会破坏哪些 Candidate Commit 不变量？
5. 为什么 recovery anchor 不等同于完整上下文窗口快照？请结合 ledger projection 说明。
