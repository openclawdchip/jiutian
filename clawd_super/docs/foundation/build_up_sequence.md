# 从底层部件往上搭建朱雀

## 1. 总体顺序

朱雀按下面顺序搭建：

```text
N07 PPA 账本
  -> foundation primitive
  -> shared contracts
  -> full-core data path skeleton
  -> control path overlay
  -> domain L2/L3 modules
  -> behavior models
  -> RTL
  -> synthesis / APR feedback
```

底层部件先闭合，再用这些部件搭完整 core 数据通路，最后把控制通路叠加上去。

数据通路优先级高于控制通路优先级。设计推进时先让数据从入口到出口可被建模、可被计时、可被摆放，再给这条数据通路添加控制状态机。

每一级推进都必须同时更新：

- floorplan 位置
- area 估算
- logic delay 估算
- SRAM / PRF access delay 估算
- wire delay 估算
- `4.0GHz` slack

## 2. 第一步：建立 foundation primitive

优先顺序：

1. `zq_reg_slice`
2. `zq_ready_valid_pipe`
3. `zq_priority_pick`
4. `zq_rr_pick`
5. `zq_fifo_small`
6. `zq_valid_bitmap`
7. `zq_sram_bank_1r1w`
8. `zq_prf_bank_1r1w`
9. `zq_tag_array`
10. `zq_age_pick`
11. `zq_replay_token`
12. `zq_flush_tree`
13. `zq_addsub_lane`
14. `zq_shift_lane`
15. `zq_compare_lane`
16. `zq_mul_pp_lane`
17. `zq_mul_reduce_lane`
18. `zq_div_step_lane`
19. `zq_packet_adapter`
20. `zq_cdc_credit`

这些 primitive 覆盖大部分主干域的底层共性。

## 3. 第二步：建立 shared contracts

shared contracts 包括：

- transaction header
- kill / flush / replay token
- exception / fault metadata
- ready/valid channel contract
- bank access contract
- SRAM request/response contract
- PRF access contract
- packet request/response contract
- event/counter contract

这些 contract 先在 `foundation` 行为模型中跑通，再进入各域。

## 4. 第三步：搭建 full-core 数据通路骨架

full-core 数据通路骨架一次性覆盖下面链路：

```text
fetch banks
  -> predecode slices
  -> decode slices
  -> uop pack slices
  -> rename slices
  -> dispatch lanes
  -> issue slices
  -> execute clusters
  -> result merge slices
  -> writeback slices
  -> commit / retire slices
```

访存数据通路并行接入：

```text
issue slices
  -> AGU slices
  -> DTLB / L1D bank pipes
  -> load return slices
  -> writeback slices
```

cache / fabric 数据通路并行接入：

```text
L1 miss path
  -> miss tracker
  -> L2 bank pipe
  -> fabric packet adapter
```

这个阶段不追求完整控制策略，只要求每条数据通路回答：

- payload bit slice 如何纵向穿过模块
- 哪些数组使用 SRAM / PRF 宏
- 哪些路径使用 DFF，哪些路径预留 latch 相位
- 每段 pipeline 的目标位置和线长
- 每段路径的时延与面积账本

## 5. 第四步：添加控制通路覆盖层

控制通路覆盖在数据通路骨架之上，按下面顺序加入：

1. local ready / valid
2. bank conflict control
3. replay token
4. flush / kill tree
5. exception / fault merge
6. branch redirect
7. resource allocation / reclaim
8. low power / debug / event observe

控制通路必须遵守数据通路的 slice、bank、cluster 边界。跨边界控制信号默认切拍，不能用单点大广播破坏已确定的 floorplan。

## 6. Slice-based 数据通路规则

宽数据通路按 bit slice 组织。`64-bit` 数据通路默认是 `64` 个纵向 slice，`128-bit` 数据通路默认是 `128` 个纵向 slice，vector lane 在 bit slice 之上再做 lane group。

每个 slice 内放置：

- local payload register 或 latch
- local mux / bypass
- local ALU bit
- local mask / predicate bit
- local writeback bit
- local observe bit

跨 slice 逻辑只允许以分层方式存在：

- carry chain
- zero / sign / overflow reduction
- branch condition reduction
- vector lane reduction
- ECC / parity reduction

跨 slice 逻辑必须有单独 PPA 估算，不能隐藏在宽数据通路描述里。

