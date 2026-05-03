# Rename Data Path

## 1. 范围

rename 数据通路覆盖 map table、free-list、checkpoint、reclaim 和 renamed uop 输出。

本文用于定义朱雀目标数据通路。控制状态机不在本文展开。

## 2. 结构规模摘要

| 项 | 数值 |
|---|---:|
| datapath units | `31` |
| module count | `30` |
| logic LOC | `127495` |
| assign count | `23618` |
| always count | `2428` |

高频数据面 token：`decode`=15536, `valid`=10557, `tag`=8198, `data`=5086, `mask`=3837, `way`=2583, `ready`=1797, `cache`=1173, `tlb`=1097, `addr`=954。

## 3. 分区

| 分区 | 图 | 单元 | 模块 | 行数 | assign | always | 估算路径 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [Map Table Read Slice](map_read.md) | [PNG](../../../assets/datapath_units/rename/map_read.png) | `16` | `15` | `117036` | `22420` | `2290` | `170.390 ps` |
| [Free-List Allocate Slice](free_allocate.md) | [PNG](../../../assets/datapath_units/rename/free_allocate.png) | `18` | `17` | `122944` | `23347` | `2427` | `186.894 ps` |
| [Checkpoint Recovery Data Path](checkpoint_recovery.md) | [PNG](../../../assets/datapath_units/rename/checkpoint_recovery.png) | `14` | `13` | `91075` | `17803` | `1603` | `208.398 ps` |
| [Renamed Uop Dispatch Pack](renamed_dispatch.md) | [PNG](../../../assets/datapath_units/rename/renamed_dispatch.png) | `15` | `14` | `121335` | `23024` | `2410` | `172.390 ps` |

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

