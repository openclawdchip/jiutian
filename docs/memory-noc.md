# Memory 与 NoC 模型

Honeycomb 架构使用显式本地内存与集群化传输，而不是假设所有核心共享一套完全硬件一致的内存结构。

本文档定义九天 v0.1 的存储层级、数据移动方式、一致性规则和 NoC 设计方向。地址空间细节见 `specs/memory-map-v0.1.md`，指令语义见 `specs/isa-v0.1.md`。

## 设计原则

Agent 原生执行面的内存系统遵循四条原则：

- **近场优先**：优先把数据放在执行它的 Agent 核或所在 cluster 附近。
- **显式搬运**：任务必须通过 DMA 或显式 store/load 表达跨空间数据移动。
- **软件可见一致性**：Agent 域默认不依赖全局硬件 snoop 来维护一致性。
- **监管可抢占**：控制消息、异常和 kill 信号必须能及时穿过 NoC。

这些原则服务于同一个目标：把带宽用于实际数据，而不是把大量片上流量消耗在全局监听和隐式状态维护上。

## 存储层级

九天的存储层级从近到远分为四层。

| 层级 | 位置 | 管理者 | v0.1 语义 | 主要用途 |
| :--- | :--- | :--- | :--- | :--- |
| SPM | 每个 Agent 核本地 | Agent 指令显式管理 | 命名空间 `spm` | 热数据、临时数据、短循环工作集 |
| Cluster SRAM | 每个 cluster 本地 | runtime 分配，Agent 显式访问 | 命名空间 `cluster` | 同 cluster 任务共享、阶段性结果 |
| Distributed SRAM | 多 cluster 分布 | runtime 和 NoC 协同 | v0.1 先以 cluster SRAM 抽象 | 跨 cluster 近端缓存、队列、mailbox |
| Host/HBM | 外部或全局内存 | 控制面授权 | 命名空间 `host` | 输入、输出、大容量数据集 |

v0.1 模拟器先实现 `spm`、`cluster` 和 `host` 三个命名空间。Distributed SRAM 和 HBM 以规格保留，不强制模拟真实延迟。

## SPM：每核显式本地内存

SPM 是 Clawd-Agent 的核心资源。它不是传统 cache，不做 tag 比较，也不由硬件替 Agent 猜测替换策略。Agent 指令通过显式地址访问 SPM，runtime 通过任务资源声明限制可用容量。

SPM 适合放置：

- 当前任务最热的输入窗口。
- 累加器、临时表、局部队列。
- 小型状态机和规则匹配表。
- DMA 即将消费或刚刚产生的数据块。

SPM 不适合放置：

- 生命周期跨越多个不相关任务的大型共享状态。
- 需要被很多 cluster 同时频繁读写的数据结构。
- 未经授权的 host 指针或控制面私有状态。

v0.1 默认 SPM 容量范围为 64KB-256KB。模拟器通过 `config.spm_bytes` 配置容量，并对越界访问触发 trap。

## Cluster SRAM：蜂窝内共享数据

Cluster SRAM 是同一 cluster 内多个 Agent 核共享的近端存储。完整产品设想中，每 8 个 Agent 核共享一个本地 SRAM/L3 slice。v0.1 模拟器用 `cluster` 命名空间表达这一层。

Cluster SRAM 适合：

- 同一任务图阶段中多个任务共享的输入分片。
- producer/consumer 之间的中间结果。
- 小型任务队列。
- barrier 前后需要交换的状态。

Cluster SRAM 的访问延迟应明显低于 host/HBM，但高于本核 SPM。规格层不要求 v0.1 模拟器周期精确，只要求功能语义稳定。

## Host/HBM：远端容量层

Host/HBM 是 Agent 域的大容量输入输出层。Agent 任务不能任意访问 host 空间，必须通过 capability 获得读写范围。

Agent 与 host 之间的访问优先通过 DMA 完成。这样可以让 runtime 观察和限制数据移动，也能让后续硬件把搬运与计算重叠。

host 空间适合：

- 外部输入数据。
- 最终输出结果。
- 大型只读表。
- 需要控制面持久化或审计的数据。

