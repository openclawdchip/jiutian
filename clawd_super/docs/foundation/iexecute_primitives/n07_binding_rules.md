# IExecute Primitive N07 绑定规则

## 1. 基础锚点

朱雀整数执行基础构件使用下面 N07 锚点。

| 项 | 数值 |
|---|---:|
| `INV D1` area | `0.04104 um^2` |
| `NAND2 D1` area | `0.05472 um^2` |
| `DFF D1` area | `0.2736 um^2` |
| `INV D1 FO4` | `7.252ps` |
| `NAND2 D1 FO4` | `8.8ps` 级 |
| `DFF CP->Q` | `25.870ps` |
| target period | `250ps` |

标准单元路径估算：

```text
path_delay_ps =
  25.870
  + logic_depth_fo4 * 7.252
  + mux_penalty_ps
  + wire_delay_ps
  + setup_margin_ps
```

## 2. Wire 绑定

| 路径 | 默认金属层 | 初始线延时锚点 |
|---|---|---:|
| bit slice 内短线 | `M1/M2/M4` | `19ps..104ps` local structure risk |
| 相邻 slice / local cluster | `M5~M9` | `15.5ps` class |
| 跨 lane / result local spine | `M10~M11` | `4.421ps` class |
| core 内长 result / redirect spine | `M12~M13` | `0.855ps` class |
| tile / fabric | `M14+` | not used by local iexecute primitive |

低层局部线不能被假定为免费资源。`64` 个 bit slice 的横向归约必须分树，不能形成单条横穿线。

## 3. Latch 绑定

整数执行快路径使用局部 latch boundary。

| boundary | 类型 | 用途 |
|---|---|---|
| `IX_OPRD_L0` | phase latch | operand read / bypass 输出 |
| `IX_EXEC_L1` | phase latch | add/shift/compare 局部中点 |
| `IX_EXEC_L2` | phase latch | result local merge 输入 |
| `IX_WB_R` | register | 跨 cluster / writeback spine |

时间借用规则：

| 项 | 约束 |
|---|---:|
| local borrow cap | `35ps` |
| non-overlap guard | `15ps` |
| cross-cluster borrow | `0ps` |
| cross-result-spine borrow | `0ps` |

## 4. Slice 绑定

`64-bit` 标量数据通路必须实现为 `64` 个 `zq_ix_*_bit_slice`。

允许跨 bit 的网络：

- carry group
- zero reduce
- sign / overflow reduce
- compare condition reduce
- saturation detect
- mask / predicate reduce
- CRC fold tree

禁止默认单体化的网络：

- `64-bit` 单点大 mux
- `64-bit` 单点 compare
- `64-bit` 单点 result select
- 全部执行输入进入一个中心 result mux

## 5. Primitive PPA 模板

每个 primitive 必须填下面字段。

| 字段 | 说明 |
|---|---|
| `state_element` | DFF / latch / none |
| `logic_fo4` | 局部组合深度 |
| `mux_penalty_ps` | 局部选择器惩罚 |
| `wire_class_ps` | 线网锚点 |
| `setup_margin_ps` | setup / uncertainty / reserve |
| `estimated_path_ps` | 合计路径 |
| `slack_ps` | `250ps - estimated_path_ps` |
| `area_model` | DFF + INV/NAND/MUX equivalent |
| `slice_count` | bit slice 或 lane slice 数 |
| `pipeline_rule` | single-cycle / latch-split / multi-cycle |

## 6. 路径等级

| 等级 | 定义 | 约束 |
|---|---|---|
| `IX_FAST0` | branch compare / simple add flag | 局部 latch-split，目标 `<= 250ps` |
| `IX_FAST1` | shift / bitfield / mask merge | 局部一到两级，目标 `<= 250ps` 每级 |
| `IX_MID` | multiply partial / compress | 多级 pipeline，每级 `<= 250ps` |
| `IX_SLOW` | divide / CRC / auth / rare special | 多周期，不能阻塞 fast lane |
| `IX_WB` | result merge / packet writeback | 分层 merge，跨 spine 前寄存 |

## 7. 构件检查

每个构件进入行为模型前必须确认：

- 是否是 `64` 个 bit slice 或明确的 lane group。
- 是否有 latch / register boundary。
- 是否有估算路径时延和 slack。
- 是否有面积估算模型。
- 是否说明跨 slice 网络如何分层。
- 是否说明 result packet 如何进入 writeback。
