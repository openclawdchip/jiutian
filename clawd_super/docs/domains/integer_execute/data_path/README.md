# Integer Execute Data Path

## 1. 范围

整数执行数据通路覆盖 result bypass、fast ALU、compare/branch assist、shift/bitfield、multiply/MAC、divide、CRC/auth/special transform 和 result merge/writeback。

本文用于定义朱雀目标数据通路。所有模块先给出结构框图，再给出 N07 slice 版图。

## 2. 结构规模摘要

| 项 | 数值 |
|---|---:|
| datapath units | `52` |
| module count | `52` |
| logic LOC | `14842` |
| assign count | `3009` |
| always count | `495` |

## 3. 分区

| 分区 | 结构图 | 版图 | 单元 | 模块 | 行数 | assign | always | 估算路径 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [Result Bypass Router](operand_bypass_lane.md) | [结构图](../../../assets/datapath_units/integer_execute/result_bypass_router_structure.png) | [版图](../../../assets/datapath_units/integer_execute/result_bypass_router_floorplan.png) | `42` | `42` | `13542` | `2432` | `493` | `151.386 ps` |
| [Fast ALU Flags Slice](fast_alu_flags.md) | [结构图](../../../assets/datapath_units/integer_execute/fast_alu_flags_structure.png) | [版图](../../../assets/datapath_units/integer_execute/fast_alu_flags_floorplan.png) | `40` | `40` | `11999` | `2344` | `393` | `167.890 ps` |
| [Compare Branch Assist](compare_branch_assist.md) | [结构图](../../../assets/datapath_units/integer_execute/compare_branch_assist_structure.png) | [版图](../../../assets/datapath_units/integer_execute/compare_branch_assist_floorplan.png) | `8` | `8` | `4286` | `777` | `151` | `162.638 ps` |
| [Shift Rotate Bitfield](shift_bitfield.md) | [结构图](../../../assets/datapath_units/integer_execute/shift_bitfield_structure.png) | [版图](../../../assets/datapath_units/integer_execute/shift_bitfield_floorplan.png) | `19` | `19` | `8455` | `1616` | `300` | `188.894 ps` |
| [Multiply MAC Reduce](multiply_mac_reduce.md) | [结构图](../../../assets/datapath_units/integer_execute/multiply_mac_reduce_structure.png) | [版图](../../../assets/datapath_units/integer_execute/multiply_mac_reduce_floorplan.png) | `12` | `12` | `3504` | `729` | `122` | `207.398 ps` |
| [Divide Remainder Iterative](divide_iterative_math.md) | [结构图](../../../assets/datapath_units/integer_execute/divide_iterative_math_structure.png) | [版图](../../../assets/datapath_units/integer_execute/divide_iterative_math_floorplan.png) | `13` | `13` | `6009` | `1051` | `262` | `193.894 ps` |
| [CRC Auth Special Transform](special_crc_auth.md) | [结构图](../../../assets/datapath_units/integer_execute/special_crc_auth_structure.png) | [版图](../../../assets/datapath_units/integer_execute/special_crc_auth_floorplan.png) | `32` | `32` | `11247` | `2015` | `433` | `203.146 ps` |
| [Result Merge Writeback](result_merge_writeback.md) | [结构图](../../../assets/datapath_units/integer_execute/result_merge_writeback_structure.png) | [版图](../../../assets/datapath_units/integer_execute/result_merge_writeback_floorplan.png) | `16` | `16` | `7787` | `1644` | `289` | `174.390 ps` |

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

1. 先实现 packet 和 slice 类型。
2. 再实现 bank / queue / local array wrapper。
3. 然后实现本地 pipeline register 或 latch boundary。
4. 最后接入控制通路状态机。
