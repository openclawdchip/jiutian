# 路线图

## Phase 0：架构种子

- 定义九天与 Honeycomb 的术语体系。
- 起草 v0.1 架构规格。
- 定义 Agent 执行域。
- 定义控制面与 Agent 执行面的边界。
- 建立 benchmark 分类。

## Phase 1：最小模拟器

- 实现一个小型 Agent 集群的功能模拟器。
- 以高层模型描述超大核任务分发。
- 建模 Agent 核执行、SPM、DMA、Barrier 与异常。
- 输出内存搬运与同步行为的 trace。

## Phase 2：APU-IR 原型

- 定义初始任务图 IR。
- 加入内存放置标注。
- 加入显式 DMA 与 Barrier 操作。
- 将简单 kernel 降低为模拟器指令。

## Phase 3：硬件微架构原型

- 规格化单个 Agent 核。
- 规格化带本地 SRAM 的集群。
- 定义基础 NoC packet 格式与路由行为。
- 为选定模块创建可综合 RTL。

## Phase 4：Benchmark 与评估

- 构建 Agentic 逻辑工作负载。
- 在公平条件下与传统 CPU baseline 对比。
- 测量吞吐、延迟、内存流量和能耗 proxy。
- 发布可复现的 benchmark 脚本与 trace。
