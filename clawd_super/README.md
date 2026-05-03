# zhuque / 朱雀

本目录是 `zhuque / 朱雀` 的工程目录。

`zhuque` 是模块顶层 codename，中文名统一使用 `朱雀`。本目录用于定义并实现朱雀自己的文档、行为模型、RTL 与验证资产。

## 当前状态

当前阶段以方法学、底层部件和全 core 数据通路骨架建设为主。

- 已完成：总体架构文档、分域文档、模块级文档目录、工程原则、推进路线、foundation 约束文档
- 进行中：foundation 行为模型与全 core 数据通路骨架
- 未开始：RTL 代码

## 工程原则

- 顶层命名统一使用 `zhuque`
- 中文名统一使用 `朱雀`
- 先文档，后行为模型，最后 RTL
- 先搭完整 core 数据通路，再叠加控制通路
- 宽数据通路默认采用纵向 slice-based 结构
- 高频局部数据通路默认预留 latch-based 时间借用能力
- 每个模块推进时同步记录 floorplan、面积、时延和 `4.0GHz` slack
- 文档按模块拆分，不合并为单一大文档
- 行为模型优先表达架构语义，不追求与实现结构一一绑定
- RTL 以可读、可验证、可维护为第一目标

## 目录

- `docs/`
  - 新生成的设计文档体系
- `docs/domains/`
  - 按功能域拆分的一级与模块级规格
- `docs/foundation/`
  - 朱雀底层部件层，定义标准单元、SRAM/PRF 宏和互连约束之上的可复用 primitive
- `docs/datapath/`
  - 朱雀完整 core 数据通路骨架、slice/bank/latch 映射和 PPA 初始账本
- `docs/plans/`
  - 端到端推进路线和阶段计划

## 建议阅读顺序

1. `docs/zhuque-architecture-overview.md`
2. `docs/zhuque-design-methodology.md`
3. `docs/foundation/README.md`
4. `docs/datapath/README.md`
5. `docs/zhuque-engineering-principles.md`
6. `docs/plans/zhuque-fullstack-roadmap.md`
7. `docs/domains/` 下的各域模块文档
