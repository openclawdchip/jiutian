# 朱雀数据通路 PPA 初始账本

## 1. 目的

本文记录朱雀 full-core 数据通路的初始面积、时延、macro 数量和 `4.0GHz` slack。

这些数值用于前端设计阶段的闭合判断。它们不是 signoff 数字，但每个数都必须来自 N07 primitive 锚点或由锚点计算得到。

## 2. N07 锚点

### 2.1 标准单元锚点

| 项 | 数值 |
|---|---:|
| `INV D1` area | `0.04104 um^2` |
| `NAND2 D1` area | `0.05472 um^2` |
| `DFF D1` area | `0.2736 um^2` |
| `INV D1 FO4` | `7.252ps` |
| `DFF CP->Q` | `25.870ps` |
| target period | `250ps` |

早期标准单元路径估算：

```text
path_ps =
  25.870
  + logic_depth_fo4 * 7.252
  + mux_penalty_ps
  + wire_delay_ps
  + setup_margin_ps
```

### 2.2 Memory / PRF 锚点

| 宏 | 容量 | Area | Cycle | 用途 |
|---|---:|---:|---:|---|
| `L1CACHE` | `36Kbit` | `2429.431 um^2` | `245ps` | L1 小叶子 |
| `HSSPSRAM` | `36Kbit` | `2774.188 um^2` | `238ps` | 高频小数组 |
| `1PRF` | `16Kbit` | `1417.590 um^2` | `249ps` | PRF bank |
| `UHDSPSRAM` | `156Kbit` | `7595.191 um^2` | `562ps` | L2/L3 密集数组 |

### 2.3 Wire 锚点

| 结构 | RC-only anchor |
|---|---:|
| `M5M0_0.038_0.038` | `15.500ps` |
| `M10M0_0.062_0.064` | `4.421ps` |
| `M12M0_0.126_0.126` | `0.855ps` |
| `M14M0_0.45_0.45` | `0.054ps` |
| `M16M0_1.8_1.8` | `0.006ps` |

## 3. Macro 面积账本

面积换算：

```text
1 mm^2 = 1,000,000 um^2
```

### 3.1 L1I Data

| 项 | 数值 |
|---|---:|
| target capacity | `256KB = 2048Kbit` |
| macro class | `L1CACHE 36Kbit` |
| selected leaves | `64` |
| raw macro capacity | `2304Kbit` |
| raw macro area | `155483.584 um^2` |
| raw macro area | `0.1555 mm^2` |

L1I data leaf 至少 `2` 级 pipeline。`245ps` macro cycle 已接近 `250ps`，不能再叠加长 mux 和远线。

### 3.2 L1D Data

| 项 | `L1CACHE` 方案 | `HSSPSRAM` 方案 |
|---|---:|---:|
| target capacity | `256KB` | `256KB` |
| selected leaves | `64` | `64` |
| raw macro capacity | `2304Kbit` | `2304Kbit` |
| raw macro area | `0.1555 mm^2` | `0.1775 mm^2` |
| macro cycle | `245ps` | `238ps` |

L1D 默认按 bank group 混用策略建模：load hot bank 优先 `HSSPSRAM`，普通 data leaf 可用 `L1CACHE`。

### 3.3 L2 Data

| 项 | 数值 |
|---|---:|
| target capacity | `16MB = 131072Kbit` |
| macro class | `UHDSPSRAM 156Kbit` |
| bank count | `64` |
| leaves / bank | `14` |
| selected leaves | `896` |
| raw macro capacity | `139776Kbit` |
| raw macro area | `6805291.136 um^2` |
| raw macro area | `6.8053 mm^2` |
| macro cycle | `562ps` |

L2 bank data 不进入 core 单周期闭环，默认 `3+` cycle bank pipe。

### 3.4 L3 Slice Data

| 项 | 数值 |
|---|---:|
| target capacity | `32MB = 262144Kbit` |
| macro class | `UHDSPSRAM 156Kbit` |
| bank group | `128` |
| leaves / bank group | `14` |
| selected leaves | `1792` |
| raw macro capacity | `279552Kbit` |
| raw macro area | `13610582.272 um^2` |
| raw macro area | `13.6106 mm^2` |
| macro cycle | `562ps` |

L3 slice 是 tile/cluster 数据面，不参与 core 高频本地闭环。

### 3.5 PRF Capacity Lower Bound

