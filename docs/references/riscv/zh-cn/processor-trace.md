# RISC-V Processor Trace 中文全文译文

源文档：`RISC-V_Processor_Trace_TD010_V1.0.pdf`

本文是 RISC-V Processor Trace 1.0 的中文译文稿，用于离线阅读、设计讨论和实现对齐。源 PDF 不属于本项目原创内容，版权、商标和许可归原发布方及贡献者所有。译文保留字段名、packet 名、接口信号名、寄存器名和必要英文术语；若译文与源 PDF 存在差异，以源 PDF 为准。

## 1. 引言

Processor Trace 定义一套低带宽记录处理器执行路径的方法。它不试图记录每条指令的完整状态，而是利用 RISC-V 指令流可由程序映像推断的特点，只输出解码器无法自行推断的信息，例如分支方向、不可推断 PC 跳转、异常/中断、上下文变化和同步点。调试器或离线分析工具把 trace packet 与程序二进制结合，即可重建控制流。

规范核心是 branch trace。数据 trace、快速 profiling、指令间周期计数和 trace transport 被列为未来方向或扩展点。实现通常由 hart 退休接口、trace encoder、trace sink/transport 和主机端 decoder 组成。

| 组件 | 作用 |
|---|---|
| Hart/core | 产生退休指令、PC、分支、异常、中断和上下文信息 |
| Trace encoder | 接收 hart 事件，压缩为 Processor Trace packet |
| Trace sink | 保存或转发 packet，例如片上 SRAM、FIFO、调试接口或外部端口 |
| Decoder | 根据 packet、程序映像和配置参数重建执行路径 |

## 2. 术语和命名

retirement 表示指令已提交并对架构状态生效。单退休实现每周期最多退休一条指令，多退休实现可同周期退休多条。uninferrable PC discontinuity 指解码器无法仅凭程序映像推断的 PC 不连续，例如间接跳转、异常、中断、返回或某些压缩/预测模式下的目标。synchronization 是让 decoder 重新获得完整上下文的 packet。context 表示 hart、特权级、地址空间或其他影响解码的执行上下文。

packet format 按 Format 0、1、2、3 分类。Format 0/1/2 偏向高频压缩分支信息，Format 3 用于同步、异常、上下文和支持信息等较完整记录。

## 3. Branch Trace 模型

Branch trace 的基本思想是：顺序执行的指令不需要逐条输出；直接分支和跳转的目标可由程序映像推断；条件分支只需输出 taken/not-taken；间接跳转、异常和中断等无法推断事件需要输出目标或上下文信息。

### 3.1 指令增量 trace 概念

| 概念 | 中文说明 |
|---|---|
| Sequential instructions | 顺序指令按 PC 递增执行，decoder 可从程序映像自然推进 |
| Uninferable PC discontinuities | 解码器无法推断目标的 PC 不连续，需要 trace 明确报告 |
| Branches | 条件分支需要报告方向；直接目标可由指令编码推断 |
| Interrupts and exceptions | 需要报告异常/中断发生位置、原因和目标上下文 |
| Synchronization | 输出完整 PC/上下文，让 decoder 从丢包或中途接入中恢复 |
| End of trace | 标记 trace 终止或当前流结束 |

### 3.2 可选和运行时可配置模式

| 模式 | 含义 |
|---|---|
| Delta address mode | 用相对地址差编码目标地址，减少 packet 位数 |
| Full address mode | 输出完整地址，便于同步和复杂跳转 |
| Implicit exception mode | 对可由架构和程序映像推断的异常省略部分字段 |
| Sequentially inferable jump mode | 对顺序可推断跳转减少输出 |
| Implicit return mode | 对符合调用/返回约定的 return 省略目标 |
| Branch prediction mode | 结合预测信息减少 branch map 输出 |
| Jump target cache mode | encoder/decoder 共享跳转目标缓存以压缩间接目标 |

这些模式在带宽、硬件复杂度和 decoder 复杂度之间取舍。实现必须通过参数发现机制报告支持模式，调试器/decoder 应按实际配置解释 packet。

## 4. Hart 到 encoder 接口

Trace encoder 需要从 hart 获得足够信息，以便在每条或每组退休指令后决定是否输出 packet。接口既要支持简单单退休核，也要支持乱序、多发射、多退休核。

### 4.1 接口需求

接口至少需要表达：

| 信息 | 用途 |
|---|---|
| retired valid | 本周期是否有退休指令 |
| retired PC | 退休指令地址 |
| instruction bits 或分类 | decoder/encoder 判断指令类型 |
| branch taken | 条件分支方向 |
| target address | 无法推断目标或需要同步时输出 |
| exception/interrupt valid | 标记异常或中断事件 |
| cause/tval/epc 信息 | 构造异常 packet |
| privilege/context | 上下文 packet 或过滤 |
| qualified status | 当前指令是否应被 trace 过滤选中 |

