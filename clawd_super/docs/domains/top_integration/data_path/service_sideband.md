# Service Sideband Data Path

## 1. 职责

连接 debug、trace、interrupt、clock/reset 和 service event payload。

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

![Service Sideband Data Path](../../../assets/datapath_units/top_integration/service_sideband.png)

```mermaid
flowchart LR
  N0["service event"]
  N1["sideband mux"]
  N2["core service input"]
  N0 --> N1
  N1 --> N2
```

## 4. 输入接口

| 输入 | 说明 |
| --- | --- |
| `debug_packet` | 进入本分区的数据 packet 或局部字段 |
| `interrupt_packet` | 进入本分区的数据 packet 或局部字段 |

## 5. 输出接口

| 输出 | 说明 |
| --- | --- |
| `service_packet` | 离开本分区的数据 packet 或局部字段 |

## 6. Slice / Bank / Latch

| 类别 | 规则 |
|---|---|
| width | `按域内 packet / slice 参数化` |
| slice | sideband packet 与主数据面隔离。 |
| bank | service FIFO 分域，不穿 fast path。 |
| latch / register | 进入核心状态前寄存。 |

## 7. N07 PPA 初始模型

| 项 | 数值 |
|---|---:|
| raw area estimate | `676.219 um2` |
| placed area estimate | `1289.043 um2` |
| logic depth | `8 FO4` |
| mux penalty | `16.000 ps` |
| wire budget | `16.000 ps` |
| margin | `45.000 ps` |
| estimated path | `160.886 ps` |
| 4GHz slack | `89.114 ps` |

估算公式：

```text
path_ps = DFF_CP_Q + FO4 * logic_depth + mux_penalty + wire_budget + margin
area_um2 = code_metric_units * INV_D1_area * mix_factor + macro_area
```

## 8. 行为模型契约

行为模型必须覆盖：

- sideband event
- service read/write
- reset status

最小接口：

```python
class TopIntegrationServiceSideband:
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

- `top_integration_service_sideband_packet`
- `top_integration_service_sideband_slice`
- `top_integration_service_sideband_pipe`
- `top_integration_service_sideband_top`

## 10. 检查点

- 优先级
- 跨域同步
- 事件丢失

