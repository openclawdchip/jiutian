# 朱雀总体架构

## 1. 一句话定义

`zhuque / 朱雀` 是一套面向高并发运行时、支持标量与向量混合执行的 RISC-V 主机处理器与集群架构。它由乱序核心、层次化缓存、可扩展 cluster fabric、系统控制与调试框架共同组成。

## 2. 总体设计目标

| 项目 | 定义 |
|---|---|
| 最高主频目标 | `4.0 GHz` |
| 核心风格 | 高宽度、高并发、深后端 OoO |
| 前端目标 | 以 `16` 路译码为中心构建高供给前端 |
| 后端目标 | 提供显著放大的执行、访存和退休并发能力 |
| 存储目标 | 提供大容量队列、深缓冲和更强缓存层级支撑 |
| 集群目标 | 以更高吞吐的 tile 和 fabric 组织支撑整体性能上限 |

## 3. 顶层层级

朱雀采用四级层级组织：

```text
zhuque_subsystem
  -> zhuque_cluster
      -> zhuque_tile
          -> zhuque_core
```

各级职责如下：

| 层级 | 作用 |
|---|---|
| `zhuque_subsystem` | 对接 SoC、外部内存、系统控制和调试环境 |
| `zhuque_cluster` | 组织多个 tile、共享缓存 slice、互连、目录和全局服务 |
| `zhuque_tile` | 容纳核心、本地二级缓存、目录入口和局部控制 |
| `zhuque_core` | 执行 RV64 指令流，完成取指、解码、乱序调度、执行和退休 |

## 4. Core 主流水

朱雀核心采用分域清晰的乱序流水：

```text
ifetch
  -> decode
  -> rename
  -> issue
  -> execute / loadstore / vector
  -> writeback
  -> commit
```

这条流水由三个层面共同支撑：

- 前端：取指、预测、对齐、uop 形成
- 中段：依赖建立、队列化、唤醒选择、执行分派
- 后端：结果回写、异常精确化、状态退休、存储顺序维护

## 5. 设计域划分

为了保证后续工程推进可并行展开，朱雀把系统拆成以下设计域：

| 设计域 | 主要内容 |
|---|---|
| top integration | 顶层 wrapper、公共 package、core/tile/cluster 装配 |
| ifetch | 预测、取指、ICache 前端、fetch queue、replay |
| decode and uop | 指令解码、RVC 展开、uop contract |
| rename | 物理寄存器映射、free-list、checkpoint、恢复 |
| issue | 整数、分支、访存、向量、特殊队列与唤醒选择 |
| integer execute | ALU、shift、mul/div、特殊整数运算 |
| vector execute | RVV lane、permute、mask、vector MAC、浮点向量支路 |
| loadstore and mmu | AGU、TLB、load/store queue、cache pipe、prefetch、snoop |
| commit and retire | ROB、precise trap、interrupt/debug、store commit、回收 |
| level2 cache | L2 tag/data/bank/pipe/response/replacement/prefetch |
| cluster fabric | cluster transport、slice、bridge、shared service、directory |
| platform control and debug | debug、trace、intctrl、clock/reset、功耗和服务控制 |
| shared cells and models | RAM model、CDC、小型公共元件和基础库 |

## 6. 目标配置

| 项目 | 定义 |
|---|---|
| ISA 基线 | RV64GCV |
| SMT | `SMT2` |
| Fetch 带宽 | `192B/cycle` |
| Decode 宽度 | `16 inst/cycle` |
| Rename 宽度 | `16 uop/cycle` |
| Dispatch 宽度 | `16 uop/cycle` |
| Commit 宽度 | `16 uop/cycle` |
| ROB | `1024` entries |
| Integer PRF | `640` |
| FP PRF | `512` |
| Vector PRF | `768` |
| Tile 核数 | `8` |
| L1I | `256KB` / core |
| L1D | `256KB` / core |
| L2 | `16MB` / tile，`64` banks |
| L3 Slice | `32MB` / tile |
| Cluster 互连 | 宽带 packetized fabric |
| 调试/中断 | 统一平台控制域管理 |

## 7. 宽度与资源定义

| 资源 | 定义 |
|---|---|
| Integer issue select | `16/cycle` |
| Memory issue select | `12/cycle` |
| Vector issue select | `12/cycle` |
| Simple ALU | `8` |
| Branch / compare | `6` |
| Integer MUL | `6` |
| Integer DIV / special | `4` |
| Load AGU | `8` |
| Store AGU | `6` |
| Store data path | `6` |
| Vector integer cluster | `12` |
| Vector permute cluster | `6` |
| Vector MAC cluster | `8` |
| Vector FP cluster | `6` |

## 8. 命名约定

顶层命名统一使用 `zhuque`：

- package：`zhuque_pkg`
- core top：`zhuque_core`
- tile top：`zhuque_tile`
- cluster top：`zhuque_cluster`
- subsystem top：`zhuque_subsystem`

各设计域采用 `zhuque_<domain>_*` 风格：

- `zhuque_ifetch_*`
- `zhuque_decode_*`
- `zhuque_rn_*`
- `zhuque_is_*`
- `zhuque_ix_*`
- `zhuque_vx_*`
- `zhuque_ls_*`
- `zhuque_ct_*`
- `zhuque_l2_*`
- `zhuque_cl_*`

## 9. 后续实现关系

后续三层实现关系固定如下：

1. 文档定义域边界和事务
2. 行为模型实现文档中的状态转移和事务
3. RTL 将行为模型拆成时序结构和物理接口

这样可以保证朱雀从一开始就是“规格驱动实现”，而不是“代码倒推出规格”。

## 10. Floorplan 导向

朱雀的实现默认采用 `floorplan-first` 约束，不把物理规划留到 RTL 之后再兜底。对总体架构有直接约束的结论是：

- 前端采用 `banked fetch + sliced decode`
- `L1I` / `L1D` 默认是多 bank、多拍访问结构
- rename / issue / PRF / ROB 默认采用 slice / bank 组织
- integer / vector / loadstore 以物理分区方式组织，再在写回侧分层合并
- `L2` / fabric 默认采用分布式和切拍式结构

详细规则见 `zhuque-floorplan-driven-design.md`。
