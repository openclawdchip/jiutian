# L2 Request Ingress

## 1. 职责

接收 L1I/L1D/MMU/fabric request，形成 L2 bank request packet。

本文定义朱雀目标结构中的数据面边界、slice/bank 组织、时序边界和行为模型接口。

## 2. 结构规模摘要

| 项 | 数值 |
|---|---:|
| datapath units | `19` |
| module count | `17` |
| logic LOC | `31820` |
| assign count | `2568` |
| always count | `1503` |
| port declarations | `2842` |

高频数据面 token：`l2`=17384, `data`=6149, `tag`=4792, `cache`=3040, `valid`=2884, `way`=2685, `addr`=1509, `ecc`=1358。

## 3. 数据结构

![L2 Request Ingress](../../../assets/datapath_units/level2_cache/l2_ingress.png)

```mermaid
flowchart LR
  N0["core request"]
  N1["bank hash"]
  N2["request queue"]
  N0 --> N1
  N1 --> N2
```

## 4. 输入接口

| 输入 | 说明 |
| --- | --- |
| `l1_miss` | 进入本分区的数据 packet 或局部字段 |
| `walk_req` | 进入本分区的数据 packet 或局部字段 |
| `fabric_req` | 进入本分区的数据 packet 或局部字段 |

## 5. 输出接口

| 输出 | 说明 |
| --- | --- |
| `l2_bank_req` | 离开本分区的数据 packet 或局部字段 |

## 6. Slice / Bank / Latch

| 类别 | 规则 |
|---|---|
| width | `按域内 packet / slice 参数化` |
| slice | 地址 slice 低位用于 bank select，高位进入 tag。 |
| bank | request queue banked，credit 与 payload 分离。 |
| latch / register | core->L2 边界寄存。 |

## 7. N07 PPA 初始模型

| 项 | 数值 |
|---|---:|
| raw area estimate | `4309.688 um2` |
| placed area estimate | `8215.343 um2` |
| logic depth | `9 FO4` |
| mux penalty | `18.000 ps` |
| wire budget | `16.000 ps` |
| margin | `45.000 ps` |
| estimated path | `170.138 ps` |
| 4GHz slack | `79.862 ps` |

估算公式：

```text
path_ps = DFF_CP_Q + FO4 * logic_depth + mux_penalty + wire_budget + margin
area_um2 = code_metric_units * INV_D1_area * mix_factor + macro_area
```

## 8. 行为模型契约

行为模型必须覆盖：

- request enqueue
- bank select
- credit stall
- priority class

最小接口：

```python
class Level2CacheL2Ingress:
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

- `level2_cache_l2_ingress_packet`
- `level2_cache_l2_ingress_slice`
- `level2_cache_l2_ingress_pipe`
- `level2_cache_l2_ingress_top`

## 10. 检查点

- 多源请求
- bank conflict
- credit empty

