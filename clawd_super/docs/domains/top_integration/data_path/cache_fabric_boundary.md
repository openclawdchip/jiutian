# Cache Fabric Boundary

## 1. 职责

连接 core L1/L2/fabric request/response packet。

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

![Cache Fabric Boundary](../../../assets/datapath_units/top_integration/cache_fabric_boundary.png)

```mermaid
flowchart LR
  N0["core cache req"]
  N1["L2/fabric bridge"]
  N2["response return"]
  N0 --> N1
  N1 --> N2
```

## 4. 输入接口

| 输入 | 说明 |
| --- | --- |
| `l1_miss` | 进入本分区的数据 packet 或局部字段 |
| `l2_resp` | 进入本分区的数据 packet 或局部字段 |

## 5. 输出接口

| 输出 | 说明 |
| --- | --- |
| `fabric_req` | 离开本分区的数据 packet 或局部字段 |
| `core_resp` | 离开本分区的数据 packet 或局部字段 |

## 6. Slice / Bank / Latch

| 类别 | 规则 |
|---|---|
| width | `按域内 packet / slice 参数化` |
| slice | cache line beat 分 slice，request metadata 分离。 |
| bank | L2/fabric boundary register 化。 |
| latch / register | 跨 tile 不借用时间。 |

## 7. N07 PPA 初始模型

| 项 | 数值 |
|---|---:|
| raw area estimate | `676.219 um2` |
| placed area estimate | `1289.043 um2` |
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

- request pack
- response unpack
- credit
- replay

最小接口：

```python
class TopIntegrationCacheFabricBoundary:
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

- `top_integration_cache_fabric_boundary_packet`
- `top_integration_cache_fabric_boundary_slice`
- `top_integration_cache_fabric_boundary_pipe`
- `top_integration_cache_fabric_boundary_top`

## 10. 检查点

- credit empty
- response ordering
- fault propagation

