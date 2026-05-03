# VRF Operand Bank Read

## 1. 职责

从 banked VRF 读取 lane group operand，并对齐 mask/predicate payload。

本文定义朱雀目标结构中的数据面边界、slice/bank 组织、时序边界和行为模型接口。

## 2. 结构规模摘要

| 项 | 数值 |
|---|---:|
| datapath units | `73` |
| module count | `73` |
| logic LOC | `71104` |
| assign count | `12193` |
| always count | `1355` |
| port declarations | `4672` |

高频数据面 token：`data`=12856, `bank`=3867, `mask`=3433, `addr`=1843, `way`=1373, `l1`=696, `fault`=522, `tag`=332。

## 3. 数据结构

![VRF Operand Bank Read](../../../assets/datapath_units/vector_execute/vrf_operand.png)

```mermaid
flowchart LR
  N0["vector issue"]
  N1["VRF bank read"]
  N2["lane operand latch"]
  N0 --> N1
  N1 --> N2
```

## 4. 输入接口

| 输入 | 说明 |
| --- | --- |
| `vector_issue` | 进入本分区的数据 packet 或局部字段 |
| `vrf_bank` | 进入本分区的数据 packet 或局部字段 |

## 5. 输出接口

| 输出 | 说明 |
| --- | --- |
| `vector_operand` | 离开本分区的数据 packet 或局部字段 |
| `mask_operand` | 离开本分区的数据 packet 或局部字段 |

## 6. Slice / Bank / Latch

| 类别 | 规则 |
|---|---|
| width | `按域内 packet / slice 参数化` |
| slice | 向量以 64-bit lane group 组织，每 group 保留 64 slice。 |
| bank | VRF 24 bank 预算，每 bank 至少一个 PRF leaf。 |
| latch / register | VRF read 后进入 lane latch。 |

## 7. N07 PPA 初始模型

| 项 | 数值 |
|---|---:|
| raw area estimate | `42331.441 um2` |
| placed area estimate | `80694.309 um2` |
| logic depth | `9 FO4` |
| mux penalty | `16.000 ps` |
| wire budget | `16.000 ps` |
| margin | `45.000 ps` |
| estimated path | `168.138 ps` |
| 4GHz slack | `81.862 ps` |

估算公式：

```text
path_ps = DFF_CP_Q + FO4 * logic_depth + mux_penalty + wire_budget + margin
area_um2 = code_metric_units * INV_D1_area * mix_factor + macro_area
```

## 8. 行为模型契约

行为模型必须覆盖：

- VRF bank read
- mask 对齐
- bank conflict
- scalar broadcast

最小接口：

```python
class VectorExecuteVrfOperand:
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

- `vector_execute_vrf_operand_packet`
- `vector_execute_vrf_operand_slice`
- `vector_execute_vrf_operand_pipe`
- `vector_execute_vrf_operand_top`

## 10. 检查点

- bank conflict
- mask 全零
- 跨 lane 读取

