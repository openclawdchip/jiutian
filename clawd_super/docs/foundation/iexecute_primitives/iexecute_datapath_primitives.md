# IExecute Datapath Primitives

## 1. 范围

本文定义朱雀整数执行数据通路基础构件。

这些构件用于搭建后续 integer execute 域的数据通路。控制状态机、发射策略、异常仲裁和 replay 调度不在本文展开；本文只保留必要的 valid、kill、fault、replay payload 位置。

## 2. 输入输出总线

### 2.1 Execute Operand Packet

| 字段 | 说明 |
|---|---|
| `valid` | operand packet 有效 |
| `op_kind` | 操作类别 |
| `src0[63:0]` | 源 0 |
| `src1[63:0]` | 源 1 |
| `src2[63:0]` | 源 2，乘加或 special 使用 |
| `imm[63:0]` | immediate |
| `dst_phys` | 目标物理寄存器 |
| `rob_id` | ROB 对齐 |
| `pred_meta` | branch / compare 元数据 |
| `fault_meta` | fault payload |
| `replay_meta` | replay payload |
| `slice_id` | 数据 slice 或 lane group 标记 |

### 2.2 Execute Result Packet

| 字段 | 说明 |
|---|---|
| `valid` | result 有效 |
| `result[63:0]` | 标量结果 |
| `flags` | zero、sign、carry、overflow、compare、saturate |
| `dst_phys` | 目标物理寄存器 |
| `rob_id` | ROB 对齐 |
| `bypass_class` | local / near / writeback |
| `fault_meta` | fault payload |
| `replay_meta` | replay payload |

## 3. `zq_ix_operand_slice`

### 数据功能

`zq_ix_operand_slice` 接收 PRF read data 和本地 bypass data，输出执行构件使用的 phase-aligned operand。

```text
PRF read data
near bypass data
writeback bypass data
  -> local bypass select
  -> operand phase latch
  -> src0/src1/src2/imm bit slice
```

### Slice 结构

| 项 | 定义 |
|---|---|
| slice count | `64` bit slice |
| state | `IX_OPRD_L0` phase latch |
| local mux | per-bit 3-way 或 4-way select |
| cross-slice | none |

### N07 绑定

| 项 | 初始值 |
|---|---:|
| logic depth | `4 FO4` |
| mux penalty | `18ps` |
| wire class | `M5 local = 15.5ps` |
| margin | `40ps` |
| estimated path | `128.378ps` |
| slack | `121.622ps` |

面积模型：

```text
area ~= 64 * (3 mux-equivalent + latch-equivalent)
```

该构件必须贴近 integer PRF bank 和 fast lane，不能跨越执行区读取远端 operand。

## 4. `zq_ix_addsub_bit_slice`

### 数据功能

`zq_ix_addsub_bit_slice` 是 add/sub/logic 的 1-bit 基础构件。

```text
src0_bit
src1_bit xor sub
carry_in
logic_op
  -> sum_bit
  -> logic_bit
  -> carry_out
```

### Slice 结构

| 项 | 定义 |
|---|---|
| granularity | `1-bit` |
| replicated count | `64` |
| local inputs | src0、src1、sub、carry_in、logic_op |
| local outputs | sum、logic_result、carry_out |
| cross-slice | carry only through `zq_ix_carry_group` |

### N07 绑定

| 项 | 初始值 |
|---|---:|
| logic depth | `5 FO4` |
| mux penalty | `10ps` |
| wire class | bit-local |
| margin | `35ps` |
| estimated path without carry group | `107.130ps` |
| slack | `142.870ps` |

面积模型：

```text
area_per_bit ~= FA-equivalent + XOR-equivalent + local mux
area_lane ~= 64 * area_per_bit
```

## 5. `zq_ix_carry_group`

### 数据功能

`zq_ix_carry_group` 将 `64` bit carry 分为多级 group，避免单条长 carry 进入 `4GHz` 热路径。

```text
bit carry generate/propagate
  -> group4 carry
  -> group8 carry
  -> group16 select
  -> final carry / overflow
```

### 分组规则

