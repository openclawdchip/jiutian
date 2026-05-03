# 朱雀 Full-Core 数据通路规格

## 1. 范围

本文定义朱雀 core 的完整数据通路。控制通路只在本文中保留接口位置，不展开状态机。

数据通路覆盖：

- 前端取指、预测结果携带、对齐、预译码、译码、uop 打包。
- rename、dispatch、issue、operand read、bypass、执行、结果合并、写回。
- load/store 地址、TLB、L1D、store data、load return、replay。
- ROB payload、retire payload、PRF reclaim payload、store commit payload。
- L1 miss、L2 bank、L3 slice、cluster fabric packet 的主数据面。

所有结构默认以 `4.0GHz` 为时序目标，以 N07 标准单元、SRAM/PRF 宏和互连账本为初始约束。

## 2. 顶层骨架

```text
zq_pc_redirect_spine
  -> zq_fetch_sector_array
  -> zq_fetch_align_slice
  -> zq_predecode_slice
  -> zq_decode_slice
  -> zq_uop_pack_slice
  -> zq_rename_slice
  -> zq_dispatch_lane
  -> zq_issue_slice
  -> zq_operand_read_slice
  -> zq_execute_cluster
  -> zq_result_merge_slice
  -> zq_writeback_slice
  -> zq_commit_slice
```

访存数据通路并行接入：

```text
zq_issue_slice
  -> zq_agu_slice
  -> zq_dtlb_slice
  -> zq_l1d_bank_pipe
  -> zq_load_return_slice
  -> zq_result_merge_slice
  -> zq_writeback_slice
```

存储层级数据通路并行接入：

```text
zq_l1_miss_slice
  -> zq_miss_tracker_bank
  -> zq_l2_bank_pipe
  -> zq_l3_slice_pipe
  -> zq_fabric_packet_lane
```

## 3. 全局数据粒度

| 数据对象 | 宽度 / 数量 | 物理组织 |
|---|---:|---|
| fetch byte window | `192B/cycle` | `3 x 64B` fetch sector |
| decode input | `16 inst/cycle` | `4 x 4` decode slice |
| uop main path | `16 uop/cycle` | `4 x 4` uop slice |
| scalar data | `64-bit` | `64` 个纵向 bit slice |
| scalar address | `64-bit` | `64` 个纵向 address slice |
| integer issue | `16/cycle` | `4` 个 integer issue slice，每 slice `4` slot |
| memory issue | `12/cycle` | `4` 个 memory issue slice，按 load/store 分流 |
| vector issue | `12/cycle` | `3` 个 vector issue group，每 group `4` slot |
| commit | `16/cycle` | `4 x 4` retire slice |
| L1I | `256KB/core` | 多 bank、多 leaf、小宏拼接 |
| L1D | `256KB/core` | 多 bank、多 leaf、load/store 分离端口抽象 |
| L2 | `16MB/tile` | `64` bank，bank 内多 leaf |
| L3 slice | `32MB/tile` | tile 级 slice bank group |

## 4. 数据通路事务

### 4.1 Fetch Packet

`zq_fetch_packet` 在前端数据通路中流动。

| 字段 | 说明 |
|---|---|
| `pc_base` | 本 fetch packet 的基地址 |
| `byte_data[192B]` | 三个 fetch sector 拼出的取指窗口 |
| `byte_valid[192]` | byte 粒度有效位 |
| `sector_id[3]` | `3 x 64B` sector 标记 |
| `pred_meta` | 快预测携带信息 |
| `fault_meta` | 取指侧 fault 占位 |
| `replay_hint` | 取指重放提示 |

### 4.2 Decode Slot

`zq_decode_slot` 是 `4 x 4` decode slice 的单 slot 输入。

| 字段 | 说明 |
|---|---|
| `pc` | 指令 PC |
| `inst_bits` | 对齐后的指令位 |
| `inst_len` | 指令长度 |
| `slice_id` | decode slice 编号 |
| `slot_id` | slice 内 slot 编号 |
| `pred_meta` | 预测信息透传 |
| `fault_meta` | 对齐、权限、页属性 fault 占位 |

### 4.3 Uop Packet

`zq_uop_packet` 是 decode 到 rename 的主数据对象。

| 字段 | 说明 |
|---|---|
| `valid` | slot 是否有效 |
| `uop_class` | integer / branch / memory / vector / system |
| `op_kind` | 局部执行类型 |
| `src_arch[3]` | 逻辑源寄存器 |
| `dst_arch` | 逻辑目标寄存器 |
| `imm` | immediate payload |
| `pc` | uop PC |
| `pred_meta` | 分支预测透传 |
| `fault_meta` | decode fault 占位 |
| `slice_id` | `4 x 4` uop slice 位置 |

