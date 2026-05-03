# Retire Window Data Path

## 1. 职责

从 ROB head 读取 `4 x 4` retire slice，形成 retire packet。

本文定义朱雀目标结构中的数据面边界、slice/bank 组织、时序边界和行为模型接口。

## 2. 结构规模摘要

| 项 | 数值 |
|---|---:|
| datapath units | `3` |
| module count | `2` |
| logic LOC | `1882` |
| assign count | `238` |
| always count | `42` |
| port declarations | `292` |

高频数据面 token：`l2`=253, `mask`=133, `l1`=112, `vector`=48, `way`=42, `commit`=3。

## 3. 数据结构

![Retire Window Data Path](../../../assets/datapath_units/commit_and_retire/retire_window.png)

```mermaid
flowchart LR
  N0["ROB head"]
  N1["retire select"]
  N2["retire packet"]
  N0 --> N1
  N1 --> N2
```

## 4. 输入接口

| 输入 | 说明 |
| --- | --- |
| `rob_state` | 进入本分区的数据 packet 或局部字段 |
| `interrupt_hint` | 进入本分区的数据 packet 或局部字段 |

## 5. 输出接口

| 输出 | 说明 |
| --- | --- |
| `retire_packet` | 离开本分区的数据 packet 或局部字段 |
| `oldest_fault` | 离开本分区的数据 packet 或局部字段 |

## 6. Slice / Bank / Latch

| 类别 | 规则 |
|---|---|
| width | `按域内 packet / slice 参数化` |
| slice | 16/cycle commit 拆成 `4 x 4` retire slice。 |
| bank | hot valid/complete bitset 与大 payload 分离。 |
| latch / register | CT_R 输出 retire 结果。 |

## 7. N07 PPA 初始模型

| 项 | 数值 |
|---|---:|
| raw area estimate | `237.110 um2` |
| placed area estimate | `451.990 um2` |
| logic depth | `12 FO4` |
| mux penalty | `22.000 ps` |
| wire budget | `16.000 ps` |
| margin | `40.000 ps` |
| estimated path | `190.894 ps` |
| 4GHz slack | `59.106 ps` |

估算公式：

```text
path_ps = DFF_CP_Q + FO4 * logic_depth + mux_penalty + wire_budget + margin
area_um2 = code_metric_units * INV_D1_area * mix_factor + macro_area
```

## 8. 行为模型契约

行为模型必须覆盖：

- in-order retire
- oldest fault
- interrupt boundary
- retire count

最小接口：

```python
class CommitAndRetireRetireWindow:
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

- `commit_and_retire_retire_window_packet`
- `commit_and_retire_retire_window_slice`
- `commit_and_retire_retire_window_pipe`
- `commit_and_retire_retire_window_top`

## 10. 检查点

- head wrap
- fault 阻断 younger
- 16 路满退

