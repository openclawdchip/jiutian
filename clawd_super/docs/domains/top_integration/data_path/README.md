# Top Integration Datapath Data Path

## 1. 范围

top integration 数据通路描述 core 内主干 packet、cache/fabric 边界、debug/trace 边界和跨域 FIFO/bridge。

本文用于定义朱雀目标数据通路。控制状态机不在本文展开。

## 2. 结构规模摘要

| 项 | 数值 |
|---|---:|
| datapath units | `4` |
| module count | `4` |
| logic LOC | `18518` |
| assign count | `22` |
| always count | `0` |

高频数据面 token：`l2`=2297, `data`=2091, `tag`=1212, `valid`=682, `issue`=356, `addr`=318, `tlb`=298, `bank`=258, `fill`=235, `fifo`=230。

## 3. 分区

| 分区 | 图 | 单元 | 模块 | 行数 | assign | always | 估算路径 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [Core Packet Spine](core_packet_spine.md) | [PNG](../../../assets/datapath_units/top_integration/core_packet_spine.png) | `4` | `4` | `18518` | `22` | `0` | `153.886 ps` |
| [Cache Fabric Boundary](cache_fabric_boundary.md) | [PNG](../../../assets/datapath_units/top_integration/cache_fabric_boundary.png) | `4` | `4` | `18518` | `22` | `0` | `177.390 ps` |
| [Service Sideband Data Path](service_sideband.md) | [PNG](../../../assets/datapath_units/top_integration/service_sideband.png) | `4` | `4` | `18518` | `22` | `0` | `160.886 ps` |

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

