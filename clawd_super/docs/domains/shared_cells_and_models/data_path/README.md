# Shared Cells And Models Data Path

## 1. 范围

共享单元数据通路覆盖 FIFO、寄存器复制、仲裁器、同步桥和可复用 packet shell。

本文用于定义朱雀目标数据通路。控制状态机不在本文展开。

## 2. 结构规模摘要

| 项 | 数值 |
|---|---:|
| datapath units | `76` |
| module count | `73` |
| logic LOC | `6931` |
| assign count | `582` |
| always count | `123` |

高频数据面 token：`data`=647, `fifo`=280, `l2`=268, `ecc`=249, `addr`=232, `way`=133, `mask`=130, `valid`=97, `tag`=84, `cache`=61。

## 3. 分区

| 分区 | 图 | 单元 | 模块 | 行数 | assign | always | 估算路径 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [Shared FIFO Pipe](fifo_pipe.md) | [PNG](../../../assets/datapath_units/shared_cells_and_models/fifo_pipe.png) | `26` | `25` | `3514` | `357` | `72` | `153.886 ps` |
| [Shared Arbiter Packet](arbiter_packet.md) | [PNG](../../../assets/datapath_units/shared_cells_and_models/arbiter_packet.png) | `41` | `39` | `4456` | `414` | `90` | `153.886 ps` |
| [Register Repeat Sync](register_repeat_sync.md) | [PNG](../../../assets/datapath_units/shared_cells_and_models/register_repeat_sync.png) | `30` | `29` | `3699` | `354` | `85` | `149.634 ps` |

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

