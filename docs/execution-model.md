# 执行模型

九天 v0.1 的执行模型围绕一个核心边界展开：Agent 执行面负责常驻守护、监听和运行有界的生成代码任务；控制面负责授权、监管、高熵任务爆发和真实副作用提交。这个边界在 Guardian-Execution 模式下表现为“Agent Core 常驻，Super Core 按需唤醒”。

本文档定义任务生命周期、状态机、调度原则、同步语义、异常语义和 trace 要求。任务字段的规范化定义见 `specs/task-model-v0.1.md`，指令语义见 `specs/isa-v0.1.md`。

## 基本单位

九天 v0.1 中有三个层次：

- **任务图**：上层 Agent 或 runtime 看到的工作流，由多个任务和依赖组成。
- **Agent 任务**：控制面准入和调度的最小单位。
- **Agent 指令**：Clawd-Agent 执行的最小语义单位。

任务图描述“哪些任务互相依赖”，Agent 任务描述“一个有界代码片段需要哪些资源”，Agent 指令描述“每一步如何读写、搬运、同步和结束”。

## 执行生命周期

一次完整执行分为 10 个阶段：

1. Clawd-Agent 以 Always-On guard 状态监听人类输入、API 请求、传感器事件、timer 或 runtime 队列。
2. Agent 域执行轻量意图分类，判断请求可在 Agent 域处理，还是需要高熵任务协处理。
3. 对简单、无副作用、有界任务，Agent 域直接生成或接收 APU-IR 任务图。
4. 对 LLM 推理、复杂 OS 路径、编译、重度感知或真实副作用任务，Agent 域写入 handoff mailbox 并发出 `WAKE_UP_SUPER`。
5. Clawd-Super 上电或解门控后，控制面运行时解析 APU-IR、验证资源声明、capability 请求、barrier 参与关系和预算。
6. 运行时为任务分配 SPM、Cluster SRAM、DMA channel、barrier 和 trace 资源。
7. APU-IR 被降低为 Agent 指令片段，或在 v0.1 中直接包含 JSON 指令。
8. Clawd-Agent 执行指令，并通过显式 DMA、barrier、flush、invalidate 管理数据；Clawd-Super 在后台承担授权、复杂计算或最终提交。
9. 任务进入 completed、trapped、killed 或 timeout 状态，结果写回 handoff mailbox、trace buffer 或 candidate output。
10. 控制面回收资源、提交结果、记录 trace，并决定是否重试、回眠或上报错误。

生命周期强调准入、唤醒和回收。Agent 代码不能绕过控制面提交真实副作用；Super Core 也不应在无需高熵处理时长期占用功耗预算。

### Guardian-Execution 唤醒路径

```text
Always-On Clawd-Agent
  listen / heartbeat / classify / memory projection
      |
      | high-entropy request
      v
WAKE_UP_SUPER doorbell
      |
      v
handoff mailbox
  task descriptor / input refs / capability request / recovery anchor
      |
      v
Clawd-Super burst
  LLM / OS / compiler / final commit / recovery
      |
      v
result + trace + sleep request
      |
      v
Always-On Clawd-Agent
```

Trace 至少应能记录 wake reason、handoff latency、Super active time 和 return-to-guard time。后续能耗模型可以把这些字段作为动态功耗范围和 Super 占空比的 proxy。

## 从 Agent runtime 到 APU-IR

Claude Code 类 Agent runtime 的已有分析给出一个重要结论：真正可执行的对象不是自然语言“意向”，而是 `ToolUse`、`CommandDescriptor`、`TaskDescriptor` 和 `ExecutionResult` 这类结构化对象。

九天执行模型正是围绕这些对象工作。低成本监听、上下文投影和简单规则预筛可以留在 Always-On Agent 域；自然语言深推理、系统提示展开、长上下文模型采样和真实副作用提交会触发 Super 域。当模型输出结构化工具调用后，控制面再决定是否把其中一部分降低为 APU-IR 交回 Agent 域。

```text
DigitalTurn
  input_refs
  context_refs
  budget
      |
      v
DecisionRecord
  selected_action_type
  risk_flags
      |
      v
CommandDescriptor / ToolUse
  command_type
  input_schema
  permission_class
  read_only
  concurrency_class
  timeout_budget
      |
      v
APU-IR Task
  capabilities
  memory regions
  program
  barriers
      |
      v
ExecutionResult
  status
  result_ref
  error_class
  state_delta
```

这个降低过程必须遵守三条规则：

- 有真实外部副作用的动作只在控制面提交，Agent Domain 只产生判定、整理、摘要或候选结果。
- 进入 Agent Domain 的任务必须能声明输入、输出、预算、capability 和失败语义。
- APU-IR 的输出必须回到 `ExecutionResult` 或 `state_delta`，再由控制面决定是否进入 transcript、memory、compact 或恢复流程。
- 高熵任务必须显式记录唤醒原因，避免 Super Core 被低价值后台工作频繁拉起。

### ToolUse 映射规则