## 7. Latch-based 时序规则

高频数据通路默认预留 latch-based 实现能力。

文档和模型中必须区分：

- edge pipeline boundary
- phase latch boundary
- time-borrow window
- local non-overlap guard
- cross-cluster registered boundary

时间借用只用于局部 slice 或 cluster 内部的路径平衡。跨 bank、跨 cluster、跨 core 的路径必须显式寄存或多周期化。

## 8. 第五步：搭建前端

前端由 foundation primitive 组成：

| 前端结构 | Foundation 依赖 |
|---|---|
| fast predictor | `zq_sram_bank_ro`、`zq_tag_array`、`zq_priority_pick` |
| PC redirect pipe | `zq_ready_valid_pipe`、`zq_flush_tree` |
| fetch queue | `zq_fifo_banked`、`zq_valid_bitmap` |
| predecode | `zq_decode_table_slice`、`zq_uop_pack_slice` |
| decode slice | `zq_decode_table_slice`、`zq_ready_valid_pipe` |

前端要先保证 fetch slice 和 decode slice 能局部闭合。

## 9. 第六步：搭建 rename / issue

| 结构 | Foundation 依赖 |
|---|---|
| map table | `zq_sram_bank_1r1w` 或 `zq_valid_bitmap` |
| free list | `zq_priority_pick`、`zq_valid_bitmap` |
| checkpoint | `zq_checkpoint_store` |
| issue queue | `zq_payload_array`、`zq_valid_bitmap` |
| wakeup | `zq_cam_match_slice`、`zq_ready_valid_pipe` |
| select | `zq_age_pick`、`zq_rr_pick` |

rename 和 issue 必须按 slice / cluster 搭建，不构造一个集中大结构。

## 10. 第七步：搭建执行簇

| 执行簇 | Foundation 依赖 |
|---|---|
| integer fast lane | `zq_addsub_lane`、`zq_shift_lane`、`zq_compare_lane` |
| integer multiply | `zq_mul_pp_lane`、`zq_mul_reduce_lane` |
| integer divide | `zq_div_step_lane` |
| vector mask | `zq_mask_lane` |
| vector permute | `zq_perm_lane` |
| result merge | `zq_priority_pick`、`zq_ready_valid_pipe` |

执行簇的结果不先汇到一个全局大 mux，而是先本地合并，再进入 writeback spine。

## 11. 第八步：搭建 loadstore / cache

| 结构 | Foundation 依赖 |
|---|---|
| AGU pipe | `zq_addsub_lane`、`zq_ready_valid_pipe` |
| DTLB lookup | `zq_tag_array`、`zq_sram_bank_ro` |
| load queue | `zq_fifo_banked`、`zq_cam_match_slice` |
| store queue | `zq_fifo_banked`、`zq_payload_array` |
| L1D bank | `zq_sram_bank_1r1w`、`zq_tag_array` |
| miss tracker | `zq_valid_bitmap`、`zq_packet_adapter` |

L1 结构使用小叶子、多 bank、短本地线。L2/L3 使用密集宏并接受多周期。

## 12. 第九步：搭建 commit / recovery

| 结构 | Foundation 依赖 |
|---|---|
| ROB state | `zq_payload_array`、`zq_valid_bitmap` |
| retire select | `zq_priority_pick`、`zq_age_pick` |
| reclaim pipe | `zq_ready_valid_pipe` |
| flush/recover | `zq_flush_tree`、`zq_replay_token` |
| event/debug | `zq_event_counter_cell` |

commit 是前端 redirect、rename reclaim、store commit 和 exception 的汇合点，必须按状态、选择、广播三类分开搭建。

## 13. 第十步：搭建 cluster fabric

| 结构 | Foundation 依赖 |
|---|---|
| request ingress | `zq_packet_adapter`、`zq_ready_valid_pipe` |
| credit flow | `zq_credit_pipe`、`zq_cdc_credit` |
| route select | `zq_rr_pick`、`zq_priority_pick` |
| response egress | `zq_packet_adapter`、`zq_fifo_small` |

跨 tile 和跨全局边界默认切拍。

## 14. 反馈闭环

每搭完一个层级，都要更新：

- primitive 参数
- 行为模型 latency
- RTL pipeline stage
- floorplan 约束
- PPA 估算表

后续综合或 APR 报告出来后，优先回写 `foundation`，再修正上层模块。