| 层级 | 数量 | 说明 |
|---|---:|---|
| group4 | `16` | bit-local carry small group |
| group8 | `8` | local select |
| group16 | `4` | lane quarter |
| group64 | `1` | final flag only，不能驱动全路径数据 |

### N07 绑定

| 项 | 初始值 |
|---|---:|
| logic depth per group stage | `4..6 FO4` |
| local wire | `M5 = 15.5ps` |
| cross group wire | `M10 = 4.421ps` with pipeline/latch |
| pipeline rule | latch-split for fast lane |

carry group 只能服务 arithmetic result 和 flags，不允许被复用成跨执行簇控制广播。

## 6. `zq_ix_flag_reduce`

### 数据功能

`zq_ix_flag_reduce` 从 bit slice 结果形成 flags。

输出 flags：

- zero
- sign
- carry
- overflow
- unsigned compare
- signed compare
- saturate
- predicate summary

### 数据结构

```text
result_bit[63:0]
carry_group
sign bits
  -> local reduce tree
  -> flag packet
```

### N07 绑定

| 项 | 初始值 |
|---|---:|
| logic depth | `8 FO4` |
| mux penalty | `8ps` |
| wire class | `M5/M10 reduce tree` |
| wire budget | `16ps` |
| margin | `40ps` |
| estimated path | `147.886ps` |
| slack | `102.114ps` |

zero reduce 必须分为 `8 x 8-bit` 局部 reduce，再做二级合并。

## 7. `zq_ix_compare_slice`

### 数据功能

`zq_ix_compare_slice` 执行 equality、less-than、fused branch compare 和 compare result formatting。

```text
src0[63:0]
src1[63:0]
condition
  -> eq tree
  -> signed/unsigned less tree
  -> branch condition
  -> compare result
```

### N07 绑定

| 项 | 初始值 |
|---|---:|
| local compare depth | `7 FO4` |
| reduce depth | `6 FO4` |
| mux penalty | `12ps` |
| wire budget | `16ps` |
| margin | `40ps` |
| latch rule | compare reduce can split at `IX_EXEC_L1` |

比较路径靠近 redirect spine，branch condition 输出与 normal result data 分离。

## 8. `zq_ix_shift_stage`

### 数据功能

`zq_ix_shift_stage` 实现 shift、rotate、extract、insert 和 bitfield 基础数据移动。

```text
src[63:0]
shift_amount[5:0]
mode
  -> stage1 shift 1/2/4
  -> stage2 shift 8/16
  -> stage3 shift 32 / rotate merge
  -> shifted result
```

### N07 绑定

| 项 | 初始值 |
|---|---:|
| logic depth per stage | `4..5 FO4` |
| stage count | `3` |
| mux penalty per stage | `8..12ps` |
| pipeline rule | stage2 may latch for `4GHz` |
| wire class | local `M5~M10` |

Barrel shift 不能作为单级 `64-bit` 大 mux，必须按阶段构造。

## 9. `zq_ix_mask_merge_slice`

### 数据功能

`zq_ix_mask_merge_slice` 处理 byte mask、predicate mask、conditional select、saturation select 和 bitfield insert。

```text
primary_result
secondary_result
mask[63:0]
mode
  -> per-bit merge
  -> lane result
```

### N07 绑定

| 项 | 初始值 |
|---|---:|
| logic depth | `4 FO4` |
| mux penalty | `14ps` |
| wire budget | `15.5ps` |
| margin | `35ps` |
| estimated path | `119.378ps` |
| slack | `130.622ps` |

mask merge 是 per-bit slice 本地构件，不允许拉成集中式 result mux。

## 10. `zq_ix_mul_encode_slice`

### 数据功能

`zq_ix_mul_encode_slice` 负责乘法 operand sign handling、window encode 和 partial-product seed。

```text
src0
src1
signedness
accumulate mode
  -> window encode
  -> partial product rows
```

### N07 绑定

| 项 | 初始值 |
|---|---:|
| logic depth | `8 FO4` |
| mux penalty | `12ps` |
| wire budget | `16ps` |
| margin | `40ps` |
| pipeline rule | output register before compress |

该构件属于 `IX_MID`，不进入 fast branch/ALU 闭环。