## 数据移动路径

九天 v0.1 的基本数据路径如下：

```text
host/HBM
   |        dma_copy
   v
cluster SRAM  <---->  SPM
   ^                    |
   |        dma_copy     | load/store
   +--------------------+
```

常见执行模式：

1. 控制面授权 host 输入和输出区域。
2. Agent 任务把输入分片 DMA 到 cluster SRAM 或 SPM。
3. Agent 核在 SPM 中执行热循环。
4. 需要共享的数据写入 cluster SRAM。
5. barrier 确认阶段完成。
6. 结果 DMA 回 host 输出区域。

## DMA 模型

DMA 是 Agent 域跨空间搬运数据的主路径。v0.1 的最小 DMA descriptor 包含：

- 源空间：`host`、`cluster` 或 `spm`。
- 源偏移。
- 目标空间：`host`、`cluster` 或 `spm`。
- 目标偏移。
- 字节数。
- 所属任务。

DMA 发起时必须检查：

- 源和目标空间是否合法。
- 地址范围未越界。
- host 读写 capability 满足方向要求。
- 长度不超过任务和系统配置上限。
- descriptor 格式合法。

`dma_wait` 用于等待当前任务已发起的 DMA 完成。v0.1 早期模拟器可以同步完成 DMA；后续模拟器应升级为固定延迟队列，以验证等待、释放和 deadlock 判断。

## 一致性

超大核域可以使用传统硬件一致性。Agent 域默认使用显式一致性操作：

- `flush` 发布已写入数据。
- `invalidate` 丢弃本地陈旧副本。
- `barrier` 在任务之间建立顺序。
- `fence` 为 DMA 与内存可见副作用建立顺序。

Agent 域不提供“任何核心写入后其他核心立即自动看见”的承诺。任务之间的数据交接必须通过显式同步和可见性操作建立。

### 可见性规则

v0.1 采用以下简化规则：

- 同一任务内，按程序顺序观察自己的 SPM 写入。
- 同一任务内，`cluster` load 能观察此前本任务对同一地址的 store。
- 不同任务之间，只有在 `barrier` 或 runtime 声明的依赖之后，才应依赖对方写入。
- DMA 结果只有在对应 `dma_wait` 完成后才可被任务消费。
- `flush` 和 `invalidate` 在模拟器中可作为 trace 事件；后续 RTL 应把它们映射为真实队列、buffer 或 cache 控制动作。

## NoC 流量类别

NoC 应支持分离的流量类别：

- 控制消息。
- DMA 传输。
- Agent 到 Agent 消息。
- 外部内存流量。
- 异常与 kill 信号。
- trace 汇聚流量。

控制流量必须能够抢占数据流量，从而保证运行时始终保有对生成代码的监管权。

## Honeycomb 拓扑方向

完整九天设计采用 cluster 化蜂窝布局。v0.1 不要求固定物理拓扑，但文档和 specs 应保持对以下结构友好：

- 16 个 cluster，每个 cluster 8 个 Agent 核。
- cluster 内低延迟互连。
- cluster 间 mesh 或 torus 路由。
- 控制面到每个 cluster 的监管通道。
- DMA 与 trace 独立虚通道。

逻辑拓扑如下：

```text
             Super Domain
                  |
        control / monitor network
                  |
  +---------+---------+---------+---------+
  | C0      | C1      | C2      | C3      |
  | 8 cores | 8 cores | 8 cores | 8 cores |
  +---------+---------+---------+---------+
  | C4      | C5      | ...     | C15     |
  +---------+---------+---------+---------+
                  |
             host / HBM
```

## 拥塞与优先级

NoC 至少需要区分以下优先级：

1. kill、trap、fault、watchdog 等监管消息。
2. barrier release、runtime control 等同步控制消息。
3. DMA descriptor 和短控制包。
4. DMA data payload。
5. bulk trace 或低优先级统计流量。

这样即使 Agent 域产生大量数据流，控制面仍能终止异常任务或回收资源。

## 与模拟器的关系

当前模拟器首先保证功能语义：

- SPM/cluster/host 三类空间。
- 边界检查。
- capability 检查。
- `dma_copy` 与 `dma_wait`。
- barrier。
- trace。

