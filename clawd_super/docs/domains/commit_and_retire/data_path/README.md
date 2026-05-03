# Commit And Retire Data Path

## 1. 范围

commit 数据通路覆盖 ROB payload、completion merge、retire window、precise fault、reclaim、store commit 和 redirect payload。

本文用于定义朱雀目标数据通路。控制状态机不在本文展开。

## 2. 结构规模摘要

| 项 | 数值 |
|---|---:|
| datapath units | `3` |
| module count | `2` |
| logic LOC | `1882` |
| assign count | `238` |
| always count | `42` |

高频数据面 token：`l2`=253, `mask`=133, `l1`=112, `vector`=48, `way`=42, `commit`=3。

## 3. 分区

| 分区 | 图 | 单元 | 模块 | 行数 | assign | always | 估算路径 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [ROB Payload Segment](rob_payload.md) | [PNG](../../../assets/datapath_units/commit_and_retire/rob_payload.png) | `3` | `2` | `1882` | `238` | `42` | `172.390 ps` |
| [Retire Window Data Path](retire_window.md) | [PNG](../../../assets/datapath_units/commit_and_retire/retire_window.png) | `3` | `2` | `1882` | `238` | `42` | `190.894 ps` |
| [Reclaim Store Redirect Outputs](reclaim_store_redirect.md) | [PNG](../../../assets/datapath_units/commit_and_retire/reclaim_store_redirect.png) | `2` | `2` | `1659` | `238` | `42` | `190.894 ps` |

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

