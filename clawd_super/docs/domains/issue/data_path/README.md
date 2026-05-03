# Issue Data Path

## 1. 范围

issue 数据通路覆盖 dispatch 入队、payload bank、ready bitset、wakeup/select 和 grant packet。

本文用于定义朱雀目标数据通路。控制状态机不在本文展开。

## 2. 结构规模摘要

| 项 | 数值 |
|---|---:|
| datapath units | `33` |
| module count | `32` |
| logic LOC | `65072` |
| assign count | `10555` |
| always count | `1231` |

高频数据面 token：`tag`=16487, `data`=10320, `addr`=4380, `way`=1231, `issue`=737, `valid`=464, `bank`=106, `l1`=97, `queue`=70, `store`=47。

## 3. 分区

| 分区 | 图 | 单元 | 模块 | 行数 | assign | always | 估算路径 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [Dispatch Payload Banks](dispatch_payload.md) | [PNG](../../../assets/datapath_units/issue/dispatch_payload.png) | `15` | `14` | `24083` | `4518` | `547` | `170.390 ps` |
| [Wakeup Ready Matrix](wakeup_ready.md) | [PNG](../../../assets/datapath_units/issue/wakeup_ready.png) | `18` | `18` | `57853` | `9986` | `1108` | `186.894 ps` |
| [Oldest Ready Select Grant](select_grant.md) | [PNG](../../../assets/datapath_units/issue/select_grant.png) | `11` | `10` | `33116` | `5679` | `433` | `186.894 ps` |
| [Replay Resource Data Path](replay_resource.md) | [PNG](../../../assets/datapath_units/issue/replay_resource.png) | `7` | `7` | `31392` | `5296` | `389` | `172.390 ps` |

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

