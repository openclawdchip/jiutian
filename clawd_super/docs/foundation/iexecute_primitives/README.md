# 朱雀 IExecute Datapath 基础构件

本目录定义朱雀整数执行数据通路的基础构件。

这些构件来自对整数执行数据通路形态的重新抽象，并用 N07 标准单元、互连、latch、slice 和 PRF 约束重新搭建。它们是 zhuque 后续 integer execute 行为模型和 RTL 的 building blocks。

## 构件文件

- `primitive_index.md`
  - IExecute 数据通路基础构件索引。
- `n07_binding_rules.md`
  - 每类构件的 N07 标准单元、线网、latch、PPA 绑定规则。
- `iexecute_datapath_primitives.md`
  - 完整构件规格，包含输入输出、slice 结构、时延、面积和实现落点。

## 构件原则

- 先构件，后域模块。
- 先数据通路，后控制通路。
- `64-bit` 标量路径默认是 `64` 个纵向 bit slice。
- 快路径使用局部 latch-based time borrowing。
- 慢路径使用多周期 pipeline 或迭代数据通路。
- 所有跨 cluster / 跨结果主干的数据必须显式寄存。
- 每个构件都带 N07 初始 PPA 模型。

## 后续使用

integer execute L2/L3 模块只能组合这些构件，不重新定义底层算术、移位、比较、乘法压缩、除法迭代、CRC/auth/special 或结果融合结构。
