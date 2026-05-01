# 九天 APU 产品简介

九天 APU 是一个面向 Agent 生成代码的开源处理器架构项目。它把“未来大量代码由 Agent 生成”作为硬件设计前提，而不是把 Agent 代码继续塞进为人类软件优化的传统执行栈。

## 核心定位

九天不是传统 CPU、GPU 或 NPU 的简单变体。

- CPU 擅长兼容复杂人类软件。
- GPU 擅长规整的大规模张量计算。
- NPU 擅长固定神经网络算子。
- 九天面向动态生成、分支复杂、生命周期短、访存碎片化、但又需要高并发执行的 Agentic 逻辑任务。

九天的目标是成为 Agent 时代的逻辑执行层。

## 架构主张

传统软件栈为了兼容性和可维护性，保留了大量抽象层：操作系统、驱动、ABI、库、框架、系统调用、虚拟内存和硬件缓存一致性。这些机制对人类软件有价值，但对 Agent 生成的短生命周期逻辑片段来说，经常变成控制开销。

九天采用双平面设计：

- 控制面：运行操作系统、runtime、调度、安全和调试。
- Agent 执行面：运行经过授权的 Agent 生成代码片段。

这种设计允许九天同时保留生态入口和原生效率。

## 目标用户

九天当前面向以下人群：

- 体系结构研究者。
- RISC-V 和自定义 ISA 研究者。
- Agent runtime 开发者。
- 编译器和 IR 设计者。
- 边缘智能、自动化和实时逻辑系统开发者。
- 对开源 AI 计算基础设施感兴趣的社区贡献者。

## 目标工作负载

九天优先研究以下 workload：

### Agent 规则执行

大量短分支和规则判断，例如权限过滤、事件分类、策略选择和工具调用前置判断。

### 结构化数据流水线

JSON、日志、表格记录和消息队列数据的解析、过滤、变换和聚合。

### 任务图与依赖图遍历

Agent 在多工具、多状态、多约束之间做调度时，会产生大量轻量图遍历和依赖检查。

### 短生命周期 JIT 片段

Agent 为某个具体任务生成一次性逻辑，执行后立即回收。传统优化器和复杂缓存层级很难在这类场景中摊销成本。

### 非规则内存访问

Agent 任务经常访问小块、不连续、生命周期明确的数据。九天通过显式 SPM、Cluster SRAM 和 DMA 把数据移动变成可控动作。

### 长期任务记忆

长任务 Agent 的共同短板是任务执行到上下文窗口上限后，compact 可能丢失结构化进度，导致重复探索甚至从头开始。九天把长期任务状态拆成目标、计划、证据、决策和恢复账本，由控制面持久化，由 Agent 执行面高速生成下一轮上下文投影。

这让 Agent 不再依赖模型记住全部历史，而是每一轮都从可审计 ledger 恢复当前目标、已完成步骤、关键证据、失败路径和下一步动作。

v0.1 对长期记忆的定位是规格闭环先行：Agent 执行面只生成候选 ledger delta、artifact preview 引用、context projection 和 recovery anchor；控制面保留 transcript、artifact 正文、已提交 ledger 和最终提交权。这样可以把长期记忆路径保持为无外部副作用的可验证任务，而不是把任意文件或历史记录交给生成代码直接修改。

## 技术组成

### Clawd-Super

控制面高性能核心，负责系统软件、调度、安全和异常处理。它是九天进入现有软件生态的入口。

### Clawd-Agent

Agent 执行面核心，负责运行 Agent ISA 指令。它优先追求高执行密度、低控制开销和显式数据搬运。

### APU-IR

任务图中间表示。它描述 memory region、capability、task、budget、barrier 和 Agent ISA program，是 Agent 生成逻辑进入硬件前的验证边界。

### SPM

Scratchpad Memory，由软件显式控制。它让数据生命周期可以被编译器和 runtime 直接表达。

### Cluster SRAM

Agent cluster 内共享的近端 SRAM，用于任务之间的中间结果交换和局部数据复用。

### Honeycomb NoC

蜂窝式片上网络，用于连接 Agent cluster、DMA、trace、外部内存和控制面。

## 当前可运行能力

当前仓库已经提供：

- APU-IR JSON 示例。
- v0.1 功能模拟器。
- round-robin 多任务调度。
- barrier 阻塞与释放。
- capability 检查。
- SPM、Cluster SRAM 和 host memory 模型。
- 同步 DMA 搬运、trap、字符串 trace 和结果导出。
- 单元测试。

这构成 v0.1 的模拟器最小闭环：从 APU-IR 输入，到任务准入、授权检查、指令执行、显式数据搬运、同步、异常和 trace，再到可检查的输出。它不是周期精确模型，也不是完整外设或长期记忆实现；ledger、artifact、context projection 和 recovery anchor 目前主要由规格定义，后续按 coverage 矩阵逐步进入模拟器和 benchmark。

最快运行：

```powershell
python simulator\jiutian_sim.py simulator\examples\copy_add.json
python -m unittest discover simulator
```

## 开源路线

九天采用文档和模拟器先行路线：

1. 先定义概念和术语。
2. 再定义 specs。
3. 用 simulator 跑通最小语义闭环。
4. 用 trace 和 benchmark 识别结构性优势与规格过度复杂之处。
5. 语义稳定后进入 RTL。

这种路线避免过早把不成熟语义硬化进硬件。

## 与传统架构的差异

九天不是用更多核心堆叠传统软件模型，而是改变 Agent 生成代码的执行契约：

- 不默认依赖标准 ABI。
- 不默认依赖全局硬件缓存一致性。
- 不把系统调用作为 Agent hot path。
- 不让生成代码绕过安全边界。
- 不用不可解释的性能主张替代可复现实验。

## 当前限制

v0.1 仍处于种子阶段：

- 模拟器不是周期精确模型。
- DMA 暂为同步语义。
- NoC 延迟尚未建模。
- MMIO 外设尚未实现。
- RTL 尚未开始。

这些限制是有意保留的。九天当前更重视语义清晰和可验证性。