跳转分类和目标推断是接口关键。直接分支、`JAL` 目标可由指令编码推断；`JALR`、return、异常入口、interrupt vector 和 debug 进入通常需要额外目标或上下文。

### 4.2 单退休和多退休

单退休实现可每周期传一条退休指令，encoder 状态机较简单。多退休实现需要在一个周期内传递多个退休 slot，且每个 slot 都可能有分支、异常或过滤状态。规范允许不同接口配置：可以传完整每 slot 信息，也可以在核心内部先折叠为 encoder 需要的事件序列。

多退休实现必须保持 trace 事件顺序与架构退休顺序一致。若同周期多个分支退休，encoder 需要按程序顺序更新 branch map 和 PC 推断状态。异常通常终止后续退休，trace 应反映异常前已退休指令和异常发生点。

### 4.3 可选旁带信号和 trigger

可选 sideband 信号可携带时间戳、hart ID、上下文 ID、过滤 qualifier、分支预测信息、跳转目标缓存命中等。规范主体聚焦 branch trace；timestamp 和更丰富 profiling 信息通常作为可选扩展或未来方向处理。

Debug Module 的 trigger 输出可作为 trace 过滤或启停条件。例如某地址范围命中 trigger 后开始 trace，离开范围后停止 trace，或在特定异常前后输出同步 packet。

## 5. Filtering

Filtering 用于减少 trace 带宽，只记录感兴趣的代码区域、特权级、hart、上下文或 trigger 区间。过滤可以发生在 hart 接口、encoder 内部或 trace sink 前。

过滤必须处理边界条件。进入过滤区域时，decoder 需要同步 packet 或完整 PC，以便从正确位置开始重建。离开过滤区域时，encoder 应输出足够信息标记 trace 不连续，避免 decoder 把缺失区间误当作顺序执行。异常、中断和上下文切换可能改变过滤状态，因此通常需要输出 context 或 support packet。

常见过滤条件包括：

| 条件 | 说明 |
|---|---|
| PC range | 只 trace 某地址范围 |
| privilege mode | 只 trace U/S/M 某些模式 |
| context ID / ASID | 按进程或地址空间过滤 |
| trigger | 由调试触发器启停 trace |
| trace enable | 软件或调试器显式开关 |

## 6. Trace encoder 输出 packet

Processor Trace packet 分为 Format 0、1、2、3。低格式更紧凑，用于高频分支信息；Format 3 带 subformat，用于同步、异常、上下文和支持状态。

### 6.1 Format 3 packet

Format 3 是扩展格式，通过 subformat 区分含义。

| Subformat | 名称 | 用途 |
|---|---|---|
| 0 | Synchronisation | 输出同步信息，例如完整 PC、branch 状态和必要上下文 |
| 1 | Exception | 输出异常/中断相关信息 |
| 2 | Context | 输出上下文变化，例如 privilege/context/地址空间信息 |
| 3 | Support | 输出支持状态、qualifier 状态、trace 控制信息 |

#### 6.1.1 Synchronisation

同步 packet 用于 decoder 初始化、丢包恢复、过滤开始和周期性 resynchronisation。它通常包含完整地址或足以重建完整 PC 的信息。`branch` 字段描述同步点附近的 branch 状态，使 decoder 能从正确的控制流位置继续。

同步频率是实现和系统配置的重要参数。频率越高，丢包恢复越快，但带宽越大。trace sink 容量小或传输链路可能丢包时，应增加同步密度。

#### 6.1.2 Exception

Exception packet 记录异常或中断事件。`tvalepc` 字段携带异常值或 EPC 相关信息，具体解释取决于 packet 配置和异常类型。异常 packet 需要让 decoder 知道从普通控制流转入 trap handler 的边界，并在返回时继续重建。

异常和中断 trace 应区分同步异常、异步中断、不可推断 PC 变化和过滤导致的不连续。若采用 implicit exception mode，某些字段可省略，但 decoder 必须能从架构规则、程序映像和上下文推断。

#### 6.1.3 Context

Context packet 描述解码上下文变化，例如 hart 上下文、特权级、地址空间标识、虚拟化状态或实现定义 context。上下文变化影响同一虚拟地址对应的程序映像，因此 decoder 必须在解析 PC 前知道当前 context。

#### 6.1.4 Support

Support packet 传递辅助状态。`qual_status` 字段可描述当前 trace qualifier/过滤状态，帮助 decoder 知道后续 packet 是否连续、是否被过滤、是否有不可恢复缺口。

### 6.2 Format 2 packet

Format 2 用于比 Format 0/1 更丰富但仍较紧凑的分支和通知信息。