| ToolUse 类型 | 默认执行域 | 可进入 Agent Domain 的部分 |
| :--- | :--- | :--- |
| 文件读取 | Super Domain 负责真实文件 I/O | 路径规则检查、结果摘要、引用索引、上下文预算裁剪 |
| 文件编辑 | Super Domain 负责最终写入 | diff 预检查、冲突检测、风险标记、补丁片段排序 |
| 搜索/grep/glob | Super Domain 负责访问文件系统 | 匹配结果过滤、排序、去重、摘要、相关性评分 |
| shell/PowerShell | Super Domain 独占 | 命令分类、危险模式识别、参数归一化 |
| MCP/API | Super Domain 负责网络和协议 | JSON 字段抽取、结果截断、schema 校验、错误分类 |
| 子 Agent | Super Domain 管理 sidechain | worker 结果合并、任务状态归约、恢复入口选择 |
| compact/memory | Super Domain 维护原始 transcript | 摘要候选、artifact pointer、引用关系和去重 |

这张表也定义了安全边界：Agent 核不是万能执行器，而是结构化逻辑的加速执行面。

### Memory 投影任务

Claude Code 类 Agent runtime 的 memory 体系把“历史”拆成 transcript、session memory、长期 memory、artifact pointer 和 compact boundary。九天中这类工作应降低为一组无副作用的投影任务，而不是让 Agent 核直接读写长期记忆。

典型 memory 投影任务：

- `memory_header_scan`：扫描 memory header 和 frontmatter，输出候选引用。
- `artifact_preview_pack`：把大型 tool result 的 preview、size、hash 和路径打包成上下文项。
- `transcript_window_check`：检查最近 transcript window 的 parent 链、compact boundary 和 tool_result 配对。
- `context_budget_pack`：在 token/字节预算内选择 memory refs、artifact refs 和最近消息。
- `session_delta_extract`：从上次摘要位置之后提取会话记忆候选。

这些任务只产生引用、摘要候选、排序、风险标记和 trace。长期 memory 文件、transcript JSONL 和 artifact 全文的最终写入仍由 Super Domain 完成。

### 长任务闭环

长任务执行不是一次性 task，而是多轮 `DigitalTurn`、工具调用和 compact 组成的闭环。九天把这个闭环拆为四个阶段：

1. **事件采集**：Agent Domain 常驻监听并整理用户消息、工具调用、工具结果、diff、测试、子 Agent 输出和 compact boundary；需要复杂 OS 或模型路径时唤醒 Super Domain。
2. **结构提取**：Agent Domain 在授权窗口中提取 goal、plan、evidence、decision 和 recovery 的候选 delta。
3. **状态提交**：Super Domain 审核 delta，提交 ledger 新版本，并把大型内容保留为 artifact 引用。
4. **上下文投影**：Agent Domain 在预算内生成下一轮 `ContextProjection`，Super Domain 审核后交给模型。

这使得模型上下文只承担“下一步工作台”的角色。任务真实状态由 ledger、artifact、transcript 和 trace 共同承担。

```text
DigitalTurn N
  ToolUse / ExecutionResult / diff / test log
      |
      v
memory_projection tasks
  ledger_delta_extract
  recovery_anchor_select
  context_budget_pack
      |
      v
Super Domain commit
  ledger version N+1
  artifact refs
  compact boundary
      |
      v
DigitalTurn N+1
  ContextProjection + active evidence
```

### Compact 事务语义

compact 不应被视为普通摘要，而应被视为一次状态事务。一次 compact 至少包含：

- 输入 transcript 范围。
- 输入 ledger 基线版本。
- artifact preview 集合。
- 输出 ledger delta。
- 输出 `ContextProjection`。
- recovery anchor。
- trace event。

如果任一关键输出不可验证，Super Domain 可以只提交 transcript boundary，不提交 ledger delta。这样 compact 失败不会污染长期记忆。

## 任务状态机

v0.1 任务状态如下：

| 状态 | 含义 | 进入条件 | 退出条件 |
| :--- | :--- | :--- | :--- |
| `created` | IR 中声明，但尚未验证 | 任务被加载 | 准入成功或拒绝 |
| `admitted` | 已验证并分配资源 | runtime 准入通过 | 派发到 core |
| `running` | 可执行指令 | 派发或等待解除 | wait、halt、trap、kill |
| `waiting` | 等待 barrier、DMA 或 runtime 事件 | 执行等待类指令 | 条件满足或被 kill |
| `completed` | 正常结束 | 执行 `halt` 或 PC 到尾部 | 控制面回收 |
| `trapped` | 出现错误 | 越界、非法指令、预算耗尽等 | 控制面处理 |
| `killed` | 控制面主动终止 | kill 信号 | 控制面回收 |

当前模拟器可以把 `admitted` 合并到加载过程，但文档和规格保留该状态，方便后续 runtime 明确区分“验证通过”和“已经运行”。

## 任务边界

Agent 任务是九天 v0.1 的最小调度单元。一个任务必须声明：