当功能语义稳定后，再加入：

- DMA 固定延迟。
- DMA 队列深度。
- NoC 拥塞 proxy。
- cluster 间访问延迟差异。
- 简单能耗统计。

模拟器不需要一开始周期精确，但必须让每一次显式数据移动都能在 trace 中被解释。

## Claude Code 类 memory 体系对九天的启发

Claude Code 类 Agent runtime 的 memory 体系不是单一“记忆文件”，而是一套上下文投影系统。已有分析和源码阅读表明，它至少包含六层：

| 层 | 软件对象 | 行为 | 九天映射 |
| :--- | :--- | :--- | :--- |
| 长期 memory 索引 | `MEMORY.md` | 常驻加载，作为记忆目录的短索引；有行数和字节上限 | Super Domain 管理，Agent Domain 可加速索引扫描和去重 |
| typed memory shard | 独立 memory 文件 | 每个主题独立文件，带 frontmatter、description、type、mtime | Host/HBM 保存，Cluster SRAM 缓存 headers |
| 相关记忆召回 | memory manifest + selector | 扫描最多一批 memory header，由模型或选择器挑出少量相关项 | Agent Domain 执行 header scan、排序、预算筛选，Super Domain 做最终召回 |
| session memory | 会话内自动摘要文件 | 达到 token 和工具调用阈值后后台抽取，记录当前会话关键事实 | Super Domain 持久化，Agent Domain 加速 delta 提取和重复检测 |
| transcript | append-only JSONL | 原始历史不断链，维护 parent/logicalParent，供恢复和审计 | Host/HBM 或持久存储；Agent Domain 只处理投影和索引 |
| artifact/tool result | 大工具结果外置 | 大输出保存到文件，消息中只放 preview 和 pointer | Host/HBM 保存全文，SPM/Cluster SRAM 处理 preview、hash、引用 |
| compact boundary | compact/microcompact | 模型可见上下文被压缩，原始 transcript 保留 | Agent Domain 加速候选裁剪，Super Domain 写入 boundary |

这套设计的关键不是“记住更多”，而是把原始历史、模型可见上下文、可恢复日志和长期记忆拆开。模型看到的是投影视图，不是原始历史；大结果通过 artifact pointer 间接进入上下文；memory 先通过短 header 和索引筛选，再按需召回正文。

### Memory 体系的不变量

九天应吸收以下不变量：

- **原始历史 append-only**：transcript 不能因为 compact 被破坏。compact 只是增加 boundary 和 summary。
- **模型可见视图可重建**：当前上下文由 transcript、memory、artifact、tool result 和 boundary 重新投影出来。
- **大内容外置**：工具输出、长文件、搜索结果和日志不应直接占满上下文，应变成 pointer、preview、hash 和 size。
- **索引优先于正文**：常驻的是短索引和 frontmatter，正文按相关性召回。
- **召回受预算约束**：memory 召回、post-compact 文件恢复、skill 恢复都应有明确 token/字节预算。
- **后台抽取不能阻塞主循环**：session memory 由后台 worker 提取，主循环最多等待有限时间。
- **递归保护**：compact 和 session memory 自己不能触发新的 autocompact 循环。

### 九天 Memory Plane 分层

对应到九天硬件，memory 体系应分成四个物理层级：

```text
SPM
  热规则、短索引窗口、当前 descriptor、局部 hash/filter

Cluster SRAM
  memory header manifest、tool result preview、compact 候选、worker delta

Host/HBM
  transcript、artifact/tool result 全文、memory shard 正文、session memory 文件

Persistent storage
  append-only JSONL、长期 memory、恢复日志、用户可审计材料
```

Agent Domain 不应直接拥有“长期记忆”。它只获得控制面授权的一段投影输入和输出窗口，用来高吞吐处理：

- frontmatter 扫描。
- memory header 排序。
- artifact preview 截断。
- tool result hash 与去重。
- compact 候选分组。
- transcript parent 链检查。
- session memory delta 提取。
- 引用关系和恢复入口整理。

Super Domain 继续负责：

