# 朱雀 Slice / Bank / Latch 映射

## 1. 目的

本文固定朱雀 full-core 数据通路的物理切分方式。

核心规则：

- bit slice 是最小纵向数据通路单元。
- uop slice 是前端、rename、dispatch、commit 的宽度单元。
- bank 是 SRAM/PRF/cache/queue 的容量和端口单元。
- latch boundary 是高频局部路径的时间边界。

## 2. Slice 层级

朱雀使用三层 slice。

| 层级 | 名称 | 粒度 | 用途 |
|---|---|---:|---|
| bit slice | `zq_bit_slice` | `1-bit` | 标量数据、地址、mask、flag |
| lane slice | `zq_lane_slice` | `64-bit` | 标量 lane、vector lane group、store data beat |
| uop slice | `zq_uop_slice` | `4 uop` | decode / rename / dispatch / retire |

`64-bit` 标量数据通路必须由 `64` 个 `zq_bit_slice` 组成。

```text
zq_lane_slice[63:0]
  = zq_bit_slice[63]
  + zq_bit_slice[62]
  + ...
  + zq_bit_slice[1]
  + zq_bit_slice[0]
```

## 3. 标量 bit slice

每个标量 bit slice 纵向包含：

```text
PRF read latch
  -> local bypass mux
  -> operand phase latch
  -> ALU bit cell
  -> result phase latch
  -> writeback driver
```

本地字段：

| 字段 | 说明 |
|---|---|
| `src0_bit` | 源 0 bit |
| `src1_bit` | 源 1 bit |
| `src2_bit` | 源 2 bit 或 store data bit |
| `imm_bit` | immediate bit |
| `carry_in` | 相邻或分组 carry |
| `carry_out` | 相邻或分组 carry |
| `cmp_bit` | compare 局部结果 |
| `mask_bit` | byte / predicate / write mask |
| `result_bit` | 本 bit 结果 |

跨 bit 网络只允许下列形式：

- `carry_group_4`
- `carry_group_8`
- `zero_reduce_tree`
- `sign_overflow_tree`
- `branch_condition_tree`
- `ecc_parity_tree`

这些网络必须分层布线，不能作为单点横向大网。

## 4. Uop Slice 映射

`16` 路主 uop 数据通路固定为 `4 x 4`。

| uop slice | slot | 主要邻接 |
|---|---|---|
| `zq_uop_slice0` | slot `0..3` | fetch sector low / rename bank group 0 |
| `zq_uop_slice1` | slot `4..7` | fetch sector middle / rename bank group 1 |
| `zq_uop_slice2` | slot `8..11` | fetch sector middle / rename bank group 2 |
| `zq_uop_slice3` | slot `12..15` | fetch sector high / rename bank group 3 |

每个 uop slice 内包含：

- local decode table
- immediate formatter
- uop pack register
- rename map read request
- free-list local allocate
- ROB write slice
- issue enqueue slice

跨 uop slice 只允许：

- commit age ordering
- branch checkpoint id
- free-list merge
- exception oldest select
- redirect payload

跨 uop slice 网络必须切拍或分层。

## 5. Fetch / Decode Slice

前端采用 `3 x 64B` fetch sector 和 `4 x 4` decode slice。

```text
fetch_sector0 64B ---+
fetch_sector1 64B -----> align / rotate -> decode_slice0..3
fetch_sector2 64B ---+
```

映射规则：

- fetch sector 面向 L1I bank。
- decode slice 面向 rename slice。
- align / rotate 是唯一允许跨 sector 的前端数据重排区。
- align / rotate 必须带 latch boundary，不做 `192B` 单拍大 mux。

## 6. PRF Bank 映射

### 6.1 Integer PRF

| 项 | 定义 |
|---|---:|
| logical entries | `640` |
| data width | `64-bit` |
| logical bank | `16` |
| entries / logical bank | `40` |
| minimum macro class | `1PRF 16Kbit` |
| physical rule | 小 bank、多实例、贴近 integer issue / execute |

integer PRF 每个 logical bank 输出一个 `64-bit` lane slice。跨 bank operand 需要局部 bypass / read mux，但不得形成全核集中读口。

### 6.2 FP PRF

| 项 | 定义 |
|---|---:|
| logical entries | `512` |
| data width | `64-bit` |
| logical bank | `16` |
| entries / logical bank | `32` |
| minimum macro class | `1PRF 16Kbit` |
| physical rule | 靠近 FP/vector 边界，避免穿越 integer 热区 |

### 6.3 Vector PRF

| 项 | 定义 |
|---|---:|
| logical entries | `768` |
| lane group | `64-bit` |
| logical bank | `24` |
| entries / logical bank | `32` |
| minimum macro class | `1PRF 16Kbit` |
| physical rule | 围绕 vector cluster 条带摆放 |

