# LoadStore And MMU Data Path

## 1. 范围

loadstore/MMU 数据通路覆盖 AGU、DTLB、L1D、load/store queue、forwarding、miss/fill/replay 和 page-walk/fault 数据面。

本文用于定义朱雀目标数据通路。控制状态机不在本文展开。

## 2. 结构规模摘要

| 项 | 数值 |
|---|---:|
| datapath units | `52` |
| module count | `50` |
| logic LOC | `99849` |
| assign count | `14273` |
| always count | `3058` |

高频数据面 token：`way`=13290, `data`=9282, `l2`=8032, `tlb`=4854, `tag`=4137, `cache`=2839, `l1`=2774, `valid`=2034, `fill`=1451, `miss`=1317。

## 3. 分区

| 分区 | 图 | 单元 | 模块 | 行数 | assign | always | 估算路径 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [AGU Address Slice](agu_address.md) | [PNG](../../../assets/datapath_units/loadstore_and_mmu/agu_address.png) | `30` | `30` | `86219` | `12456` | `2767` | `153.386 ps` |
| [DTLB Translate And Permission](dtlb_translate.md) | [PNG](../../../assets/datapath_units/loadstore_and_mmu/dtlb_translate.png) | `46` | `44` | `99601` | `14244` | `3058` | `177.390 ps` |
| [L1D Tag Data Bank Pipe](l1d_bank.md) | [PNG](../../../assets/datapath_units/loadstore_and_mmu/l1d_bank.png) | `44` | `42` | `99596` | `14245` | `3058` | `142.134 ps` |
| [Load Queue Forwarding](load_forward.md) | [PNG](../../../assets/datapath_units/loadstore_and_mmu/load_forward.png) | `28` | `27` | `95140` | `13681` | `2895` | `193.894 ps` |
| [Store Address Data Queue](store_queue.md) | [PNG](../../../assets/datapath_units/loadstore_and_mmu/store_queue.png) | `32` | `31` | `96440` | `13887` | `2931` | `177.390 ps` |
| [Miss Fill Replay Path](miss_fill_replay.md) | [PNG](../../../assets/datapath_units/loadstore_and_mmu/miss_fill_replay.png) | `34` | `33` | `90244` | `13315` | `2619` | `170.138 ps` |
| [MMU Walk Fault Merge](mmu_walk_fault.md) | [PNG](../../../assets/datapath_units/loadstore_and_mmu/mmu_walk_fault.png) | `38` | `37` | `98912` | `14118` | `3043` | `193.894 ps` |

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

