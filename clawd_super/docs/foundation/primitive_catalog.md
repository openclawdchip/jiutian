# 朱雀 Primitive 清单

## 1. Primitive 分类

朱雀底层 primitive 分为四类：

- physical primitive
- storage primitive
- flow primitive
- compute primitive

每个 primitive 都要求有文档、行为模型和 RTL 三种形态。

## 2. Physical Primitive

| Primitive | 职责 | 行为模型要求 | RTL 要求 |
|---|---|---|---|
| `zq_reg_slice` | pipeline register、valid metadata、kill 支持 | 周期推进、stall、flush、reset | 参数化宽度、reset policy、enable、flush |
| `zq_state_bitset` | valid/free/busy 位图 | set/clear/test/priority | banked bitset、局部 priority |
| `zq_reset_sync` | reset 同步和释放 | reset stretch、domain release | 2FF sync、可配置释放延迟 |
| `zq_cdc_toggle` | 单 bit 跨域事件 | toggle event、ack | 双向 toggle sync |
| `zq_cdc_credit` | credit 跨域 | credit send/return | gray counter 或 token sync |
| `zq_local_clock_gate` | 局部时钟门控抽象 | enable 语义 | RTL 先占位，后端替换 ICG |

## 3. Storage Primitive

| Primitive | 职责 | N07 绑定 | 使用域 |
|---|---|---|---|
| `zq_sram_bank_1r1w` | 单读单写 SRAM bank | `L1CACHE` / `HSSPSRAM` / `UHDSPSRAM` | predictor、queue、cache |
| `zq_sram_bank_ro` | 只读表 bank | `L1CACHE` 小叶子 | decode table、predictor |
| `zq_prf_bank_1r1w` | 小型 PRF bank | `1PRF 16Kbit` 起步 | integer/FP/vector PRF |
| `zq_tag_array` | tag + valid + way hit | SRAM + compare 或 DFF | cache/TLB/predictor |
| `zq_payload_array` | queue payload storage | DFF/SRAM hybrid | issue、ROB、LSQ |
| `zq_valid_bitmap` | valid/free/busy 状态 | DFF bitset | queue、ROB、bank state |
| `zq_checkpoint_store` | rename/branch checkpoint | SRAM/DFF hybrid | rename、commit |

## 4. Flow Primitive

| Primitive | 职责 | 行为模型要求 | RTL 要求 |
|---|---|---|---|
| `zq_ready_valid_pipe` | ready/valid 流水 | backpressure、bubble、kill | skid 可选、flush priority |
| `zq_credit_pipe` | credit 流控 | credit consume/return | overflow/underflow assert |
| `zq_fifo_small` | 小 FIFO | enq/deq/head/tail/full/empty | DFF 实现 |
| `zq_fifo_banked` | banked FIFO | bank conflict、ordered pop | SRAM payload + bitset |
| `zq_priority_pick` | masked priority select | first/last/priority | 参数化宽度 |
| `zq_rr_pick` | round-robin select | fairness、mask、grant state | rotating pointer |
| `zq_age_pick` | oldest-ready select | age compare、ready mask | 分层 age select |
| `zq_replay_token` | replay 信息 | cause、target、age、domain | compact token format |
| `zq_flush_tree` | flush/kill 分发 | priority、mask、domain fanout | 分层广播、寄存切拍 |
| `zq_packet_adapter` | req/resp 包化 | channel map、sideband | payload pack/unpack |

## 5. Compute Primitive

| Primitive | 职责 | 行为模型要求 | RTL 要求 |
|---|---|---|---|
| `zq_addsub_lane` | add/sub/flags | carry、overflow、zero、sign | 低延迟 lane |
| `zq_shift_lane` | shift/rotate/bitfield | left/right/rotate/extract | 分层 barrel |
| `zq_compare_lane` | compare/branch assist | signed/unsigned/condition | 靠近 branch spine |
| `zq_mul_pp_lane` | partial product | operand signedness、window | 分级 pipeline |
| `zq_mul_reduce_lane` | multiply reduction | carry-save、final sum | 多级 reduction |
| `zq_div_step_lane` | divide step | qbit、remainder、done | 多周期 FSM |
| `zq_crc_lane` | CRC update | polynomial、width、seed | XOR network |
| `zq_auth_lane` | pointer/auth transform | key select、mix、result | 稀有路径隔离 |
| `zq_mask_lane` | vector mask/predicate | lane active、predicate merge | vector lane local |
| `zq_perm_lane` | vector permute | lane select、shuffle | bank-aware permute |

## 5.1 IExecute Datapath Primitive

朱雀整数执行数据通路进一步拆成可直接建模和 RTL 化的基础构件。

| Primitive | 职责 | N07 绑定重点 | 使用域 |
|---|---|---|---|
| `zq_ix_operand_slice` | operand read / bypass / latch | local mux + phase latch | integer execute |
| `zq_ix_addsub_bit_slice` | 1-bit add/sub/logic | FA/XOR/MUX，`64` bit slice | fast integer |
| `zq_ix_carry_group` | 分组 carry | group4/group8/group16，局部线 | fast integer |
| `zq_ix_flag_reduce` | zero/sign/carry/overflow/saturate | 分层 reduce tree | fast integer / compare |
| `zq_ix_compare_slice` | equality、signed/unsigned compare、branch condition | compare bit + reduce tree | branch assist |
| `zq_ix_shift_stage` | shift/rotate/bitfield | 分级 barrel，不做大 mux | shift lane |
| `zq_ix_mask_merge_slice` | byte/predicate/conditional merge | per-bit local mux | shift / special |
| `zq_ix_mul_encode_slice` | multiplier window / partial product seed | pipeline before compress | multiply |
| `zq_ix_mul_compress_stage` | 4:2/6:2/8:2/9:2 compression | 多级 compressor band | multiply |
| `zq_ix_mul_finish_slice` | final add / normalize | addsub + carry group | multiply |
| `zq_ix_div_prepare_slice` | sign/abs/clz/pow2 detect | reduce tree + register | divide |
| `zq_ix_div_step_slice` | qbit/remainder/quotient update | iterative compare + addsub | divide |
| `zq_ix_crc_fold_slice` | CRC polynomial fold | XOR tree，byte split | special |
| `zq_ix_mix_shuffle_slice` | nibble/byte/word shuffle | structured shuffle，非 crossbar | special |
| `zq_ix_auth_mix_slice` | pointer/auth transform mix | side-lane multi-stage | special |
| `zq_ix_special_result_slice` | slow result normalize | register before merge | special |
| `zq_ix_result_merge_slice` | fast/slow result merge | staged mux，`IX_WB_R` | writeback |
| `zq_ix_writeback_packet_slice` | result packet register | DFF area per bit，M12+ spine | writeback |

## 6. 行为模型落点

行为模型目录建议：

```text
models/
  foundation/
    physical/
    storage/
    flow/
    compute/
```

每个 primitive 行为模型至少包含：

- 参数对象
- 输入事务
- 输出事务
- 状态对象
- step 函数
- directed tests
- 统计事件

## 7. RTL 落点

RTL 目录建议：

```text
rtl/
  foundation/
    physical/
    storage/
    flow/
    compute/
```

每个 primitive RTL 至少包含：

- package/type
- module
- assertions
- filelist
- basic testbench

## 8. 上层使用规则

设计域只能组合 primitive，不重复定义底层结构。

当上层需要新增底层能力时，先扩展 `foundation`，再回到上层模块。
