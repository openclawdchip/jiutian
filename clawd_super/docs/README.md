# 朱雀文档体系

本目录定义 `zhuque / 朱雀` 的新工程规格。

这套文档是朱雀实现的正式起点。每份文档都回答三个问题：

1. 这个模块在朱雀里负责什么。
2. 这个模块对外暴露什么接口和状态。
3. 这个模块后续的行为模型和 RTL 应该落成什么样子。

## 文档分层

- `zhuque-architecture-overview.md`
  - 顶层架构、层级和全局命名
- `zhuque-floorplan-driven-design.md`
  - 从物理规划反推各域组织方式和切片原则
- `zhuque-floorplan-sketch-v1.md`
  - 第一版 core / tile floorplan 草图和主脊柱示意
- `zhuque-floorplan-core-v2.md`
  - core 级细化 floorplan 图，以及独立的 dispatch / redirect / writeback 分图
- `zhuque-engineering-principles.md`
  - 工程约束、接口风格、模型和 RTL 对齐规则
- `plans/zhuque-fullstack-roadmap.md`
  - 文档、行为模型、RTL 的全量推进顺序
- `domains/*.md`
  - 各功能域的正式规格
- `domains/<domain>/README.md`
  - 各功能域的模块入口
- `domains/<domain>/INDEX.md`
  - 各功能域的模块总索引
- `domains/<domain>/data_path/*.md`
  - 各功能域的数据通路模块规格
- `domains/<domain>/control_path/*.md`
  - 各功能域的控制通路模块规格
- `domains/<domain>/top_mixed/*.md`
  - 各功能域的混合模块规格

## 模块级文档

当前每个设计域都下钻到模块级文档层。

- 一级文档负责定义域目标、固定指标和总边界
- 一级文档同时负责定义 floorplan 约束、物理分区和关键时序闭环
- 模块文档负责按 `data_path` / `control_path` / `top_mixed` 分开定义
- 数据通路文档包含结构框图
- 控制通路文档包含状态机
- 每个模块都单独成文，不合并为单一大文档
- 后续行为模型默认直接对接模块文档
