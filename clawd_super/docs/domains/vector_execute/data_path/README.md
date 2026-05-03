# Vector Execute Data Path

## 1. 范围

vector execute 数据通路围绕 VRF bank、lane group、mask/permute、MAC/FP 和 vector writeback 展开。

本文用于定义朱雀目标数据通路。控制状态机不在本文展开。

## 2. 结构规模摘要

| 项 | 数值 |
|---|---:|
| datapath units | `151` |
| module count | `151` |
| logic LOC | `90790` |
| assign count | `16799` |
| always count | `1511` |

高频数据面 token：`data`=12858, `bank`=3867, `mask`=3436, `l1`=2746, `addr`=1843, `way`=1529, `l2`=1264, `fault`=630, `tag`=332, `valid`=298。

## 3. 分区

| 分区 | 图 | 单元 | 模块 | 行数 | assign | always | 估算路径 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [VRF Operand Bank Read](vrf_operand.md) | [PNG](../../../assets/datapath_units/vector_execute/vrf_operand.png) | `73` | `73` | `71104` | `12193` | `1355` | `168.138 ps` |
| [Vector Integer Lane Field](valu_lane.md) | [PNG](../../../assets/datapath_units/vector_execute/valu_lane.png) | `59` | `59` | `40478` | `8861` | `952` | `177.390 ps` |
| [Permute Mask Predicate](permute_mask.md) | [PNG](../../../assets/datapath_units/vector_execute/permute_mask.png) | `74` | `74` | `66543` | `13103` | `1036` | `193.894 ps` |
| [Vector MAC FP Cluster](mac_fp.md) | [PNG](../../../assets/datapath_units/vector_execute/mac_fp.png) | `54` | `54` | `57615` | `8502` | `1037` | `210.398 ps` |
| [Vector Writeback Merge](vector_writeback.md) | [PNG](../../../assets/datapath_units/vector_execute/vector_writeback.png) | `16` | `16` | `27664` | `5302` | `617` | `174.390 ps` |

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