| 字段 | 含义 |
|---|---|
| `notify` | 通知 decoder 发生特殊状态，例如同步需求或事件提示 |
| `updiscon` | unpredicted discontinuity，表示不可预测/不可推断 PC 不连续 |
| `irreport` | implicit return 相关报告 |
| `irdepth` | implicit return 栈或深度信息 |

Format 2 适合在常规 branch map 之外报告少量额外状态，而不必使用完整 Format 3。

### 6.3 Format 1 packet

Format 1 主要携带分支压缩信息。

| 字段 | 含义 |
|---|---|
| `updiscon` | 是否存在不可推断 PC 不连续 |
| `branch_map` | 条件分支 taken/not-taken 位图 |
| `irstatus` | implicit return 状态 |
| `irdepth` | implicit return 深度 |

`branch_map` 按退休顺序记录条件分支方向。decoder 在程序映像中遇到条件分支时消耗一个 bit，决定走 fall-through 还是 target。

### 6.4 Format 0 packet

Format 0 是最紧凑的格式，用于高频分支方向和短状态。

| 字段 | 含义 |
|---|---|
| `subformat` | Format 0 内部子类型 |
| `branch_fmt` | branch map 编码形式 |
| `irstatus` | implicit return 状态 |
| `irdepth` | implicit return 深度 |

Format 0 通过牺牲表达能力换取低带宽。遇到无法表达的事件时，encoder 需要升级到 Format 1/2/3 或输出同步 packet。

## 7. 地址、上下文和压缩编码

地址可以用 full address 或 delta address 表示。Full address 直接提供完整 PC，适合同步和复杂上下文；delta address 输出相对上一个已知地址的差值，带宽更低但依赖 decoder 状态。若发生丢包、过滤缺口或上下文切换，delta 可能无法独立解码，需要先同步。

压缩依赖以下事实：

- 顺序 PC 可由指令长度推断。
- 直接分支目标可由指令编码推断。
- 条件分支只需方向 bit。
- 常见 return 可通过 implicit return 机制推断。
- 重复间接目标可用 jump target cache mode 压缩。

encoder 必须在压缩收益和恢复能力之间平衡。调试器若要求精确随机接入，应配置更频繁同步和更多 full address。

## 8. Exception、interrupt 和 timestamp

异常和中断是 branch trace 的关键不连续点。同步异常与具体指令相关，decoder 需要知道异常 PC、cause 相关信息和 trap 目标。异步中断发生在指令边界，trace 需要表达中断采纳点及其目标上下文。返回指令本身可能通过程序映像推断，也可能因 privilege/context 改变需要 context packet。

timestamp 不属于本规范主体 branch packet 的核心必选字段，但系统可通过 sideband、support packet 或未来扩展携带时间信息。timestamp 可用于性能分析、跨 hart trace 对齐和外设事件关联。实现若提供 timestamp，应说明计数源、宽度、溢出、与 packet 的绑定关系以及过滤期间是否连续计数。

## 9. 参考编码算法

参考算法根据 hart 退休事件维护 decoder 可见状态，并决定何时输出何种 packet。

### 9.1 Format selection

算法优先选择能表达当前事件的最小格式：

1. 若 decoder 状态未知、过滤刚开启、上下文变化或需要周期同步，输出 Format 3 Synchronisation/Context。
2. 若发生异常或中断，输出 Format 3 Exception，必要时附带 context/address。
3. 若出现不可推断 PC 不连续，但可用紧凑字段表达，选择 Format 2 或 Format 1。
4. 若只有条件分支方向，累积到 `branch_map` 并用 Format 0/1 输出。
5. 若 packet 缓冲即将溢出或 branch_map 满，提前 flush。

### 9.2 Resynchronisation

Resynchronisation 在以下场景触发：trace start、decoder 请求、周期计数达到阈值、packet 丢失、过滤边界、上下文变化、不可编码事件或 encoder 状态溢出。同步 packet 应给出足够信息，使 decoder 不依赖之前 packet 即可继续。

### 9.3 多退休考虑

多退休实现中，算法必须按退休顺序处理每个 slot。若一个周期内出现多个分支，`branch_map` bit 顺序仍是架构顺序。若异常出现在某 slot，后续 slot 不应被视作已退休。若过滤状态在同周期内变化，encoder 需要精确标记边界或输出同步。

## 10. 参数与发现

Decoder 必须知道 encoder 参数才能正确解释 packet。参数发现可以通过硬件描述、调试接口、寄存器、ROM 表或 `ipxact` 描述提供。

常见参数包括：

| 参数 | 说明 |
|---|---|
| 支持的 Format | 是否支持 Format 0/1/2/3 及各 subformat |
| 地址宽度 | PC/full address/delta address 宽度 |
| context 字段 | hart/context/privilege/ASID 等字段宽度和含义 |
| branch_map 宽度 | 每个 packet 可携带多少分支方向 |
| implicit return | 是否支持，深度多少 |
| jump target cache | 是否支持，条目数和替换策略 |
| filtering | 支持哪些 qualifier 和过滤源 |
| timestamp | 是否支持，宽度和时钟源 |
| sink/transport | packet 输出路径、FIFO 深度、丢包指示 |

