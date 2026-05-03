# Platform Control Debug Data Path

## 1. 范围

平台控制与调试数据通路覆盖 interrupt payload、debug register access、trace capture、ATB packet 和事件 FIFO。

本文用于定义朱雀目标数据通路。控制状态机不在本文展开。

## 2. 结构规模摘要

| 项 | 数值 |
|---|---:|
| datapath units | `33` |
| module count | `30` |
| logic LOC | `30818` |
| assign count | `2924` |
| always count | `1424` |

高频数据面 token：`addr`=4744, `data`=1573, `way`=1429, `l1`=1171, `l2`=837, `mask`=620, `fifo`=598, `valid`=573, `trace`=376, `tlb`=250。

## 3. 分区

| 分区 | 图 | 单元 | 模块 | 行数 | assign | always | 估算路径 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [Interrupt Event Payload](interrupt_payload.md) | [PNG](../../../assets/datapath_units/platform_control_debug/interrupt_payload.png) | `31` | `29` | `30724` | `2891` | `1424` | `158.886 ps` |
| [Debug Register Access Path](debug_register.md) | [PNG](../../../assets/datapath_units/platform_control_debug/debug_register.png) | `31` | `29` | `30724` | `2891` | `1424` | `177.390 ps` |
| [Trace Capture FIFO](trace_capture.md) | [PNG](../../../assets/datapath_units/platform_control_debug/trace_capture.png) | `29` | `28` | `28990` | `2881` | `1421` | `177.390 ps` |

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