- 真实文件读写。
- memory 正文召回。
- transcript 持久化。
- compact summary 的最终提交。
- 隐私、权限和用户确认。

### 典型数据流

一轮长会话中的 memory 数据流：

```text
1. Super Domain 追加原始消息到 transcript。
2. 工具产生大结果；全文写入 artifact/tool-results，消息中保留 pointer 与 preview。
3. Agent Domain 扫描 tool result preview、memory headers、recent transcript window。
4. Agent Domain 输出：相关 memory 候选、去重结果、compact 候选、风险标记。
5. Super Domain 选择是否召回正文、是否写 session memory、是否触发 compact。
6. compact 发生时，Super Domain 写入 boundary；Agent Domain 可协助生成保留引用和裁剪列表。
7. 下一轮上下文由 transcript + boundary + memory refs + artifact refs 重新投影。
```

这一流程说明：九天要加速的不是模型权重本身，而是 Agent runtime 在上下文和记忆边界上的大量结构化搬运、筛选、压缩、索引和恢复准备。

### 对 APU-IR 的要求

为了承载这类 memory workload，APU-IR 需要能表达：

- `MemoryHeaderScan`：输入一批 header，输出按相关性或新鲜度排序的候选。
- `ArtifactPreview`：从大结果 metadata 和 preview 中生成摘要候选。
- `TranscriptWindow`：读取最近窗口，检查 parent 链和 compact boundary。
- `ContextBudgetPack`：在 token/字节预算内选择保留项。
- `SessionMemoryDelta`：比较上次摘要位置之后的新增消息和工具调用。
- `ReferenceDedup`：对 memory refs、artifact refs、file refs 去重和分组。

v0.1 不必马上实现这些高级 op，但 ISA 和模拟器中的 SPM、DMA、barrier、trace 应为它们保留表达空间。

## 面向长期任务的九天记忆闭环

Claude Code 这类 Agent 的短板不是不会写 memory，而是长任务运行到上下文窗口上限后，模型可见工作集被压缩，原始任务目标、已经验证过的事实、失败路径、用户约束和下一步计划容易被混成一段不可执行摘要。摘要一旦丢失结构，Agent 下一轮就只能“重新理解任务”，于是出现长任务越做越慢、重复探索、忘记已验证结论、甚至从头开始的问题。

九天的长期记忆设计不是单纯扩大上下文，而是把长任务拆成可恢复的硬件友好对象：

| 对象 | 含义 | 持久层 | 热路径加速 |
| :--- | :--- | :--- | :--- |
| `GoalLedger` | 用户目标、成功标准、禁止事项 | transcript / persistent memory | 目标字段校验、冲突检测 |
| `PlanLedger` | 当前计划、阶段、未完成项、依赖关系 | session memory / task log | 依赖图排序、完成度归约 |
| `EvidenceLedger` | 已读文件、测试结果、命令输出、引用 | artifact store / transcript | hash、去重、引用 packing |
| `DecisionLedger` | 为什么这么做、哪些方案被拒绝 | memory shard / compact boundary | reason code 分类、摘要候选 |
| `RecoveryLedger` | last safe point、回滚点、失败原因 | persistent recovery log | 恢复入口选择、状态 delta 检查 |
| `ContextProjection` | 下一轮模型真正看到的上下文 | volatile prompt view | 预算 packing、相关性排序 |

这些 ledger 不是另一个 UI 层概念，而是九天和 Agent runtime 之间的运行契约。Super Domain 负责把它们写入可审计持久层；Agent Domain 负责在每一轮前后高速整理、筛选、校验和打包。

### 为什么它能避免“重头来”

长任务之所以会重头来，是因为传统 Agent 把三类东西混在同一个上下文窗口里：

- **事实**：已经观察到什么。
- **决策**：为什么选择当前路线。
- **执行状态**：现在做到哪一步，下一步是什么。

窗口一满，compact 只保留自然语言摘要，事实、决策和执行状态之间的结构关系就会弱化。九天要求每轮结束都生成结构化 checkpoint：