## 11. `zq_ix_mul_compress_stage`

### 数据功能

`zq_ix_mul_compress_stage` 是 partial product 压缩树构件。

支持压缩形式：

- 4:2
- 6:2
- 8:2
- 9:2

```text
partial product rows
  -> compressor stage 0
  -> compressor stage 1
  -> compressor stage 2
  -> sum/carry rows
```

### N07 绑定

| 项 | 初始值 |
|---|---:|
| stage logic depth | `8..12 FO4` |
| wire class | local `M5/M10` |
| margin | `45ps` |
| pipeline rule | every compressor band can register |
| result class | multi-cycle |

压缩树按 lane group 规则摆放，不允许所有 partial rows 拉回单点中心。

## 12. `zq_ix_mul_finish_slice`

### 数据功能

`zq_ix_mul_finish_slice` 完成 carry-propagate、截断、扩展、flag 和 accumulate result normalize。

```text
sum row
carry row
mode
  -> final add
  -> high/low select
  -> flag packet
```

### N07 绑定

| 项 | 初始值 |
|---|---:|
| final add | uses `zq_ix_addsub_bit_slice` + `zq_ix_carry_group` |
| mux penalty | `16ps` |
| pipeline rule | register before result merge |
| result class | `IX_MID` |

## 13. `zq_ix_div_prepare_slice`

### 数据功能

`zq_ix_div_prepare_slice` 准备除法迭代数据。

包含：

- signedness normalize
- abs operand
- leading-zero count
- power-of-two fast detect
- initial remainder / divisor align

### N07 绑定

| 项 | 初始值 |
|---|---:|
| clz reduce | multi-level tree |
| pow2 detect | zero reduce + one-hot detect |
| pipeline rule | prepare register before iteration |
| result class | `IX_SLOW` |

除法 prepare 不与 fast ALU 共享 flags reduce 的热路径。

## 14. `zq_ix_div_step_slice`

### 数据功能

`zq_ix_div_step_slice` 是除法每周期迭代构件。

```text
remainder
divisor
quotient
step_state
  -> compare/subtract
  -> qbit
  -> remainder update
  -> quotient update
```

### N07 绑定

| 项 | 初始值 |
|---|---:|
| per-step logic | compare + addsub |
| state | DFF register per iteration |
| pipeline rule | iterative multi-cycle |
| result class | `IX_SLOW` |

每 step 可以使用 `zq_ix_compare_slice` 和 `zq_ix_addsub_bit_slice`，但必须在 divide lane 局部实例化。

## 15. `zq_ix_crc_fold_slice`

### 数据功能

`zq_ix_crc_fold_slice` 实现 CRC polynomial fold 和 update。

```text
data
crc_state
poly_select
  -> xor fold network
  -> updated crc
```

### N07 绑定

| 项 | 初始值 |
|---|---:|
| logic type | XOR/NAND/INV network |
| fold rule | tree split by byte / halfword |
| pipeline rule | multi-cycle or side-lane |
| result class | `IX_SLOW` |

CRC fold 不进入 simple ALU result mux 的第一层。

## 16. `zq_ix_mix_shuffle_slice`

### 数据功能

`zq_ix_mix_shuffle_slice` 提供 nibble、byte、word 级 shuffle 和 inverse shuffle。

```text
src[63:0]
shuffle_mode
  -> cell shuffle
  -> inverse shuffle
  -> mixed result
```

### N07 绑定

| 项 | 初始值 |
|---|---:|
| logic depth | `4..8 FO4` per shuffle stage |
| mux penalty | mode dependent |
| pipeline rule | local stage latch if more than two shuffle stages |
| result class | special side-lane |

shuffle 是结构化短交换网络，不允许作为任意 `64 x 64` crossbar。

## 17. `zq_ix_auth_mix_slice`

### 数据功能

`zq_ix_auth_mix_slice` 为 pointer/auth transform 提供 mix、substitution、mask 和 multiply-like helper 数据通路。

```text
pointer payload
modifier payload
key / tweak payload
mask
  -> setup
  -> substitution
  -> mix multiply
  -> compare / encode
  -> auth result
```

### N07 绑定

