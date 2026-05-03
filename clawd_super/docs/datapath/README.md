# 朱雀 Full-Core 数据通路

本目录定义朱雀 core 的完整数据通路骨架。

数据通路先于控制通路建立。这里固定 payload、slice、bank、pipeline、latch、macro 和 PPA 账本，后续控制状态机只能覆盖在这些边界之上。

## 文件

- `full_core_datapath.md`
  - full-core 数据通路主规格，覆盖 fetch 到 commit、LSU 到 L2/fabric 的完整链路。
- `slice_bank_latch_map.md`
  - bit slice、uop slice、cache bank、PRF bank、latch 相位边界映射。
- `datapath_ppa_ledger.md`
  - N07 初始面积、时延、macro 数量和 `4.0GHz` slack 账本。

## 固定原则

- `64-bit` 标量数据通路默认拆成 `64` 个纵向 bit slice。
- `16` 路 uop 主干默认拆成 `4 x 4` 个 uop slice。
- 前端 `192B/cycle` 默认拆成 `3 x 64B` fetch sector，再重排到 `4 x 4` decode slice。
- PRF、ROB、issue queue、L1、L2、L3 默认 bank 化。
- 高频局部路径默认预留 latch-based 时间借用。
- 跨 cluster、跨 cache bank、跨 core、跨 tile 路径必须显式切拍。
- 每个数据通路段都要记录面积、时延、线网层级和 slack。

## 后续使用

行为模型从这些数据通路文件生成事务对象、latency class、bank conflict 和 replay 事件。

RTL 从这些数据通路文件生成 package、interface、pipeline register、latch boundary、macro wrapper 和局部 primitive 组合。