`ipxact` 示例用于描述 encoder 的可发现属性，使工具能自动配置 decoder。

## 11. Decoder

Decoder 输入 trace packet、程序映像和 encoder 参数，输出重建的执行路径。它维护当前 PC、context、分支方向队列、implicit return 状态、jump target cache 和同步状态。

### 11.1 基本流程

1. 等待 Synchronisation packet，建立初始 PC 和 context。
2. 从程序映像读取当前 PC 指令，判断指令长度和类型。
3. 若为顺序指令，PC 前进到下一条。
4. 若为条件分支，从 `branch_map` 消耗一个方向 bit。
5. 若为直接跳转，按指令编码计算目标。
6. 若为间接跳转、异常或中断，从 packet 获取目标或状态。
7. 若收到 Context packet，切换程序映像或地址空间解释。
8. 若发现 packet 缺失或状态不一致，进入失同步状态，等待下一次同步。

### 11.2 错误和缺口处理

Decoder 应检测 branch_map 不足、遇到无法推断目标却无 packet、context 未知、地址超出程序映像、packet 校验失败、sink 报告丢包等条件。发生错误后，工具可以标记 trace gap，并在下一同步点恢复。调试器 UI 应明确显示不可重建区间，避免把推测路径当作真实执行。

## 12. 调试器和分析工具消费流程

典型消费流程如下：

1. 读取或发现 encoder 参数。
2. 配置 trace filter、同步周期、sink 和 transport。
3. 启动 trace，并记录程序映像、符号表和上下文映射。
4. 从 sink 取出 packet 流，按时间或顺序输入 decoder。
5. Decoder 重建 PC 流、异常/中断事件和上下文切换。
6. 工具把 PC 映射到函数、源码、基本块和性能统计。
7. 若有 timestamp 或外部事件流，按时间戳对齐多 hart 和设备事件。

对于多 hart trace，工具需要区分 hart ID 或 context，并分别维护 decoder 状态。若 packet 流复用同一 transport，应有足够 framing 或 context packet 标识来源。

## 13. 实现注意事项

硬件实现应关注：

- Hart 退休接口必须按架构顺序提供事件。
- 异常/中断与已退休指令边界必须精确。
- 过滤边界必须输出同步或不连续标记。
- Packet FIFO 溢出必须可检测，并触发 resynchronisation。
- 压缩模式的状态机要能在 reset、flush、debug halt 和 context switch 时复位。
- 多退休、多分支和同周期异常要有确定优先级。
- Trace sink 与 encoder 跨时钟域时要保证 packet 原子性。
- 若实现 timestamp，必须定义与 packet 的采样关系和溢出行为。

软件和工具实现应关注：

- 不同 encoder 参数不能混用。
- 程序映像必须与执行时二进制一致。
- 自修改代码、动态加载和地址空间切换需要 context 或同步支持。
- 过滤会造成 trace gap，不能当作连续执行。
- 异常和 interrupt trace 需要结合特权架构 trap 规则解释。

## 14. 未来方向

规范提到若干未来方向：

| 方向 | 说明 |
|---|---|
| Data trace | 记录加载/存储地址或数据，用于数据流调试 |
| Fast profiling | 低成本统计执行热点和路径 |
| Inter-instruction cycle counts | 记录指令间周期数，支持性能分析 |
| Transport | 标准化 packet 传输、framing、压缩和错误报告 |

这些能力可能与 branch trace 共用 context、timestamp、filter 和 sink，但需要额外带宽和隐私/安全考虑。

## 15. 示例代码与 packet

示例的意义在于展示 decoder 如何从少量 packet 恢复控制流。例如一段包含条件分支、间接跳转和异常的代码，trace 不输出每条顺序指令，只输出分支方向 bit、不可推断目标、异常 packet 和同步点。decoder 对照程序映像逐条推进，遇到分支时消耗 `branch_map`，遇到异常 packet 时切换到 trap handler，再根据返回路径继续。

实现测试应包含：全顺序代码、密集条件分支、间接跳转、函数调用/返回、异常/中断、过滤启停、丢包恢复、多 hart 交织、上下文切换和 packet FIFO 边界。

## 16. 翻译完成状态

本文件已从入口/摘要稿改为 Processor Trace 中文正文译文稿，覆盖 trace 总体模型、trace encoder/sink、同步、branch trace、exception/interrupt trace、timestamp、过滤、packet 类型、压缩/编码、上下文/地址信息、hart 到 encoder 接口、参数发现、decoder、调试器消费流程和实现注意事项。