Vector PRF 的物理组织是 banked lane group，不是单体宽 VRF。

## 7. Issue Bank 映射

| issue domain | select / cycle | physical slice | local grant |
|---|---:|---:|---:|
| integer | `16` | `4` | `4` |
| memory | `12` | `4` | `3` average |
| vector | `12` | `3` | `4` |
| branch | included in integer | distributed | local fast |

issue queue payload array 与 ready bitset 分离：

```text
payload bank
  + valid bitset
  + ready bitset
  + local age pick
  -> grant packet
```

跨 issue slice 的 older-than 比较不能做全局单拍矩阵，必须先本地 pick，再少量全局 merge。

## 8. L1 / L2 / L3 Bank 映射

### 8.1 L1I

| 项 | 定义 |
|---|---:|
| capacity | `256KB` |
| fetch bandwidth | `192B/cycle` |
| logical bank | `16` |
| data leaf class | `L1CACHE 36Kbit` |
| initial data leaves | `64` |
| access rule | request / data-return 至少两级 |

### 8.2 L1D

| 项 | 定义 |
|---|---:|
| capacity | `256KB` |
| load AGU | `8` |
| store AGU | `6` |
| store data path | `6` |
| logical bank | `16` |
| data leaf class | `L1CACHE 36Kbit` 或 `HSSPSRAM 36Kbit` |
| initial data leaves | `64` |
| access rule | address/tag 与 data/return 分级 |

### 8.3 L2

| 项 | 定义 |
|---|---:|
| capacity | `16MB/tile` |
| bank | `64` |
| data leaf class | `UHDSPSRAM 156Kbit` |
| initial data leaves | `896` |
| leaves / bank | `14` |
| access rule | bank pipe 多周期返回 |

### 8.4 L3 Slice

| 项 | 定义 |
|---|---:|
| capacity | `32MB/tile` |
| bank group | `128` |
| data leaf class | `UHDSPSRAM 156Kbit` |
| initial data leaves | `1792` |
| leaves / bank group | `14` |
| access rule | 不进入 core 高频闭环 |

## 9. Latch Boundary 映射

朱雀数据通路区分 register boundary 和 phase latch boundary。

| boundary | 类型 | 位置 | 规则 |
|---|---|---|---|
| `FE_REQ_R` | register | next PC 到 L1I request | 跨 predictor / L1I bank |
| `FE_DATA_L` | phase latch | L1I data return 到 align | 局部前端 |
| `DE_PACK_R` | register | decode 到 uop pack | 进入 rename 前切拍 |
| `RN_ALLOC_R` | register | rename allocate 输出 | 跨 rename slice |
| `IS_GRANT_R` | register | issue grant 输出 | 跨 issue 到 operand |
| `OPRD_L0` | phase latch | PRF read 到 bypass | 局部 operand |
| `EXE_L1` | phase latch | bypass 到 ALU / lane | 局部 execute |
| `EXE_L2` | phase latch | ALU / compare 到 result | 局部 execute |
| `WB_R` | register | result merge 到 writeback | 跨 cluster |
| `CT_R` | register | ROB retire 输出 | 跨 commit fanout |
| `L1D_REQ_R` | register | AGU 到 DTLB / tag | 跨 LSU pipe |
| `L1D_DATA_L` | phase latch | L1D data 到 load return | 局部 L1D |
| `L2_REQ_R` | register | L1 miss 到 L2 | 跨 core / tile |
| `FAB_R` | register | fabric packet | 跨 tile / cluster |

## 10. 时间借用规则

局部 latch-based 路径允许时间借用，但必须满足：

| 项 | 初始约束 |
|---|---:|
| target period | `250ps` |
| local borrow cap | `35ps` |
| non-overlap guard | `15ps` |
| cross-cluster borrow | `0ps` |
| cross-bank borrow | `0ps` |
| cross-tile borrow | `0ps` |

允许借用的路径：

- PRF read latch 到 local bypass。
- bypass 到 fast ALU bit slice。
- ALU bit slice 到 local result latch。
- L1D bank 内 data leaf 到 load return latch。

不允许借用的路径：

- decode 到 rename 跨 slice 主干。
- issue 到远端 execute cluster。
- L1D 到 L2。
- L2 到 fabric。
- commit 到前端 redirect spine。

## 11. 布线层级映射

| 路径 | 推荐金属层 | 规则 |
|---|---|---|
| bit slice 内局部线 | `M1/M2/M4` | 短线、规则条带 |
| slice 邻接线 | `M5~M9` | 相邻 slice / cluster 内 |
| 跨 uop slice | `M10~M11` | 必须切拍或分层 |
| core 内长数据主干 | `M12~M13` | writeback / redirect spine |
| tile 主干 | `M14~M15` | L2 / fabric |
| 顶层接出 | `M16` | subsystem / package side |

低层金属不承载宽长单周期广播。
