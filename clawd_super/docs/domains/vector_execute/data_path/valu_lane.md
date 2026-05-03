# Vector Integer Lane Field

## 1. 职责

执行 vector integer ALU、shift、saturate 和 lane-local flag。

本文定义朱雀目标结构中的数据面边界、slice/bank 组织、时序边界和行为模型接口。

## 2. 结构规模摘要

| 项 | 数值 |
|---|---:|
| datapath units | `59` |
| module count | `59` |
| logic LOC | `40478` |
| assign count | `8861` |
| always count | `952` |
| port declarations | `3416` |

高频数据面 token：`data`=7383, `bank`=2332, `l1`=2098, `mask`=1533, `way`=970, `l2`=906, `addr`=754, `fault`=439。

## 3. 数据结构

![Vector Integer Lane Field](../../../assets/datapath_units/vector_execute/valu_lane.png)

```mermaid
flowchart LR
  N0["lane operand"]
  N1["valu slice"]
  N2["lane result"]
  N0 --> N1
  N1 --> N2
```

## 4. 输入接口

| 输入 | 说明 |
| --- | --- |
| `vector_operand` | 进入本分区的数据 packet 或局部字段 |
| `mask` | 进入本分区的数据 packet 或局部字段 |

## 5. 输出接口

| 输出 | 说明 |
| --- | --- |
| `valu_result` | 离开本分区的数据 packet 或局部字段 |

## 6. Slice / Bank / Latch

| 类别 | 规则 |
|---|---|
| width | `按域内 packet / slice 参数化` |
| slice | 每 lane group 维持 64-bit slice，mask 与数据并行。 |
| bank | VALU 靠近 VRF bank 边缘。 |
| latch / register | lane 内 latch-based，跨 lane register。 |

## 7. N07 PPA 初始模型

| 项 | 数值 |
|---|---:|
| raw area estimate | `6054.582 um2` |
| placed area estimate | `11541.547 um2` |
| logic depth | `10 FO4` |
| mux penalty | `18.000 ps` |
| wire budget | `16.000 ps` |
| margin | `45.000 ps` |
| estimated path | `177.390 ps` |
| 4GHz slack | `72.610 ps` |

估算公式：

```text
path_ps = DFF_CP_Q + FO4 * logic_depth + mux_penalty + wire_budget + margin
area_um2 = code_metric_units * INV_D1_area * mix_factor + macro_area
```

## 8. 行为模型契约

行为模型必须覆盖：

- lane add/logic
- mask merge
- saturate
- rounding

最小接口：

```python
class VectorExecuteValuLane:
    def reset(self, config): ...
    def accept(self, packet, cycle): ...
    def step(self, cycle): ...
    def flush(self, token): ...
    def peek_outputs(self): ...
    def area_estimate(self): ...
    def delay_estimate(self): ...
```

## 9. RTL 落点

RTL 第一版只实现 payload、slice、bank、register/latch boundary 和 minimal ready/valid。控制状态机后续覆盖在这些接口之上。

建议 RTL 单元：

- `vector_execute_valu_lane_packet`
- `vector_execute_valu_lane_slice`
- `vector_execute_valu_lane_pipe`
- `vector_execute_valu_lane_top`

## 10. 检查点

- mask-off 不改写
- lane 独立
- 饱和边界

