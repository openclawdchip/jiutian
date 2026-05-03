# Core Packet Spine

## 1. 职责

组织 fetch->decode->rename->issue->execute->writeback->commit 主数据面。

本文定义朱雀目标结构中的数据面边界、slice/bank 组织、时序边界和行为模型接口。

## 2. 结构规模摘要

| 项 | 数值 |
|---|---:|
| datapath units | `4` |
| module count | `4` |
| logic LOC | `18518` |
| assign count | `22` |
| always count | `0` |
| port declarations | `1277` |

高频数据面 token：`l2`=2297, `data`=2091, `tag`=1212, `valid`=682, `issue`=356, `addr`=318, `tlb`=298, `bank`=258。

## 3. 数据结构

![Core Packet Spine](../../../assets/datapath_units/top_integration/core_packet_spine.png)

```mermaid
flowchart LR
  N0["domain packets"]
  N1["core spine"]
  N2["domain boundary"]
  N0 --> N1
  N1 --> N2
```

## 4. 输入接口

| 输入 | 说明 |
| --- | --- |
| `domain_output` | 进入本分区的数据 packet 或局部字段 |

## 5. 输出接口

| 输出 | 说明 |
| --- | --- |
| `domain_input` | 离开本分区的数据 packet 或局部字段 |

## 6. Slice / Bank / Latch

| 类别 | 规则 |
|---|---|
| width | `按域内 packet / slice 参数化` |
| slice | 主干只传 packet，不重新组合 64-bit 数据云。 |
| bank | 跨域 FIFO/ready-valid banked。 |
| latch / register | 每个域边界寄存。 |

## 7. N07 PPA 初始模型

| 项 | 数值 |
|---|---:|
| raw area estimate | `676.219 um2` |
| placed area estimate | `1289.043 um2` |
| logic depth | `8 FO4` |
| mux penalty | `14.000 ps` |
| wire budget | `16.000 ps` |
| margin | `40.000 ps` |
| estimated path | `153.886 ps` |
| 4GHz slack | `96.114 ps` |

估算公式：

```text
path_ps = DFF_CP_Q + FO4 * logic_depth + mux_penalty + wire_budget + margin
area_um2 = code_metric_units * INV_D1_area * mix_factor + macro_area
```

## 8. 行为模型契约

行为模型必须覆盖：

- packet handoff
- ready/valid
- fault/replay sideband

最小接口：

```python
class TopIntegrationCorePacketSpine:
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

- `top_integration_core_packet_spine_packet`
- `top_integration_core_packet_spine_slice`
- `top_integration_core_packet_spine_pipe`
- `top_integration_core_packet_spine_top`

## 10. 检查点

- backpressure
- kill
- fault metadata