### 4.4 Renamed Uop

`zq_renamed_uop` 是 rename 到 issue 的主数据对象。

| 字段 | 说明 |
|---|---|
| `src_phys[3]` | 物理源寄存器号 |
| `src_ready[3]` | 源操作数 ready 位 |
| `dst_phys` | 新物理目标寄存器号 |
| `old_dst_phys` | retire 后释放的物理寄存器号 |
| `rob_id` | ROB 位置 |
| `issue_domain` | integer / memory / vector / branch |
| `latency_class` | 预期执行延迟类别 |
| `checkpoint_id` | 恢复点占位 |

### 4.5 Issue Entry

`zq_issue_entry` 是 issue queue payload 和 wakeup/select 的数据载体。

| 字段 | 说明 |
|---|---|
| `age` | 局部年龄 |
| `src_phys[3]` | 源 tag |
| `src_ready[3]` | ready 位 |
| `dst_phys` | 目标 tag |
| `op_kind` | 执行操作 |
| `imm` | immediate |
| `rob_id` | 精确异常与 commit 追踪 |
| `mem_meta` | load/store 属性 |
| `vec_meta` | vector lane / mask 属性 |

### 4.6 Execute Request

`zq_execute_req` 是 issue 到执行簇的数据对象。

| 字段 | 说明 |
|---|---|
| `src_data[3]` | 已读取或旁路得到的源操作数 |
| `src_tag[3]` | 源 tag 观察字段 |
| `dst_phys` | 结果目标 |
| `op_kind` | 执行操作 |
| `imm` | immediate |
| `rob_id` | ROB 追踪 |
| `slice_id` | 数据 slice 位置 |
| `replay_class` | 可能触发的 replay 类别 |

### 4.7 Result Packet

`zq_result_packet` 是执行、访存、特殊单元到写回的数据对象。

| 字段 | 说明 |
|---|---|
| `valid` | 结果有效 |
| `dst_phys` | 目标物理寄存器 |
| `result_data` | 结果数据，标量默认 `64-bit` |
| `flags` | 条件码、比较、溢出、异常摘要 |
| `rob_id` | commit 对齐 |
| `bypass_class` | 本地旁路 / 跨簇旁路 / 写回后可见 |
| `fault_meta` | 异常占位 |
| `replay_token` | replay 占位 |

### 4.8 Memory Request / Response

`zq_mem_req` 和 `zq_mem_resp` 是 LSU 数据通路对象。

| 字段 | 说明 |
|---|---|
| `vaddr` | 虚拟地址 |
| `paddr` | 物理地址 |
| `size` | 访问宽度 |
| `load_store` | load / store 标记 |
| `store_data` | store 数据 payload |
| `byte_mask` | byte enable |
| `lq_id` | load queue 位置 |
| `sq_id` | store queue 位置 |
| `rob_id` | commit 对齐 |
| `bank_id` | L1D bank |
| `way_id` | 命中 way |
| `miss_token` | miss / replay 追踪 |

### 4.9 Commit Packet

`zq_commit_packet` 是 retire 数据通路对象。

| 字段 | 说明 |
|---|---|
| `retire_valid[16]` | `16` 路 retire valid |
| `rob_id[16]` | retire ROB id |
| `dst_phys[16]` | architectural state 更新目标 |
| `old_dst_phys[16]` | PRF reclaim 目标 |
| `store_commit[16]` | store commit 授权 |
| `fault_meta[16]` | precise fault payload |
| `redirect_meta` | redirect payload 占位 |

## 5. 前端数据通路

### 5.1 Fetch Sector

```text
next_pc
  -> L1I tag leaf
  -> L1I data leaf
  -> 3 x 64B fetch sector
  -> sector valid / fault merge
```

组织规则：

- `192B/cycle` 由 `3` 个 `64B` sector 组成。
- L1I data leaf 使用小 SRAM 宏拼接，不使用单体大数组。
- 快预测数据只携带到 packet，不在本阶段展开训练控制。
- tag、way、fault、valid 与 byte payload 并行流动。
- L1I access 至少 `2` 级流水：request / data-return。

### 5.2 Align And Predecode

```text
3 x 64B sector
  -> byte rotate / boundary detect
  -> 4 x predecode slice
  -> 4 x 4 decode slot
```

组织规则：

- fetch sector 到 decode slice 之间设置 align latch。
- byte rotate 不做单体 `192B` 大 mux，按 `4` 个 predecode slice 分摊。
- RVC 边界、非法长度、跨 sector 连接信息进入本地 metadata。

