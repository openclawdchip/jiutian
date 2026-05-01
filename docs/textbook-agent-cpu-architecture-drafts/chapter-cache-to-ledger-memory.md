# 从 Cache 到 Ledger-Aware Memory

## 1. 为什么传统 Cache 不够

传统计算机体系结构把内存层次建立在一个基本假设上：程序的访存局部性可以由硬件在运行时捕捉。寄存器、L1/L2 Cache、LLC、DRAM/HBM、外存构成了从近到远的容量与延迟梯度。Cache 通过 tag、替换、预取和一致性协议，尽量让程序觉得自己面对的是一片连续而快速的内存。

这个模型对长期运行的人类软件很有效，因为循环、数组、栈帧、对象布局具有稳定模式。但 Agentic workload 的热路径不完全相同。Agent 任务常常在短生命周期内完成一次读取、归纳、生成、验证和提交；它访问的对象不是单纯的字节数组，而是 goal、context section、artifact preview、trace event、candidate ledger delta 和 recovery anchor。硬件如果仍只在 cache line 层面猜测局部性，就会错过更重要的语义：哪些状态只是临时上下文，哪些状态必须被审计，哪些状态可以丢弃，哪些状态必须进入 ledger。

因此，Agent CPU 的内存系统不应只问“这个地址最近是否被访问”，还应问“这段数据在任务语义中扮演什么角色”。

## 2. 从容量层次到语义层次

Agent CPU 仍然需要传统内存层次。控制面代码、运行时队列、普通数据结构仍可受益于 Cache；大模型外部状态也仍需要 HBM 或主存提供容量。但在 Agent 执行面，内存层次要叠加一层语义分类。

| 层级 | 传统用途 | Agent CPU 中的语义 |
|---|---|---|
| Register / local state | 指令近端操作数 | 当前 task 的短暂控制状态 |
| L1/L2 Cache | 自动缓存热点数据 | 服务控制面与少量不可显式管理热路径 |
| SPM | 软件管理片上存储 | 当前 context 分片、临时表、局部工作集 |
| Cluster SRAM | cluster 内共享缓存 | 多 Agent 阶段共享、producer/consumer 中间态 |
| HBM / Host Memory | 大容量数据 | transcript、artifact、ledger、trace 的容量层 |
| Context Window | 无传统对应物 | 模型可见投影，不是真实记忆 |
| Ledger Region | 无传统对应物 | 已提交事实、证据引用和可恢复状态 |

这里最关键的转变是：context window 不是“更大的 Cache”，而是一次推理前对真实记忆的投影。它可以被重排、压缩、摘要、裁剪；只要投影过程可追溯，context 本身不必承担全部持久性责任。真正的系统状态应保存在 ledger、artifact、trace 和恢复锚点中。

## 3. SPM、Cluster SRAM 与显式 DMA

传统 Cache 的优点是透明，缺点也是透明。它让程序员和编译器不必说明数据移动，却也让运行时难以判断带宽究竟被谁消耗。Agent CPU 更适合采用显式本地内存：每个 Agent 核拥有 SPM，cluster 内共享 Cluster SRAM，远端容量层由 HBM 或 host memory 提供。

典型流程如下：

1. Super Domain 授权任务可读取的 ledger 区段、artifact 预览区和输出区域。
2. Agent Domain 用 DMA 把 ledger header、相关 trace 摘要和 artifact preview 搬入 Cluster SRAM。
3. 每个 Agent 核把自己需要的 context section 或候选表搬入 SPM。
4. 任务在 SPM 中完成筛选、打包、验证或 delta 生成。
5. 候选结果写回 Cluster SRAM，经 barrier 汇合后，由控制面提交或拒绝。

显式 DMA 的价值不只是性能。它让数据移动成为可审计事件：搬了多少字节，从哪个命名空间到哪个命名空间，为哪个 task 服务，是否越过 capability 边界。这些信息可以进入 trace，进而成为 benchmark、调试和安全策略的一部分。

## 4. Ledger-Aware Memory 的基本概念

Ledger-aware memory 指内存系统知道某些区域具有账本语义。账本语义至少包含四点。

第一，写入不能等同于提交。Agent 可以生成 candidate ledger delta，但不能直接改写已提交 ledger。提交必须经过权限、证据、预算和一致性检查。

第二，读取必须保留 provenance。一个 context projection 如果引用了某段事实，就应能追溯到 ledger entry、artifact preview 或 trace summary，而不是只留下模型输入中的一段自然语言。

第三，替换策略应考虑语义热度。传统 LRU 关心最近访问；ledger-aware memory 还应关心任务图依赖、恢复锚点距离、证据复用频率和审计优先级。

第四，可见性应显式化。flush、invalidate、fence 不只是缓存一致性操作，也可以表达“某个候选状态已经对下一阶段可见”或“某个 projection 已失效，需要重新从 ledger 打包”。

## 5. Artifact Preview 与 Trace

Agent 经常不需要完整 artifact，而只需要预览：文件摘要、表格 schema、图像描述、测试失败片段、代码 diff 的关键 hunks。Artifact preview 类似传统体系结构中的 cache line，但它的切分单位由语义决定，而不是固定字节宽度。一个好的 preview 应当小到能放入 context window，大到足以支持推理判断，并且能回指原始 artifact。

Trace 则是内存系统的时间维度。传统内存层次主要保存“现在有什么”；Agent CPU 还要保存“状态如何变成现在这样”。DMA copy、barrier arrive、ledger delta extract、context_budget_pack、trap、recovery anchor select 都应成为结构化 trace event。这样，当任务失败或输出可疑时，系统可以从 trace 重建路径，而不是只检查最终内存快照。

## 6. 设计原则

Ledger-aware memory 不取消 Cache，而是重新分工。Cache 继续服务普通控制流；SPM 和 Cluster SRAM 服务可预测、可声明、可搬运的 Agent 工作集；HBM 保存大容量事实与产物；context window 只保存本轮推理投影；ledger 保存可审计状态。

这带来一个体系结构判断：Agent CPU 的性能不应只用 cache hit rate 衡量，还要衡量 projection latency、DMA effective bytes、ledger delta throughput、trace overhead、artifact preview reuse rate。也就是说，内存系统的目标从“隐藏延迟”扩展为“让状态移动、状态可见和状态提交都可度量”。

### 本章习题

1. 为什么说 context window 不是 Agent CPU 的真实内存？请结合 ledger 和 artifact preview 说明。
2. 比较传统 Cache line 与 artifact preview：二者的切分依据、替换策略和正确性责任有什么不同？
3. 设计一个 `ledger_delta_extract` 任务的数据移动流程，要求显式使用 SPM、Cluster SRAM、HBM 和 DMA。
4. 如果一个系统只记录最终 ledger，不记录 trace，会给调试、审计和恢复带来哪些问题？
5. 选择三个指标，用来评价 ledger-aware memory 是否优于只依赖传统 Cache 的实现。
