# Map Table Read Slice

## 1. 职责

读取 integer、FP、vector 架构寄存器映射，形成物理源寄存器 tag。

本文定义朱雀目标结构中的数据面边界、slice/bank 组织、时序边界和行为模型接口。

## 2. 结构规模摘要

| 项 | 数值 |
|---|---:|
| datapath units | `16` |
| module count | `15` |
| logic LOC | `117036` |
| assign count | `22420` |
| always count | `2290` |
| port declarations | `6146` |

高频数据面 token：`decode`=15536, `valid`=10377, `tag`=7872, `data`=5086, `mask`=3240, `way`=2445, `ready`=1797, `cache`=1173。

## 3. 数据结构

![Map Table Read Slice](../../../assets/datapath_units/rename/map_read.png)

```mermaid
flowchart LR
  N0["uop packet"]
  N1["domain map table"]
  N2["source tag pack"]
  N0 --> N1
  N1 --> N2
```

## 4. 输入接口

| 输入 | 说明 |
| --- | --- |
| `uop_packet` | 进入本分区的数据 packet 或局部字段 |
| `recovery_map` | 进入本分区的数据 packet 或局部字段 |

## 5. 输出接口

| 输出 | 说明 |
| --- | --- |
| `src_phys` | 离开本分区的数据 packet 或局部字段 |
| `src_ready` | 离开本分区的数据 packet 或局部字段 |

## 6. Slice / Bank / Latch

| 类别 | 规则 |
|---|---|
| width | `按域内 packet / slice 参数化` |
| slice | 源寄存器 tag 按 uop slice 读出，不能集中成 16 路大表。 |
| bank | map table 按寄存器域 bank 化。 |
| latch / register | RN_ALLOC_R 前保存 map read 结果。 |

## 7. N07 PPA 初始模型

| 项 | 数值 |
|---|---:|
| raw area estimate | `14501.534 um2` |
| placed area estimate | `27643.550 um2` |
| logic depth | `10 FO4` |
| mux penalty | `16.000 ps` |
| wire budget | `16.000 ps` |
| margin | `40.000 ps` |
| estimated path | `170.390 ps` |
| 4GHz slack | `79.610 ps` |

估算公式：

```text
path_ps = DFF_CP_Q + FO4 * logic_depth + mux_penalty + wire_budget + margin
area_um2 = code_metric_units * INV_D1_area * mix_factor + macro_area
```

## 8. 行为模型契约

行为模型必须覆盖：

- map lookup
- domain select
- zero/source ready
- recovery map visibility

最小接口：

```python
class RenameMapRead:
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

- `rename_map_read_packet`
- `rename_map_read_slice`
- `rename_map_read_pipe`
- `rename_map_read_top`

## 10. 检查点

- 多域源寄存器
- 无目的 uop
- 恢复中读取