### 5.3 Decode And Uop Pack

```text
4 x 4 decode slot
  -> local decode table
  -> immediate slice
  -> uop pack slice
  -> rename input register
```

组织规则：

- 每个 decode slice 处理 `4` 个 slot。
- decode table 是本地组合逻辑或小 ROM leaf。
- 复杂系统类只生成慢路径标记，不压入主数据通路。
- uop pack 后形成 `16` 路定宽 uop packet。

## 6. Rename / Dispatch 数据通路

### 6.1 Rename Slice

```text
16 uop
  -> 4 x rename slice
  -> src map read
  -> free-list allocate
  -> checkpoint payload write
  -> renamed uop packet
```

组织规则：

- rename 采用 `4 x 4` slice。
- integer、FP、vector map 和 free-list 物理分域。
- free-list 先局部 pick，再做跨 slice merge。
- checkpoint payload 只写入恢复所需数据，不复制完整控制状态。

### 6.2 Dispatch Lane

```text
renamed uop
  -> domain split
  -> ROB payload write
  -> issue payload write
  -> operand readiness seed
```

组织规则：

- dispatch 不经过一个全局大 crossbar。
- `uop_class` 在 rename 后转换为物理 issue domain。
- ROB payload 与 issue payload 分开写，payload 只在需要的物理方向移动。
- dispatch 到 issue 的跨区路径默认寄存。

## 7. Issue / Operand 数据通路

### 7.1 Issue Slices

```text
issue payload array
  -> ready bit slice
  -> local oldest-ready pick
  -> domain grant packet
```

组织规则：

- integer issue：`4` 个 slice，每 slice `4` grant，总计 `16/cycle`。
- memory issue：`4` 个 slice，总计 `12/cycle`，保留 load/store 方向位。
- vector issue：`3` 个 group，每 group `4` grant，总计 `12/cycle`。
- wakeup tag 先本地匹配，跨簇匹配必须切拍。
- issue payload array 与 ready bitset 分离。

### 7.2 Operand Read

```text
grant packet
  -> PRF bank read
  -> local bypass select
  -> operand latch
  -> execute req
```

组织规则：

- integer PRF、FP PRF、Vector PRF 分开 bank。
- PRF read 是独立 pipeline stage，不和大规模 bypass mux 合并成单拍。
- bypass 分为本地旁路、邻近簇旁路、写回后可见三类。
- `64-bit` 标量 operand 在物理上是 `64` 个 bit slice。

## 8. Integer Execute 数据通路

### 8.1 Fast Integer Lane

```text
operand latch
  -> add/sub bit slice
  -> shift / bitfield slice
  -> compare slice
  -> local result latch
```

组织规则：

- simple ALU、shift、compare 靠近 integer issue 和 branch redirect spine。
- `64-bit` ALU 是 `64` 个纵向 bit slice。
- carry、zero、sign、overflow 是分层跨 slice 网络。
- fast lane 预留 latch-based 时间借用，不把长短路径强行对齐到同一组合云。

### 8.2 Multiply / Divide / Special

```text
operand latch
  -> partial product / special transform
  -> reduction / iterative step
  -> result normalize
  -> local result latch
```

组织规则：

- multiply 采用多级 partial-product 和 reduction pipeline。
- divide / special 采用多周期数据通路，不进入单周期 fast lane。
- special 结果走边缘回写入口，不污染 fast result merge。

## 9. Vector Execute 数据通路

```text
vector issue group
  -> VRF bank read
  -> lane-group operand latch
  -> vector integer / permute / MAC / FP cluster
  -> vector local merge
  -> VRF writeback
```

组织规则：

- vector 围绕 VRF bank 摆放。
- mask/predicate 与 lane data 并行流动。
- permute 靠近 VRF，跨 lane 数据交换必须 bank-aware。
- MAC / FP 走多级 pipeline，结果先簇内合并再进入 VRF writeback。

## 10. LoadStore / MMU 数据通路

### 10.1 AGU / DTLB / L1D

```text
memory issue grant
  -> AGU slice
  -> DTLB slice
  -> L1D tag bank
  -> L1D data bank
  -> load return slice
```

组织规则：

- load AGU：`8` 条，按 L1D bank group 分布。
- store AGU：`6` 条，store address 与 store data 分离。
- DTLB 与 L1D tag 物理相邻。
- L1D access 至少 `2` 级流水：address/tag 和 data/return。
- bank conflict 生成 replay token，不在数据通路里集中阻塞全核。

### 10.2 Store Data

```text
store issue grant
  -> store data PRF/bypass read
  -> store data queue slice
  -> byte mask merge
  -> L1D store data port
```

