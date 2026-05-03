# Frontend IFetch Data Path

## 1. 范围

前端数据通路覆盖 next PC、预测携带、L1I bank、fetch sector、align、predecode 和 fetch queue。

本文用于定义朱雀目标数据通路。控制状态机不在本文展开。

## 2. 结构规模摘要

| 项 | 数值 |
|---|---:|
| datapath units | `51` |
| module count | `46` |
| logic LOC | `69944` |
| assign count | `5452` |
| always count | `4859` |

高频数据面 token：`data`=32172, `cache`=13245, `tag`=10658, `way`=6366, `valid`=2502, `l1`=1136, `addr`=1059, `bank`=616, `l2`=520, `mask`=477。

## 3. 分区

| 分区 | 图 | 单元 | 模块 | 行数 | assign | always | 估算路径 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [Next-PC Redirect Spine](next_pc_redirect.md) | [PNG](../../../assets/datapath_units/frontend_ifetch/next_pc_redirect.png) | `25` | `22` | `65960` | `4977` | `4812` | `146.886 ps` |
| [L1I Sector Data Path](l1i_sector.md) | [PNG](../../../assets/datapath_units/frontend_ifetch/l1i_sector.png) | `47` | `42` | `69737` | `5436` | `4859` | `134.882 ps` |
| [Align Predecode Queue](align_predecode.md) | [PNG](../../../assets/datapath_units/frontend_ifetch/align_predecode.png) | `24` | `22` | `61373` | `5060` | `4846` | `172.390 ps` |

## 4. 统一接口

所有分区至少支持：

- `valid`
- `ready`
- `packet`
- `kill_token`
- `replay_token`
- `fault_meta`
- `area_estimate`
- `delay_estimate`

## 5. 实现顺序

1. 先实现本目录中的 packet 和 slice 类型。
2. 再实现 bank / queue / macro wrapper。
3. 然后实现本地 pipeline register 或 latch boundary。
4. 最后接入控制通路状态机。

