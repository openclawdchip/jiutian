# 朱雀设计方法学

## 1. 方法定位

朱雀采用自底向上的物理约束驱动方法。

设计起点不是抽象的流水线宽度，也不是先写 RTL 再等待后端修正，而是先建立三类底层能力账本：

- 标准单元能力账本
- 存储宏单元能力账本
- 互连线网能力账本

这三类账本共同决定朱雀的架构宽度、模块切片、队列容量、cache 组织、PRF 组织、pipeline 深度、floorplan 分区和验证闭环。

## 1.1 Core 搭建主线

朱雀 core 的搭建分成两个不可交换的阶段。

第一阶段先搭完整数据通路。所有取指、译码、重命名、发射、执行、访存、回写、提交和缓存访问的数据承载路径，都必须先用 foundation primitive 连接成全 core 骨架。这个阶段只保留最小握手、stall、flush 接口和延迟标记，不把复杂控制状态机提前塞进数据通路。

第二阶段再添加控制通路。控制通路围绕已经成形的数据通路增加状态机、仲裁、异常、恢复、replay、credit、功耗管理和 debug 观察。控制逻辑必须服从数据通路的物理切分，不允许为了控制集中化破坏 slice、bank 和 cluster 的边界。

整个过程始终由 floorplan 驱动。每添加一个 primitive、一个 slice、一个 bank、一个 pipeline stage，都必须同步记录面积、逻辑时延、存储访问时延、线延时和目标周期 slack。设计评审时不只看功能是否连通，还要看该连接在物理上是否能闭合。

## 1.2 Slice Base 硬约束

朱雀宽数据通路采用 slice-based 组织。以 `64-bit` 数据通路为例，默认实现为 `64` 个纵向 bit slice，而不是一个横向单体 `64-bit` 大块。

同一个 bit slice 内纵向贯穿寄存、旁路、选择、算术、比较、mask、写回和局部观察点。跨 bit 的结构只在必要位置出现，例如 carry、归约、全零检测、异常聚合和结果打包，并且必须分层、切拍或局部化。

slice-based 设计的目标是让版图从一开始就形成规则条带：

- 每个 slice 有稳定宽度和局部布线通道。
- 相邻 slice 之间只传递必要的短距离信号。
- PRF、bypass、ALU、load data、store data、vector lane 可以沿同一纵向切分对齐。
- 宽 mux、宽 broadcast、宽 compare 不允许默认做成单点集中结构。

## 1.3 Latch Base 硬约束

朱雀关键高频数据通路采用 latch-based 思路建模和实现。行为模型、RTL 和 PPA 账本都必须支持相位边界、透明窗口和时间借用，而不是只按 edge-triggered flop 粗略估算。

latch-based 设计用于解决 `4.0GHz` 下局部路径不均衡的问题。短路径释放的相位余量可以被相邻长路径借用，但必须满足下面约束：

- latch 相位边界在模块文档中显式标注。
- 时间借用只在局部 slice 或局部 cluster 内使用。
- 跨 cluster、跨 cache bank、跨 core 边界不依赖隐式时间借用。
- 行为模型记录逻辑 latency，PPA 模型记录相位预算和借用窗口。
- RTL 初版可先用等价 pipeline 抽象表达，后续物理实现再替换为 latch-based 结构。

## 2. 基本判断

朱雀的目标是高频、宽发射、大容量和强并发同时成立。这样的核心不能只从逻辑功能出发设计。

必须先回答下面三个问题：

- 一个标准单元逻辑路径在目标频率下还能容纳多少级有效逻辑。
- 一个 SRAM / PRF 宏单元在目标频率下能做多大、多少端口、多少 bank。
- 一条局部线、跨簇线、跨 core 线和跨 tile 线分别需要多少时延预算。

如果这三个问题没有被量化，前端宽度、执行单元数量、ROB 容量、cache 容量和 cluster 规模都只是纸面参数。

## 3. 底层 PPA 账本

### 3.1 标准单元账本

标准单元账本记录：

- 基本门面积
- DFF 面积
- 输入电容
- 代表性 FO4 时延
- DFF `CP->Q` 时延
- 多驱动强度的面积和时延变化
- 多阈值单元的速度、面积和功耗取舍

