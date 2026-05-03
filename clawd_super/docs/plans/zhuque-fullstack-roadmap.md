# 朱雀全量推进路线

## 1. 总体策略

朱雀按三层推进：

1. 文档层
2. 行为模型层
3. RTL 层

三层都要求“全量覆盖”，但每层内部可以按依赖关系分批完成。

所有阶段都受 `docs/zhuque-design-methodology.md` 约束。模块规格、行为模型和 RTL 需要同时检查功能语义、物理可实现性和验证可闭合性。

## 2. 文档阶段

文档阶段的交付目标：

- 顶层总体架构文档
- 工程原则
- foundation 底层部件层
- 全设计域一级规格文档
- 全设计域二级子模块规格文档
- 域之间的依赖说明

文档阶段完成后，应能回答：

- 每个域负责什么
- 每个域如何连接
- 每个域先建什么行为模型
- 每个域后续 RTL 如何拆层

## 3. 行为模型阶段

行为模型建议按以下顺序推进：

1. foundation primitives
2. shared cells and models
3. decode and uop
4. rename
5. issue
6. integer execute
7. vector execute
8. loadstore and mmu
9. commit and retire
10. ifetch
11. level2 cache
12. cluster fabric
13. platform control and debug
14. top integration

这个顺序的目的不是先做“最小闭环”，而是先解决下游最容易形成语义 contract 的域，再把前端和集群级语义接上。

## 4. RTL 阶段

RTL 阶段按与行为模型相同的域顺序推进，但每个域内部要遵循下面的顺序：

1. package 和 interface
2. state element
3. small primitive
4. data path
5. control path
6. top orchestrator
7. domain-level testbench

## 5. 域间依赖

| 域 | 依赖 |
|---|---|
| ifetch | platform control、level2、top integration |
| decode | ifetch contract、shared models |
| rename | decode |
| issue | rename、integer execute、vector execute、loadstore |
| integer execute | decode contract |
| vector execute | decode contract |
| loadstore and mmu | issue、level2、platform control |
| commit and retire | rename、issue、loadstore、execute |
| level2 cache | loadstore、cluster fabric |
| cluster fabric | level2、platform control |
| top integration | 全部域 |

## 6. 行为模型完成标准

某个域进入 RTL 前，应满足：

- 有稳定的状态对象
- 有 directed test
- 有 flush/replay/exception 场景
- 有至少一条域级集成场景
- 对外接口字段已经固定

## 7. RTL 完成标准

某个域的 RTL 达到第一阶段完成，需满足：

- filelist 可独立编译
- package/interface 完整
- 顶层模块和子模块边界稳定
- 有基本仿真
- 与行为模型的关键事务一致
