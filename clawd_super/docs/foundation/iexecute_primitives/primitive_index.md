# IExecute Datapath Primitive Index

## 1. Primitive 分类

朱雀整数执行数据通路基础构件分成八类。

| 类别 | Primitive | 主要用途 |
|---|---|---|
| operand | `zq_ix_operand_slice` | PRF read output、bypass、operand latch |
| arithmetic | `zq_ix_addsub_bit_slice` | add/sub/logic 基础 bit slice |
| arithmetic | `zq_ix_carry_group` | 分组 carry 和 carry select |
| flags | `zq_ix_flag_reduce` | zero/sign/carry/overflow/saturate |
| compare | `zq_ix_compare_slice` | fused compare、branch condition |
| shift | `zq_ix_shift_stage` | shift/rotate/bitfield 分级 barrel |
| mask | `zq_ix_mask_merge_slice` | byte mask、predicate、conditional merge |
| multiply | `zq_ix_mul_encode_slice` | partial product 编码 |
| multiply | `zq_ix_mul_compress_stage` | 4:2 / 6:2 / 8:2 / 9:2 压缩 |
| multiply | `zq_ix_mul_finish_slice` | final carry-propagate 和 result normalize |
| divide | `zq_ix_div_prepare_slice` | sign、abs、clz、power-of-two fast detect |
| divide | `zq_ix_div_step_slice` | qbit、remainder update、迭代 step |
| crc | `zq_ix_crc_fold_slice` | polynomial fold / update |
| special | `zq_ix_mix_shuffle_slice` | nibble/byte shuffle、inverse shuffle |
| special | `zq_ix_auth_mix_slice` | pointer/auth transform 的 GF/mix 数据路径 |
| special | `zq_ix_special_result_slice` | rare integer helper result normalize |
| result | `zq_ix_result_merge_slice` | fast / slow / special result merge |
| result | `zq_ix_writeback_packet_slice` | result tag/data/fault/replay packet |

## 2. 组合关系

快整数路径：

```text
zq_ix_operand_slice
  -> zq_ix_addsub_bit_slice
  -> zq_ix_carry_group
  -> zq_ix_flag_reduce
  -> zq_ix_result_merge_slice
```

比较与分支路径：

```text
zq_ix_operand_slice
  -> zq_ix_compare_slice
  -> zq_ix_flag_reduce
  -> zq_ix_result_merge_slice
```

移位与 bitfield 路径：

```text
zq_ix_operand_slice
  -> zq_ix_shift_stage
  -> zq_ix_mask_merge_slice
  -> zq_ix_result_merge_slice
```

乘法路径：

```text
zq_ix_operand_slice
  -> zq_ix_mul_encode_slice
  -> zq_ix_mul_compress_stage
  -> zq_ix_mul_finish_slice
  -> zq_ix_result_merge_slice
```

除法路径：

```text
zq_ix_operand_slice
  -> zq_ix_div_prepare_slice
  -> zq_ix_div_step_slice
  -> zq_ix_special_result_slice
  -> zq_ix_result_merge_slice
```

CRC / special 路径：

```text
zq_ix_operand_slice
  -> zq_ix_crc_fold_slice / zq_ix_mix_shuffle_slice / zq_ix_auth_mix_slice
  -> zq_ix_special_result_slice
  -> zq_ix_result_merge_slice
```

## 3. 物理分区

| 分区 | 包含 primitive | floorplan 位置 |
|---|---|---|
| fast lane | operand、addsub、carry、flag、compare | integer issue 与 redirect spine 附近 |
| shift lane | shift、mask merge | fast lane 邻接 |
| multiply lane | encode、compress、finish | fast lane 外侧，多级 pipeline |
| divide lane | prepare、step、special result | 整数簇边缘，多周期 |
| special lane | crc、shuffle、auth、special result | 整数簇边缘或 service side |
| result lane | result merge、writeback packet | writeback spine 前一级 |

## 4. RTL 命名落点

```text
rtl/foundation/iexecute/
  zhuque_ix_primitive_pkg.sv
  zhuque_ix_operand_slice.sv
  zhuque_ix_addsub_bit_slice.sv
  zhuque_ix_carry_group.sv
  zhuque_ix_flag_reduce.sv
  zhuque_ix_compare_slice.sv
  zhuque_ix_shift_stage.sv
  zhuque_ix_mask_merge_slice.sv
  zhuque_ix_mul_encode_slice.sv
  zhuque_ix_mul_compress_stage.sv
  zhuque_ix_mul_finish_slice.sv
  zhuque_ix_div_prepare_slice.sv
  zhuque_ix_div_step_slice.sv
  zhuque_ix_crc_fold_slice.sv
  zhuque_ix_mix_shuffle_slice.sv
  zhuque_ix_auth_mix_slice.sv
  zhuque_ix_special_result_slice.sv
  zhuque_ix_result_merge_slice.sv
  zhuque_ix_writeback_packet_slice.sv
```

## 5. 行为模型落点

```text
models/foundation/iexecute/
  primitives.py
  bit_slice.py
  shift.py
  multiply.py
  divide.py
  special.py
  result.py
```
