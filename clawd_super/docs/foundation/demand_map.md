# 底层需求地图

## 1. 目的

本文定义朱雀底层部件层需要覆盖的功能需求。

这些需求用于决定 foundation primitive 的类别、粒度、PPA 预算和上层组合边界。

## 2. 扫描范围

当前底层需求覆盖前端、译码、重命名、执行、访存、提交、L2、cluster、debug、interrupt、shared 和 fabric。

大体量需求集中在 instruction decode、frontend、loadstore、vector execute、rename、commit、transport 和 level2 方向。

## 3. 总体需求强度

按关键词族粗粒度扫描，需求强度如下：

| 需求族 | 命中量级 | 设计含义 |
|---|---:|---|
| state / register / reset | `161122` | 状态寄存、流水寄存、控制寄存和 reset 策略必须先统一 |
| clock / reset / sync / bridge | `44032` | CDC、reset domain 和时钟边界是底层一等公民 |
| decode / opcode / instruction | `21722` | 译码表、字段抽取和 uop 打包需要专用 primitive |
| integer arithmetic | `11635` | ALU、shift、mul、div、compare、CRC、auth 类 primitive 必须完备 |
| cache / TLB / miss / way | `1528` | cache/TLB bank、tag 和 miss tracker 是基础存储部件 |
| fabric protocol | `1151` | packet、req/resp、credit 和协议桥要独立成底层流控部件 |
| load / store / AGU / forward | `1143` | LSU 需要地址、队列、转发、hazard 检查 primitive |
| SRAM / RAM / array / bank | `1049` | SRAM/PRF wrapper 和 bank 调度必须先定义 |
| queue / entry / head / tail | `457` | queue/fifo/entry storage 是跨域通用部件 |
| vector / lane / mask | `476` | vector lane 和 mask primitive 要与标量 primitive 并列 |
| ready / valid / stall / credit | `252` | 流控要统一，不能每域各写一套 |
| trace / debug / counter | `252` | observability 必须作为底层 sideband 设计 |
| rename / free / checkpoint / PRF | `251` | map、free-list、checkpoint、PRF bank 进入 foundation |
| commit / retire / flush / replay | `240` | flush/replay/recover 优先级需要底层统一语义 |
| CAM / match / tag / lookup | `139` | tag match、hazard match、age match 需要统一比较部件 |
| issue / wakeup / scoreboard | `56` | wakeup/select 必须结合 floorplan 做分布式 primitive |
| arbitration / select | `39` | 仲裁数量不按关键词直接反映复杂度，但需要统一 round-robin、priority 和 age select |

## 4. 底层部件族

朱雀从底层需求中抽象出以下部件族：

| 部件族 | 作用 |
|---|---|
| register_slice | pipeline register、valid bit、metadata register、flushable state |
| reset_sync_cell | reset 同步、reset stretch、domain-local reset release |
| cdc_bridge_cell | async/sync bridge、toggle sync、credit sync |
| ready_valid_channel | ready/valid 载荷、skid、bubble、kill |
| credit_channel | credit counter、return credit、overflow guard |
| local_fifo | small FIFO、ring pointer、head/tail、empty/full |
| banked_array_wrapper | SRAM/PRF bank 封装、读写仲裁、bank conflict |
| tag_match_array | tag compare、valid mask、way select、hit vector |
| cam_match_slice | CAM-like match、hazard match、dependency match |
| priority_select | fixed priority、oldest ready、masked select |
| round_robin_select | rotating grant、fairness guard、credit-aware select |
| age_matrix_select | issue/commit 类 age select |
| decode_table_slice | opcode classify、field extract、immediate form |
| uop_pack_slice | uop metadata pack、trap metadata pack、slice merge |
| addsub_cell | add/sub、carry、flag |
| shift_cell | shift、rotate、bitfield |
| compare_cell | compare、branch assist、condition flag |
| multiply_cell | partial product、reduction、MAC |
| divide_step_cell | iterative divide、qbit、remainder update |
| crc_auth_cell | CRC、pointer auth、special transform |
| mask_perm_cell | vector mask、predicate、permute |
| replay_token_cell | replay cause、replay target、reissue age |
| flush_tree_cell | kill mask、flush priority、domain fanout |
| event_counter_cell | perf/event counter、trace event、debug capture |
| packet_adapter_cell | req/resp packetize、flit field、sideband pack |

## 5. 对上层的使用规则

上层模块不能重新发明这些部件。

示例：

- IFetch 的 fetch queue 使用 `local_fifo` 和 `ready_valid_channel`
- Decode 的译码 slice 使用 `decode_table_slice` 和 `uop_pack_slice`
- Rename 的 free-list 使用 `banked_array_wrapper`、`priority_select` 和 `replay_token_cell`
- Issue 的 wakeup/select 使用 `cam_match_slice`、`age_matrix_select` 和 `ready_valid_channel`
- Integer execute 使用 `addsub_cell`、`shift_cell`、`multiply_cell` 和 `divide_step_cell`
- LoadStore 使用 `tag_match_array`、`cam_match_slice`、`banked_array_wrapper` 和 `replay_token_cell`
- Commit 使用 `flush_tree_cell`、`event_counter_cell` 和 `priority_select`
- Cluster fabric 使用 `packet_adapter_cell`、`credit_channel` 和 `cdc_bridge_cell`

## 6. 文档推进要求

后续 L2/L3 文档要从本页选择底层部件。

每个模块必须说明：

- 采用哪些 primitive
- 关键状态放在哪里
- 数据路径经过哪些 primitive
- 控制路径由哪些 primitive 组合
- 使用何种 N07 宏或标准单元预算
- 是否需要跨 bank、跨 slice、跨 cluster 或跨 tile