- 输入区域。
- 输出区域。
- 临时区域。
- 最大周期预算。
- 最大 SPM 使用量。
- 最大 Cluster SRAM 使用量。
- DMA 权限。
- 可用 barrier。
- 异常处理策略。

任务不能隐式访问控制面内存，也不能假设任意地址可读写。所有 host 访问必须由 capability 授权。

## 调度原则

v0.1 调度器优先保证可解释性，不追求最优性能。默认策略：

- 每个任务绑定到一个 Agent core。
- 调度器采用 round-robin，每轮每个 runnable task 执行一条指令。
- Barrier 按名称聚合参与者；未满足参与者数量时任务进入 waiting 状态。
- Barrier 满足参与者数量后释放所有等待任务，并推进到下一条指令。
- DMA 以显式 `dma_copy` 和 `dma_wait` 表达；早期模拟器可同步完成，后续应支持固定延迟队列。
- 如果所有活跃任务都在 waiting 且无 barrier、DMA 或 runtime 事件可释放，调度器报告 deadlock。
- 周期预算按指令或事件递减。
- 任务完成后释放本地资源。

调度器必须让 trace 可解释。即使后续引入更复杂策略，也应能复现任务何时运行、何时等待、何时被释放。

## DMA 与等待

`dma_copy` 表示任务请求一次显式数据搬运。`dma_wait` 表示任务在继续消费数据前等待自己发起的 DMA 完成。

v0.1 的语义约束：

- DMA descriptor 发起时必须完成权限和边界检查。
- DMA 完成前，目标数据不保证可见。
- `dma_wait` 之后，任务可以观察该任务此前 DMA 的结果。
- DMA 失败必须让任务 trap，不能静默丢弃。
- 多个 DMA 的完成顺序应由队列模型或 fence 规则明确。

早期功能模拟器可以同步完成 DMA，但文档中的长期语义应按异步队列理解。这样后续加入 NoC 延迟时不需要改变 APU-IR。

## Barrier 与同步

Barrier 是多个任务之间的显式同步点。每个 barrier 有名称和参与者数量。

执行规则：

- 任务执行 `barrier` 后进入 `waiting`。
- 当等待同一 barrier 的任务数量达到声明参与者数量时，barrier release。
- 被释放任务的 PC 推进到下一条指令。
- release 事件必须进入 trace。
- 如果参与者永远不足，调度器应报告 deadlock。

Barrier 不自动复制数据，也不替代 DMA。它只建立顺序点。数据可见性仍需结合 `flush`、`invalidate`、`fence` 或特定空间规则。

## 内存可见性

Agent 执行面默认不提供全局硬件一致性。任务之间的数据交接必须通过以下动作建立：

- `dma_copy`：显式搬运数据。
- `flush`：发布本地写入。
- `invalidate`：丢弃本地旧副本。
- `barrier`：协调多个任务的顺序点。
- `fence`：约束 DMA 与内存可见副作用顺序。

v0.1 模拟器可以把 `flush`、`invalidate` 和 `fence` 作为 trace 事件处理；后续 RTL 应把它们映射到真实 buffer、队列或 cache 控制。

## 异常语义

v0.1 不追求与传统 CPU 相同的精确异常模型。模拟器与后续 RTL 至少需要支持：

- 非法指令 trap。
- capability 越界 trap。
- SPM 越界 trap。
- Cluster SRAM 越界 trap。
- DMA 越界 trap。
- 周期预算耗尽 trap。
- barrier deadlock trap 或调度器错误。
- 显式 `trap` 指令。

控制面收到异常后可以终止任务、清理 SPM、记录 trace，并选择是否重试。

## Trace 要求

执行模型必须可观察。v0.1 trace 至少应覆盖：

- 任务开始和结束。
- 每次 DMA 发起和完成。
- barrier wait 和 release。
- trap 原因。
- flush、invalidate、fence。
- 关键调度事件。

trace 不是附属功能，而是验证 Agent 原生执行模型是否成立的核心工具。没有 trace，就无法解释显式内存和弱一致性模型下的错误。

## 与 benchmark 的关系

执行模型服务于 benchmark。早期 benchmark 不应只测算术吞吐，而应覆盖：

- 小任务启动开销。
- DMA 搬运与计算重叠。
- barrier 密集同步。
- 非规则 host/cluster/SPM 数据访问。
- capability 检查失败路径。
- deadlock 检测。

这些 benchmark 能帮助判断 APU-IR 和 ISA 是否过度复杂，也能指导后续 RTL 优先实现哪些模块。

## v0.1 收敛标准

执行模型进入 v0.1 可实现状态的标准：

- 任务状态机在模拟器中有对应状态。
- 每个等待状态都有明确释放条件。
- 每个 trap 都能映射到规格中的错误类型。
- DMA 和 barrier 的 trace 足以复现执行顺序。
- 文档中的调度规则与 `simulator/jiutian_sim.py` 行为一致。
- 长任务路径能表达 ledger delta、context projection 和 recovery anchor。

这个模型足以支撑早期 benchmark 和架构讨论，也为后续异步 DMA、NoC 延迟和 RTL 固化保留空间。