组织规则：

- store address 和 store data 解耦。
- store data path 为 `6/cycle`，按 bank group 分摊。
- store commit token 从 commit slice 进入 store queue，不跨越 fast load hit path。

### 10.3 Miss / Fill / Replay

```text
L1 miss
  -> miss tracker bank
  -> L2 request packet
  -> fill return packet
  -> L1 fill slice
  -> replay token
```

组织规则：

- miss tracker 是 banked payload + valid bitset。
- replay token 是常规数据对象，不作为异常旁路。
- fill data 返回先进入 L1 fill slice，再驱动 load replay。

## 11. Writeback 数据通路

```text
integer result
vector result
load result
special result
  -> local result merge
  -> writeback slice
  -> PRF bank write
  -> wakeup tag broadcast
```

组织规则：

- result merge 先局部合并，再进入写回主干。
- writeback 不做单点全输入大 mux。
- wakeup tag 与 result data 分离，tag 可以更早发送，data 保持局部化。
- 跨 cluster writeback 默认切拍。

## 12. Commit / Retire 数据通路

```text
ROB state / payload
  -> 4 x retire slice
  -> precise fault payload
  -> PRF reclaim payload
  -> store commit payload
  -> redirect payload
```

组织规则：

- `1024` entry ROB 按 segment / bank 组织。
- `16/cycle` commit 拆成 `4 x 4` retire slice。
- ROB state 与 payload 分离；hot retire valid 不拖动大 payload。
- reclaim payload 朝 rename 方向返回。
- store commit payload 朝 LSU 方向返回。
- redirect payload 朝前端 spine 返回。

## 13. L2 / L3 / Fabric 数据通路

```text
core L1 miss
  -> tile L2 request lane
  -> L2 bank select
  -> L2 tag/data pipe
  -> L3 slice / fabric packet
  -> response return lane
```

组织规则：

- L2 是 `64` bank 分布式结构。
- L2 bank access 使用密集 SRAM 宏，多周期返回。
- fabric packet lane 与 debug/service sideband 分离。
- 跨 tile 数据使用 packetized lane，不使用裸宽总线。

## 14. 最小控制接口位置

数据通路阶段只保留下面控制接口，不展开控制 FSM：

| 接口 | 所在位置 | 作用 |
|---|---|---|
| `valid` / `ready` | 每级 pipeline 边界 | 基本 backpressure |
| `stall_hint` | fetch / decode / issue / LSU | 局部暂停 |
| `kill_mask` | fetch 到 commit 关键边界 | 清除无效 payload |
| `replay_token` | issue / LSU / writeback | 重发事务 |
| `fault_meta` | fetch / decode / LSU / execute / commit | 精确异常 payload |
| `credit` | L2 / fabric | 跨边界流控 |

控制通路必须在这些接口上覆盖，不能新增绕过数据通路的隐式全局控制网。

## 15. 行为模型落点

| 数据通路段 | 行为模型对象 |
|---|---|
| fetch sector | `ZqFetchPacket`、`ZqFetchSectorPipe` |
| decode slice | `ZqDecodeSlot`、`ZqDecodeSlicePipe` |
| uop pack | `ZqUopPacket`、`ZqUopSlice` |
| rename slice | `ZqRenameSlice`、`ZqFreeListBank` |
| issue slice | `ZqIssueEntry`、`ZqIssueBank` |
| operand read | `ZqPrfBank`、`ZqBypassSlice` |
| integer execute | `ZqScalarBitSlice`、`ZqIntegerCluster` |
| vector execute | `ZqVectorLaneGroup`、`ZqVrfBank` |
| LSU | `ZqAguSlice`、`ZqL1dBankPipe` |
| writeback | `ZqResultMergeSlice`、`ZqWritebackLane` |
| commit | `ZqRobSegment`、`ZqRetireSlice` |
| L2 / fabric | `ZqL2BankPipe`、`ZqFabricPacketLane` |

## 16. RTL 落点

RTL 第一版按下面目录生成：

```text
rtl/core/datapath/
  zhuque_core_datapath_pkg.sv
  zhuque_fetch_datapath.sv
  zhuque_decode_datapath.sv
  zhuque_rename_datapath.sv
  zhuque_issue_datapath.sv
  zhuque_integer_datapath.sv
  zhuque_vector_datapath.sv
  zhuque_loadstore_datapath.sv
  zhuque_writeback_datapath.sv
  zhuque_commit_datapath.sv
  zhuque_l2_datapath.sv
```

每个 RTL 数据通路模块先实现 payload、slice、bank、register/latch boundary 和 minimal ready/valid，控制 FSM 后续覆盖。
