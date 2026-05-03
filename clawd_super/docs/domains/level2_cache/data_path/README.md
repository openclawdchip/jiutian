# Level2 Cache Data Path

## 1. 范围

level2 数据通路覆盖 core miss ingress、bank select、tag/data pipe、fill/evict、snoop/coherence 和 response return。

本文用于定义朱雀目标数据通路。控制状态机不在本文展开。

## 2. 结构规模摘要

| 项 | 数值 |
|---|---:|
| datapath units | `19` |
| module count | `17` |
| logic LOC | `31820` |
| assign count | `2568` |
| always count | `1503` |

高频数据面 token：`l2`=17384, `data`=6149, `tag`=4792, `cache`=3040, `valid`=2884, `way`=2685, `addr`=1509, `ecc`=1358, `fill`=929, `l1`=554。

## 3. 分区

| 分区 | 图 | 单元 | 模块 | 行数 | assign | always | 估算路径 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [L2 Request Ingress](l2_ingress.md) | [PNG](../../../assets/datapath_units/level2_cache/l2_ingress.png) | `19` | `17` | `31820` | `2568` | `1503` | `170.138 ps` |
| [L2 Tag Data Bank Pipe](l2_tag_data.md) | [PNG](../../../assets/datapath_units/level2_cache/l2_tag_data.png) | `17` | `15` | `31696` | `2558` | `1503` | `156.886 ps` |
| [L2 Fill Evict Data Path](l2_fill_evict.md) | [PNG](../../../assets/datapath_units/level2_cache/l2_fill_evict.png) | `15` | `13` | `29805` | `2422` | `1400` | `177.390 ps` |
| [L2 Snoop Response Path](l2_snoop_resp.md) | [PNG](../../../assets/datapath_units/level2_cache/l2_snoop_resp.png) | `9` | `7` | `28470` | `2234` | `1359` | `193.894 ps` |

## 4. 统一接口

所有分区至少支持：

- `valid`
- `ready`
- `packet`
- `kill_token`
- `replay_token`
- `fault_meta`
- `area_estimate`
- `delay_estimate`

## 5. 实现顺序

1. 先实现本目录中的 packet 和 slice 类型。
2. 再实现 bank / queue / macro wrapper。
3. 然后实现本地 pipeline register 或 latch boundary。
4. 最后接入控制通路状态机。

