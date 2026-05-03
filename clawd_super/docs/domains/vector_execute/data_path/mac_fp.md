# Vector MAC FP Cluster

## 1. 职责

执行 vector MAC、dot product、FP helper 和 local reduction。

本文定义朱雀目标结构中的数据面边界、slice/bank 组织、时序边界和行为模型接口。

## 2. 结构规模摘要

| 项 | 数值 |
|---|---:|
| datapath units | `54` |
| module count | `54` |
| logic LOC | `57615` |
| assign count | `8502` |
| always count | `1037` |
| port declarations | `3083` |

高频数据面 token：`data`=9412, `bank`=3329, `mask`=1079, `way`=1055, `addr`=869, `l1`=803, `fault`=473, `l2`=417。

## 3. 数据结构

![Vector MAC FP Cluster](../../../assets/datapath_units/vector_execute/mac_fp.png)

```mermaid
flowchart LR
  N0["lane operand"]
  N1["partial product"]
  N2["local accumulate"]
  N3["cluster result"]
  N0 --> N1
  N1 --> N2
  N2 --> N3
```

## 4. 输入接口

| 输入 | 说明 |
| --- | --- |
| `vector_operand` | 进入本分区的数据 packet 或局部字段 |
| `accumulate` | 进入本分区的数据 packet 或局部字段 |

## 5. 输出接口

| 输出 | 说明 |
| --- | --- |
| `mac_result` | 离开本分区的数据 packet 或局部字段 |
| `fp_result` | 离开本分区的数据 packet 或局部字段 |

## 6. Slice / Bank / Latch

| 类别 | 规则 |
|---|---|
| width | `按域内 packet / slice 参数化` |
| slice | MAC/FP 使用多级 pipeline，局部 reduce 后再出簇。 |
| bank | MAC/FP 簇围绕 VRF 长边布置。 |
| latch / register | 每级 pipeline <= 250ps。 |

## 7. N07 PPA 初始模型

| 项 | 数值 |
|---|---:|
| raw area estimate | `5993.586 um2` |
| placed area estimate | `11425.274 um2` |
| logic depth | `14 FO4` |
| mux penalty | `22.000 ps` |
| wire budget | `16.000 ps` |
| margin | `45.000 ps` |
| estimated path | `210.398 ps` |
| 4GHz slack | `39.602 ps` |

估算公式：

```text
path_ps = DFF_CP_Q + FO4 * logic_depth + mux_penalty + wire_budget + margin
area_um2 = code_metric_units * INV_D1_area * mix_factor + macro_area
```

## 8. 行为模型契约

行为模型必须覆盖：

- MAC
- dot product
- FP helper
- reduction

最小接口：

```python
class VectorExecuteMacFp:
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

- `vector_execute_mac_fp_packet`
- `vector_execute_mac_fp_slice`
- `vector_execute_mac_fp_pipe`
- `vector_execute_mac_fp_top`

## 10. 检查点

- signedness
- rounding metadata
- multi-cycle valid