朱雀设计中，所有关键控制路径都要用标准单元账本估算逻辑深度。典型对象包括：

- branch redirect
- wakeup/select
- rename allocation
- bypass select
- load hit path
- store commit
- interrupt/trap select

### 3.2 存储宏单元账本

存储宏单元账本记录：

- SRAM family
- PRF family
- capacity
- shape
- port model
- area
- access time
- cycle time
- banking recommendation

朱雀设计中，所有大容量结构都必须映射到存储宏单元账本。典型对象包括：

- L1I
- L1D
- L2
- L3 slice
- BTB
- branch predictor table
- ROB payload storage
- issue queue payload storage
- integer / FP / vector PRF
- load queue / store queue data arrays

### 3.3 互连线网账本

互连线网账本记录：

- 金属层角色
- 典型宽度
- 典型间距
- 单位或结构电容
- 单位或结构电阻
- RC-only 时延锚点
- 推荐使用场景

朱雀设计中，所有跨模块热路径都要被线网账本约束。典型对象包括：

- redirect 到 next PC
- decode 到 rename
- rename 到 issue
- wakeup 到 select
- execute 到 writeback
- writeback 到 reclaim
- LSU 到 L1D
- L1D 到 L2
- core 到 tile fabric

## 4. 频率预算方法

朱雀最高主频目标为 `4.0GHz`，单周期预算为：

```text
Tcycle = 250ps
```

每条关键路径都按下面形式建模：

```text
path_delay =
  launch_flop_clkq
  + local_logic_delay
  + mux_and_select_delay
  + wire_delay
  + memory_access_delay
  + setup_and_margin
```

设计文档中不允许只写“单周期完成”。必须说明：

- 这条路径是否真的属于单周期热路径。
- 如果是单周期路径，它的逻辑预算、线网预算和 margin 分别是多少。
- 如果不能稳定单周期完成，它在哪一级切拍。
- 如果依赖 SRAM，它使用哪类宏、几级访问、几级返回。

## 5. 架构参数生成方法

朱雀的架构参数从底层账本向上生成，而不是孤立指定。

### 5.1 宽度参数

译码、rename、dispatch、commit、issue、load/store、vector 执行宽度必须同时满足：

- 前端供给能力
- rename map/free-list 端口能力
- issue queue bank 能力
- PRF 读写端口能力
- writeback 总线能力
- commit/reclaim 回收能力
- floorplan 可布线能力

当宽度增加时，优先采用切片和 bank，而不是构造单体超宽模块。

### 5.2 容量参数

ROB、issue queue、load/store queue、predictor table、PRF、cache 容量必须同时满足：

- 行为模型容量需求
- 存储宏单元 shape
- bank 数量
- 访问延迟
- 旁路和回写距离
- floorplan 面积形状

容量不能只用 entries 表达。每个大容量结构都要明确：

- 逻辑容量
- 物理 bank 数
- 每 bank 容量
- 端口模型
- 读写时序
- replay / flush / recover 代价

### 5.3 主频参数

主频目标优先级高于单体模块的形式整齐性。

为了守住 `4.0GHz`，允许并且鼓励：

- 多级预测
- 多级 cache access
- 分片译码
- 分片 rename
- 分布式 issue
- 局部 bypass
- 多级 result merge
- 跨簇切拍
- 跨 tile 切拍

## 6. Floorplan 优先规则

朱雀的 floorplan 不是 RTL 完成后的后端动作，而是模块定义的输入条件。

每个模块文档都要回答：

- 模块应靠近哪个上游模块。
- 模块应靠近哪个下游模块。
- 哪些信号是局部热路径。
- 哪些信号允许跨区。
- 哪些信号必须切拍。
- 哪些数组必须 bank 化。
- 哪些控制路径必须移出热路径。

模块拆分优先服务物理邻接关系。逻辑上属于同一功能的结构，如果物理上必须分布，就应拆成多个子模块；逻辑上属于不同功能的结构，如果共享同一条热路径，可以在同一 floorplan 区域内协同设计。

