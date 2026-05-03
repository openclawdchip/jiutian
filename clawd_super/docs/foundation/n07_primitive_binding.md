# N07 Primitive 绑定

## 1. 目的

本文定义 N07 底层 PPA 证据如何绑定到朱雀 foundation primitive。

绑定目标：

- 标准单元用于小逻辑、控制、寄存、选择和短组合路径。
- SRAM/PRF 宏单元用于大容量数组、cache、PRF、predictor、队列 payload。
- 互连金属层用于约束局部线、跨簇线、跨 core 线和跨 tile 线。

## 2. 标准单元绑定

当前标准单元锚点来自：

- `C:\chipwiki\wiki\synthesis\n07-logic-and-interconnect-ppa-envelope-v1.md`

| Primitive | 标准单元锚点 | 初始时序规则 |
|---|---|---|
| register_slice | `DFQD1` | 每级至少计入 `CP->Q ~= 25.870ps` 和 setup/margin |
| reset_sync_cell | `DFF + small gates` | reset release 不进入热路径 |
| ready_valid_channel | `DFF + NAND/INV/MUX` | 组合 ready 链不能跨多个物理区 |
| priority_select | `NAND2/INV/MUX` | 超过局部 slice 必须分层选择 |
| round_robin_select | `DFF + priority_select` | grant state 本地寄存 |
| age_matrix_select | `DFF + compare + priority_select` | 不做全局单周期大矩阵 |
| decode_table_slice | `NAND/INV/MUX` | 每 slice 本地译码，复杂分类后移 |
| uop_pack_slice | `DFF + MUX` | pack 后进入 register_slice |
| addsub_cell | `FA/NAND/INV/DFF` | 低延迟路径分段并贴近 issue |
| shift_cell | `MUX/NAND/INV` | 大 barrel shift 需要分层 |
| compare_cell | `XOR/NAND/INV` | branch assist 靠近 redirect spine |
| multiply_cell | `AND/FA/DFF` | 多级 partial product 和 reduction |
| divide_step_cell | `DFF + addsub + compare` | 默认多周期 |
| crc_auth_cell | `XOR/MUX/DFF` | 稀有路径允许边缘布置 |
| mask_perm_cell | `MUX/AND/OR/DFF` | vector lane 本地化 |
| flush_tree_cell | `DFF + buffer tree + gates` | 分层 fanout，不能单点广播 |
| event_counter_cell | `DFF + adder` | 不进入热路径 |

基础锚点：

| 项 | 数值 |
|---|---:|
| `INV D1` area | `0.04104 um^2` |
| `NAND2 D1` area | `0.05472 um^2` |
| `DFF D1` area | `0.2736 um^2` |
| `INV D1 FO4` | `7.252ps` |
| `DFF CP->Q` | `25.870ps` |

早期路径估算：

```text
path_ps =
  25.870
  + logic_depth_fo4 * 7.252
  + mux_penalty_ps
  + wire_delay_ps
  + setup_margin_ps
```

## 3. SRAM / PRF 宏绑定

当前 memory 锚点来自：

- `C:\chipwiki\wiki\synthesis\n07-sram-ppa-envelope-v1.md`

| Primitive | 推荐宏方向 | 使用规则 |
|---|---|---|
| banked_array_wrapper | `L1CACHE 36Kbit` / `HSSPSRAM 36Kbit` / `UHDSPSRAM` | 根据频率和容量选宏 |
| tag_match_array | 小容量可用标准单元，大容量用 SRAM + compare | tag compare 靠近 bank |
| local_fifo | 小 FIFO 用 DFF，大 payload 用 SRAM | 控制位和 payload 可分开 |
| PRF bank | `1PRF 16Kbit` 起步 | `4GHz` 下不做大单体 PRF |
| L1I/L1D bank | `L1CACHE 36Kbit` 起步 | 小叶子、多 bank、短线 |
| L2 bank | `UHDSPSRAM 156Kbit` 起步 | 多周期、强 bank、靠近 tile spine |
| L3 slice bank | `UHDSPSRAM 156Kbit` 起步 | 大容量、多周期、远离 core 热路径 |
| predictor table | `L1CACHE` 或小 SRAM leaf | fast path 小表，large table 慢路径 |
| queue payload array | small DFF / SRAM hybrid | ready/valid 和 payload 分离 |

关键锚点：

| 宏 | 容量 | Area | Cycle | 适用 |
|---|---:|---:|---:|---|
| `L1CACHE` | `36 Kbit` | `2429.431 um^2` | `0.245ns` | `4GHz` 级 L1 小叶子 |
| `HSSPSRAM` | `36 Kbit` | `2774.188 um^2` | `0.238ns` | `4GHz` 级高速小数组 |
| `1PRF` | `16 Kbit` | `1417.590 um^2` | `0.249ns` | 小型 PRF bank |
| `UHDSPSRAM` | `156 Kbit` | `7595.191 um^2` | `0.562ns` | L2/L3 密集数组 |

## 4. 互连层绑定

当前互连锚点来自：

- `C:\chipwiki\wiki\synthesis\n07-logic-and-interconnect-ppa-envelope-v1.md`

金属层角色：

| 金属层 | 角色 |
|---|---|
| `M1/M2/M4` | 本地标准单元、短局部线 |
| `M5~M9` | 中短距离局部数据和控制 |
| `M10~M11` | 中距离跨 slice / 跨 bank |
| `M12~M13` | core 内较长数据通路和主干 |
| `M14~M15` | core/tile 主干、时钟和宽总线优先层 |
| `M16` | UT-AlRDL，适合超长全局通道和顶层接出 |

代表 RC 结构锚点：

| 结构 | RC-only anchor |
|---|---:|
| `M1M0_0.034_0.02` | `39.732ps` |
| `M2M0_0.02_0.02` | `103.790ps` |
| `M5M0_0.038_0.038` | `15.500ps` |
| `M10M0_0.062_0.064` | `4.421ps` |
| `M12M0_0.126_0.126` | `0.855ps` |
| `M14M0_0.45_0.45` | `0.054ps` |
| `M16M0_1.8_1.8` | `0.006ps` |

使用规则：

- 局部热路径优先在物理邻近区域闭合。
- 跨 slice 数据通路优先用 `M10+` 并切拍。
- 跨 core 主干优先用 `M12+`。
- 跨 tile 或顶层接出优先用 `M14+` / `M16`。
- 低层金属不承担宽、长、单周期全局广播。

## 5. 绑定检查表

每个 foundation primitive 必须回答：

- 主要由标准单元还是 SRAM/PRF 宏实现。
- 如果是标准单元，估算 FO4 深度是多少。
- 如果是 SRAM/PRF，使用哪类宏、多少 bank、几周期访问。
- 如果有跨区线，使用哪个金属层级和几级 pipeline。
- 是否进入 `4GHz` 单周期热路径。
- 是否有 replay / flush / recover 参与。
