# Decode And Uop Data Path

## 1. 范围

译码数据通路把 instruction slot 转成统一 uop payload，并按 `4 x 4` slice 对齐 rename。

本文用于定义朱雀目标数据通路。控制状态机不在本文展开。

## 2. 结构规模摘要

| 项 | 数值 |
|---|---:|
| datapath units | `11` |
| module count | `5` |
| logic LOC | `36508` |
| assign count | `983` |
| always count | `88` |

高频数据面 token：`data`=2315, `bank`=126, `way`=88, `tag`=73, `replay`=37, `valid`=29, `l2`=22, `prf`=19, `fault`=18, `decode`=14。

## 3. 分区

| 分区 | 图 | 单元 | 模块 | 行数 | assign | always | 估算路径 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [Instruction Boundary And Expand](boundary_expand.md) | [PNG](../../../assets/datapath_units/decode_and_uop/boundary_expand.png) | `6` | `3` | `35344` | `902` | `88` | `170.390 ps` |
| [Opcode Classify And Immediate](opcode_immediate.md) | [PNG](../../../assets/datapath_units/decode_and_uop/opcode_immediate.png) | `8` | `4` | `33540` | `982` | `88` | `203.398 ps` |
| [Uop Pack Metadata](uop_pack.md) | [PNG](../../../assets/datapath_units/decode_and_uop/uop_pack.png) | `1` | `1` | `26986` | `140` | `0` | `186.894 ps` |

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