## 7. 文档方法

朱雀文档按三层展开：

- L1：设计域
- L2：朱雀模块
- L3：朱雀子模块

L2 不是源文件粒度，而是 floorplan 和行为边界都稳定的功能块。

L3 是 L2 下面可直接写行为模型的子模块。每个 L3 文档必须包含：

- 输入字段
- 输出字段
- 状态对象
- 数据通路规则
- 控制通路规则
- 时序假设
- 异常与恢复
- backpressure
- replay / flush
- 可观测事件
- 行为模型落点
- RTL 落点

数据通路文档必须有结构框图。控制通路文档必须有状态机。

## 8. 行为模型方法

行为模型不是 RTL 的影子，也不是伪代码摘要。它是架构语义和物理约束之间的可执行合同。

每个行为模型都要表达：

- 正常事务
- 资源冲突
- bank conflict
- backpressure
- flush
- replay
- recover
- fault
- latency class
- throughput limit
- counters / observability

行为模型必须保留物理相关参数，例如：

- bank 数
- queue 深度
- issue 宽度
- access latency
- bypass latency
- replay latency
- cross-cluster latency

这些参数用于提前发现架构参数和 floorplan 目标之间的矛盾。

## 9. RTL 方法

RTL 从行为模型和模块文档生成，不从抽象功能一次性平铺。

每个 RTL 模块按下面顺序落地：

1. package / type
2. interface
3. state element
4. data path primitive
5. control state machine
6. local arbitration
7. top orchestrator
8. assertions
9. directed testbench

RTL 中必须显式表达：

- reset 边界
- pipeline 边界
- ready/valid 或等价握手
- flush 优先级
- replay 优先级
- fault 优先级
- counter / debug 可观测点

宽模块默认按 slice / bank / cluster 实现，不默认使用集中式大 mux、大 CAM 或大广播。

## 10. 验证方法

朱雀验证按三条线并行推进：

- 行为模型验证
- RTL 局部验证
- PPA 约束验证

行为模型验证回答语义是否正确。RTL 局部验证回答实现是否一致。PPA 约束验证回答该结构是否可能在目标频率和 floorplan 中成立。

每个设计域进入下一级前，必须满足：

- 文档字段完整
- 行为模型可执行
- directed tests 覆盖正常路径和异常路径
- RTL 编译通过
- 关键路径有初步时序预算
- 大数组有宏单元映射计划
- 跨区连线有切拍计划

## 11. AI 辅助方法

AI 在朱雀工程中承担四类任务：

- 生成和维护模块文档
- 生成和检查行为模型
- 生成 RTL 初版和测试
- 读取后端报告并反馈到架构参数

AI 不直接替代 signoff。AI 的任务是扩大搜索、减少重复劳动、保持账本一致，并把 PPA 反馈及时带回架构和模块文档。

每一次 AI 生成都要回到三个问题：

- 这个结构在功能上是否正确。
- 这个结构在物理上是否可能。
- 这个结构在验证上是否可闭合。

## 12. 闭环流程

朱雀采用下面的闭环：

```text
底层 PPA 账本
  -> 架构参数
  -> floorplan 分区
  -> L1/L2/L3 文档
  -> 行为模型
  -> RTL
  -> 综合 / APR / STA 报告
  -> PPA 账本更新
  -> 架构参数修正
```

任何一级发现不可闭合，都回到上一级修正，而不是在后端强行修补。

## 13. 当前朱雀落点

当前朱雀方法学已经具备三类底层输入：

- 标准单元逻辑和互连锚点：`C:\chipwiki\wiki\synthesis\n07-logic-and-interconnect-ppa-envelope-v1.md`
- SRAM / PRF 宏单元锚点：`C:\chipwiki\wiki\synthesis\n07-sram-ppa-envelope-v1.md`
- 朱雀 floorplan 约束：`D:\ai_brain\jiutian\clawd_super\docs\zhuque-floorplan-driven-design.md`
- 朱雀底层部件层：`D:\ai_brain\jiutian\clawd_super\docs\foundation\README.md`

下一步所有模块文档、行为模型和 RTL 都应使用这三类输入作为约束条件。