```text
Turn N 结束
  -> append transcript
  -> persist artifact refs
  -> update GoalLedger / PlanLedger / EvidenceLedger
  -> generate RecoveryLedger(last_safe_trace_id, pending_steps, dirty_outputs)
  -> compact only the model-visible projection
  -> keep ledgers intact
```

下一轮开始时，不是从全文历史里猜当前状态，而是由 runtime 读取 ledger：

```text
Turn N+1 开始
  -> load GoalLedger
  -> load active PlanLedger window
  -> recall only relevant EvidenceLedger entries
  -> restore RecoveryLedger last safe point
  -> Agent Domain packs ContextProjection under token budget
  -> model receives "当前目标 + 当前阶段 + 已证据 + 下一步"
```

这样 compact 只压缩“给模型看的视图”，不压缩“任务真实状态”。模型忘了多少上下文并不致命，因为任务状态有结构化账本可重建。

### 九天与 Claude Code 类 Agent 的协同方式

Claude Code 类 Agent runtime 已经具备若干雏形：append-only transcript、大工具结果外置、memory index、session memory、compact boundary、sidechain worker。九天把这些软件机制硬件化为一个持续运行的记忆流水线：

1. **Agent runtime 产生事件**：用户输入、tool_use、tool_result、权限拒绝、测试结果、文件变更、compact。
2. **Super Domain 归档原始材料**：transcript、artifact、session memory、长期 memory、recovery log。
3. **Agent Domain 并行提取结构**：从事件中抽取 goal、plan step、evidence、decision、risk、pending work。
4. **Ledger 更新**：控制面检查权限和一致性后写入对应 ledger。
5. **ContextProjection 生成**：Agent Domain 在预算内选择下一轮最关键的 ledger refs 和 artifact previews。
6. **模型继续执行**：模型看到的不是“长历史压缩成一段话”，而是结构化恢复包。

这套机制使 Agent 的长期任务从“上下文驱动”变成“账本驱动”。上下文窗口只是投影缓存，ledger 才是任务真状态。

### 硬件职责分工

| 工作 | Super Domain | Agent Domain |
| :--- | :--- | :--- |
| transcript 追加 | 负责真实写入和恢复链 | 检查 parent/logicalParent 链 |
| artifact 外置 | 负责文件系统和权限 | 生成 preview、hash、引用去重 |
| plan 状态 | 负责提交和审计 | 归约完成度、检测依赖冲突 |
| evidence 选择 | 负责读取正文 | 排序、过滤、预算 packing |
| compact | 负责写 boundary | 生成保留/丢弃候选 |
| recovery | 负责回滚/重试策略 | 选择 last safe point 和 dirty state |

Agent Domain 永远不直接拥有最终记忆写权限。它给出结构化候选，Super Domain 决定是否提交。这保证长期记忆不会被一次错误生成污染。

### 对 NoC 和 Memory 的压力

长期记忆闭环会产生持续的小块不规则访问：

- 大量 metadata/header 扫描。
- 多个 artifact preview 的 hash 和去重。
- transcript tail window 的 parent 链检查。
- plan/evidence/recovery ledger 的小对象更新。
- compact 前后的引用重排。

这正是 SPM + Cluster SRAM + DMA 的适用场景。SPM 保存当前轮的规则表、hash 表和短窗口；Cluster SRAM 保存跨核共享的候选列表；Host/HBM 保存完整 ledger 和 artifact；NoC 负责高频小块搬运和 trace 汇聚。

传统 CPU 会在对象图、字符串、JSON、Map/Set、文件 metadata 上反复走 cache/TLB/GC/runtime 路径。九天的 Agent Domain 把这部分变成显式任务图，使长任务每轮结束都有低成本 checkpoint，每轮开始都有低成本恢复投影。

## 设计收敛标准

Memory 与 NoC 文档进入 v0.1 可实现状态的标准：

- 所有存储空间都能映射到 `specs/memory-map-v0.1.md`。
- 所有搬运动作都能映射到 `specs/isa-v0.1.md`。
- capability 规则与 `docs/security.md` 不冲突。
- 模拟器至少能发现越界、非法 host 访问和 barrier deadlock。
- trace 能说明数据何时从哪里移动到哪里。