| PRF | logical bits | minimum `1PRF` leaves | raw macro area |
|---|---:|---:|---:|
| integer PRF | `640 x 64 = 40960 bit` | `3` | `0.0043 mm^2` |
| FP PRF | `512 x 64 = 32768 bit` | `2` | `0.0028 mm^2` |
| vector PRF lane groups | `768 x 64 = 49152 bit` | `3` | `0.0043 mm^2` |

上述为容量下界，不包含端口复制、bank 拆分、ECC、write driver 和物理通道。设计使用的 floorplan 预算必须按 logical bank 数放大。

### 3.6 PRF Floorplan Budget

| PRF | logical bank | selected leaves | raw macro area | 说明 |
|---|---:|---:|---:|---|
| integer PRF | `16` | `16` | `0.0227 mm^2` | 每 bank 至少一个小 PRF leaf |
| FP PRF | `16` | `16` | `0.0227 mm^2` | 靠近 FP/vector 边界 |
| vector PRF | `24` | `24` | `0.0340 mm^2` | lane group bank |

PRF 的真实 floorplan 面积还要加端口复制和局部 bypass 通道。后续 RTL/PnR 前，PRF area 账本必须分成 macro、read mux、write mux、bypass wire 四项。

## 4. 标准单元数据通路账本

### 4.1 Pipeline Register Bits

按 `DFF D1 area = 0.2736 um^2` 估算：

| 数据通路寄存对象 | bits / stage | DFF raw area / stage |
|---|---:|---:|
| `16` 路 uop packet，`256b/uop` | `4096` | `1120.666 um^2` |
| `16` 路 renamed uop，`320b/uop` | `5120` | `1400.832 um^2` |
| `16` 路 issue payload，`384b/uop` | `6144` | `1680.998 um^2` |
| `16` 路 result tag，`96b/result` | `1536` | `420.250 um^2` |
| `8` 路 load return，`128b/load` | `1024` | `280.166 um^2` |
| `16` 路 commit payload，`192b/slot` | `3072` | `840.499 um^2` |

寄存器面积是 bit-level 下界，不包含 clock gate、scan、reset、hold buffer 和布线通道。

### 4.2 Bit Slice Cell Budget

每个 `64-bit` scalar lane 由 `64` 个 bit slice 组成。

| bit slice 局部对象 | 估算锚点 | 单 bit 逻辑深度 |
|---|---|---:|
| operand latch | DFF / latch equivalent | `1` state element |
| local bypass mux | NAND/INV/MUX | `3..5 FO4` |
| add/sub bit cell | FA/NAND/INV | `2..4 FO4` |
| compare bit | XOR/NAND/INV | `2..3 FO4` |
| result select | MUX | `2..4 FO4` |

Fast ALU 不能把 `64-bit` carry、compare、result select 全部压成一个无切分组合云。carry 和 reduction 必须分组。

## 5. 关键路径时延账本

### 5.1 单周期标准单元路径

| 路径 | logic FO4 | mux ps | wire ps | margin ps | path ps | slack ps |
|---|---:|---:|---:|---:|---:|---:|
| local next-PC select | `8` | `14` | `9` | `40` | `146.886` | `103.114` |
| decode slice local table | `14` | `20` | `16` | `40` | `203.398` | `46.602` |
| local issue ready pick | `12` | `18` | `16` | `40` | `186.894` | `63.106` |
| local result merge | `10` | `20` | `16` | `40` | `174.390` | `75.610` |
| ROB segment retire pick | `12` | `22` | `16` | `40` | `190.894` | `59.106` |

这些路径可以作为单周期局部标准单元路径，但要求保持局部物理邻接。

### 5.2 Macro-Centered 路径

| 路径 | macro cycle | extra local logic | wire class | cycle plan |
|---|---:|---:|---|---|
| L1I leaf read | `245ps` | 只允许 latch / small select | local | request / data-return |
| L1D hot leaf read | `238..245ps` | 只允许 bank-local select | local | address/tag / data-return |
| PRF bank read | `249ps` | bypass 后移 | local | read stage + bypass stage |
| L2 leaf read | `562ps` | bank pipe control 分离 | tile local | `3+` core cycles |
| L3 leaf read | `562ps` | fabric packet 分离 | tile/fabric | multi-cycle |

任何接近 `250ps` 的 macro cycle 都不能再叠加长距离线和大 mux。

### 5.3 Latch-Based 局部路径

