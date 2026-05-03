# Replay Resource Data Path

## 1. 职责

处理 replay token、resource busy 和 entry 保留/重发数据面。

本文定义朱雀目标结构中的数据面边界、slice/bank 组织、时序边界和行为模型接口。

## 2. 结构规模摘要

| 项 | 数值 |
|---|---:|
| datapath units | `7` |
| module count | `7` |
| logic LOC | `31392` |
| assign count | `5296` |
| always count | `389` |
| port declarations | `4193` |

高频数据面 token：`tag`=5213, `data`=2143, `addr`=1871, `issue`=711, `valid`=433, `way`=389, `l1`=97, `bank`=72。

## 3. 数据结构

![Replay Resource Data Path](../../../assets/datapath_units/issue/replay_resource.png)

```mermaid
flowchart LR
  N0["replay token"]
  N1["queue entry"]
  N2["resource blocker"]
  N0 --> N1
  N1 --> N2
```

## 4. 输入接口

| 输入 | 说明 |
| --- | --- |
| `replay_token` | 进入本分区的数据 packet 或局部字段 |
| `resource_busy` | 进入本分区的数据 packet 或局部字段 |

## 5. 输出接口

| 输出 | 说明 |
| --- | --- |
| `retry_entry` | 离开本分区的数据 packet 或局部字段 |
| `stall_hint` | 离开本分区的数据 packet 或局部字段 |

## 6. Slice / Bank / Latch

| 类别 | 规则 |
|---|---|
| width | `按域内 packet / slice 参数化` |
| slice | replay 是队列数据对象，不是独立控制旁路。 |
| bank | replay queue 与主 issue bank 相邻。 |
| latch / register | replay 返回跨域时寄存。 |

## 7. N07 PPA 初始模型

| 项 | 数值 |
|---|---:|
| raw area estimate | `3996.617 um2` |
| placed area estimate | `7618.551 um2` |
| logic depth | `10 FO4` |
| mux penalty | `18.000 ps` |
| wire budget | `16.000 ps` |
| margin | `40.000 ps` |
| estimated path | `172.390 ps` |
| 4GHz slack | `77.610 ps` |

估算公式：

```text
path_ps = DFF_CP_Q + FO4 * logic_depth + mux_penalty + wire_budget + margin
area_um2 = code_metric_units * INV_D1_area * mix_factor + macro_area
```

## 8. 行为模型契约

行为模型必须覆盖：

- load replay
- execution busy
- entry retain
- retry

最小接口：

```python
class IssueReplayResource:
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

- `issue_replay_resource_packet`
- `issue_replay_resource_slice`
- `issue_replay_resource_pipe`
- `issue_replay_resource_top`

## 10. 检查点

- replay 顺序
- younger flush
- busy 解除