| 项 | 初始值 |
|---|---:|
| result class | `IX_SLOW` |
| pipeline rule | side-lane multi-stage |
| wire rule | local only，no fast lane intrusion |
| state | local registers between major stages |

auth mix 是稀有路径构件，不能占用 fast lane 中央 result merge 第一层。

## 18. `zq_ix_special_result_slice`

### 数据功能

`zq_ix_special_result_slice` 将 divide、CRC、auth、rare helper 的结果规格化为统一 result packet。

```text
slow_lane_result
fault_meta
replay_meta
  -> result normalize
  -> special result packet
```

### N07 绑定

| 项 | 初始值 |
|---|---:|
| logic depth | `6 FO4` |
| mux penalty | `18ps` |
| wire budget | `16ps` |
| margin | `45ps` |
| pipeline rule | register before global result merge |

## 19. `zq_ix_result_merge_slice`

### 数据功能

`zq_ix_result_merge_slice` 分层合并 fast、shift、mul、div、special 的 result packet。

```text
fast result
shift result
mul result
div result
special result
  -> local 2:1 / 3:1 merge
  -> lane result packet
  -> writeback register
```

### N07 绑定

| 项 | 初始值 |
|---|---:|
| logic depth | `10 FO4` |
| mux penalty | `20ps` |
| wire budget | `16ps` |
| margin | `40ps` |
| estimated path | `174.390ps` |
| slack | `75.610ps` |
| pipeline rule | `IX_WB_R` before writeback spine |

result merge 必须分层。禁止所有执行输入同时进入一个中心 mux。

## 20. `zq_ix_writeback_packet_slice`

### 数据功能

`zq_ix_writeback_packet_slice` 生成进入 writeback spine 的数据包。

| 字段 | 说明 |
|---|---|
| `valid` | result valid |
| `dst_phys` | 目标 PRF |
| `result[63:0]` | 结果 |
| `flags` | flag packet |
| `rob_id` | ROB 对齐 |
| `bypass_class` | bypass 可见性 |
| `fault_meta` | fault payload |
| `replay_meta` | replay payload |

### N07 绑定

| 项 | 初始值 |
|---|---:|
| state | DFF register |
| data bits | implementation dependent |
| DFF area | `0.2736 um^2/bit` |
| wire rule | `M12+` if entering core writeback spine |
| borrow | none across writeback boundary |

## 21. 构件依赖矩阵

| Primitive | 依赖 |
|---|---|
| `zq_ix_operand_slice` | `zq_ready_valid_pipe`、local latch |
| `zq_ix_addsub_bit_slice` | standard-cell FA/XOR/MUX |
| `zq_ix_carry_group` | addsub bit slice |
| `zq_ix_flag_reduce` | reduce tree |
| `zq_ix_compare_slice` | compare bit + reduce tree |
| `zq_ix_shift_stage` | staged mux |
| `zq_ix_mask_merge_slice` | per-bit mux |
| `zq_ix_mul_encode_slice` | Booth/window encode style primitive |
| `zq_ix_mul_compress_stage` | compressor cells |
| `zq_ix_mul_finish_slice` | addsub + carry group |
| `zq_ix_div_prepare_slice` | clz + pow2 detect |
| `zq_ix_div_step_slice` | compare + addsub |
| `zq_ix_crc_fold_slice` | XOR fold |
| `zq_ix_mix_shuffle_slice` | staged shuffle cells |
| `zq_ix_auth_mix_slice` | substitution + mix + mask |
| `zq_ix_special_result_slice` | result normalize |
| `zq_ix_result_merge_slice` | staged mux + packet merge |
| `zq_ix_writeback_packet_slice` | register slice |

## 22. 行为模型最小接口

每个构件行为模型必须提供：

- `params`
- `input_packet`
- `output_packet`
- `latency_class`
- `area_estimate`
- `delay_estimate`
- `step()`
- `flush()` 或 kill 输入处理
- event counters

## 23. RTL 最小接口

每个构件 RTL 必须提供：

- parameterized width
- valid / ready 或 local valid enable
- kill input
- input payload
- output payload
- local assertions
- PPA annotation comment block