| 局部路径 | base ps | borrow cap | guard | closure rule |
|---|---:|---:|---:|---|
| PRF read latch -> bypass | `249ps macro class` | `35ps` | `15ps` | macro output 后接局部 latch |
| bypass -> ALU bit | `80..130ps` | `35ps` | `15ps` | bit slice 内 |
| ALU bit -> result latch | `70..120ps` | `35ps` | `15ps` | bit slice 内 |
| L1D data -> load return | `238..245ps macro class` | `35ps` | `15ps` | bank 内局部 |

时间借用只在局部 slice / cluster 内有效，不能跨 cluster 或 cache bank 结算。

## 6. 数据通路段 PPA 账本

| 段 | 面积主项 | 时延主项 | 初始 pipeline | 结论 |
|---|---|---|---|---|
| fetch sector | L1I data leaf `0.1555mm^2` + tag | macro `245ps` | `2+` | 不能单拍全取指 |
| align/predecode | standard cell + local latch | local mux + M5/M10 wire | `1` | 不能做 `192B` 大 mux |
| decode | standard cell table | `203ps` local path | `1` | `4 x 4` 可局部闭合 |
| rename | PRF/map/free-list bank | local pick + bank read | `2+` | map/free-list 分域 |
| issue | payload bank + bitset | local ready pick `187ps` | `1+` | 先本地 select |
| PRF read | `1PRF` bank | macro `249ps` | `1` | bypass 后移 |
| fast integer | bit slice cell | local latch + carry group | `1..2` | latch-based |
| multiply | standard cell + registers | reduction tree | `3+` | 多级 pipeline |
| divide/special | state + add/sub step | iterative | multi-cycle | 不进 fast path |
| vector | VRF bank + lane cells | bank read + lane pipe | multi-cycle | 围绕 VRF |
| LSU AGU | add/sub lane | local add path | `1` | 靠近 L1D |
| DTLB/L1D | tag/data macros | macro `238..245ps` | `2+` | banked hot path |
| writeback | local merge + PRF write | merge `174ps` | `1+` | 分层 merge |
| commit | ROB segment + bitset | retire pick `191ps` | `1+` | `4 x 4` retire |
| L2 | UHDSPSRAM `6.8053mm^2` | macro `562ps` | `3+` | tile local multi-cycle |
| L3 | UHDSPSRAM `13.6106mm^2` | macro `562ps` | multi-cycle | fabric side |

## 7. Bank Conflict / Replay 账本

| 触发端 | 冲突对象 | 数据通路响应 |
|---|---|---|
| L1I sector | fetch bank conflict | sector invalid + fetch replay |
| decode slice | slot overflow | uop pack bubble |
| rename | free-list / map bank conflict | rename stall local slice |
| issue | payload bank conflict | local grant suppress |
| PRF | read bank conflict | operand replay or delayed read |
| L1D | bank conflict / miss | load replay token |
| store queue | store data bank conflict | store data delayed |
| L2 | bank busy / MSHR full | request credit stall |
| writeback | PRF write bank conflict | writeback replay / delayed wake |

replay token 是数据对象，沿数据通路返回，不允许形成独立的不可计时旁路。

## 8. 初始 Floorplan 面积汇总

| 区域 | raw macro area | standard-cell area class | 备注 |
|---|---:|---|---|
| frontend L1I data | `0.1555mm^2` | medium | tag、align、decode 另计 |
| integer PRF floorplan | `0.0227mm^2` raw macro | high wire | 端口和 bypass 会放大 |
| FP PRF floorplan | `0.0227mm^2` raw macro | medium wire | 靠 vector 边界 |
| vector PRF floorplan | `0.0340mm^2` raw macro | high wire | lane group 周边通道大 |
| L1D data | `0.1555..0.1775mm^2` | high | tag、DTLB、LSQ 另计 |
| L2 data | `6.8053mm^2` | medium | tile 主面积 |
| L3 slice data | `13.6106mm^2` | medium | tile/cluster 侧 |

raw macro area 不是总面积。总 floorplan 还要加入 tag、ECC、control、repeaters、clock、power grid、routing channel 和 keepout。

## 9. 必须回写的 PPA 事件

后续行为模型或 RTL 发现下面事件时，必须回写本账本：

- 某条路径需要跨 cluster 但没有 register boundary。
- 某个 macro 周期接近 `250ps` 还叠加了大 mux。
- 某个 `64-bit` 数据路径被写成单体大模块。
- 某个 `16` 路结构被写成单点全局选择。
- 某个 replay / flush 走了未计时的隐式旁路。
- 某个 L2/L3 数据返回假定单周期回 core。
- 某个 PRF 端口需求无法由 bank 组织承载。

这些事件不是后端修补项，而是前端数据通路定义需要修改的信号。
