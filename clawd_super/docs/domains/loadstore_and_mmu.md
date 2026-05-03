# LoadStore And MMU

## 1. 角色

loadstore and mmu 共同构成朱雀后端最复杂的访存子系统，负责地址生成、权限和地址翻译、队列排序、数据对齐、缓存访问、预取、snoop 和与二级缓存的连接。

## 2. 范围

这个域包含：

- AGU
- TLB / translation
- load queue
- store address / store data buffer
- replay queue
- forwarding
- unaligned handling
- tag/data array pipe
- fill buffer
- prefetch
- snoop

## 3. 固定目标

| 项目 | 定义 |
|---|---|
| Load AGU | `8` |
| Store AGU | `6` |
| Store data path | `6` |
| Load queue | `192` entries |
| Store address queue | `192` entries |
| Store data queue | `192` entries |
| Replay queue | `96` entries |
| Fill buffer | `64` entries |
| DTLB L1 | `192` entries |
| STLB | `6144` entries |
| Outstanding miss | `128` |
| Prefetch streams | `96` |

## 4. 关键原则

- 访存顺序必须显式建模
- 地址翻译和缓存访问分层
- replay 不是异常路径，而是正常事务的一部分
- store commit 由 commit 明确授权

## 5. 输入输出

| 输入 | 说明 |
|---|---|
| memory issue packet | 来自 issue |
| commit precommit/store commit | 来自 commit |
| level2 response | 来自 L2 |
| control/debug events | 来自平台控制 |

| 输出 | 说明 |
|---|---|
| load writeback | 回 issue/PRF |
| exception/fault | 回 commit |
| cache request | 发往 L2 |
| replay/block | 反馈给 issue |

## 6. 状态对象

- load queue
- store address buffer
- store data buffer
- replay queue
- fill buffer
- TLB state
- outstanding cache request state

## 7. Floorplan 视角

### 7.1 物理目标

loadstore and mmu 的关键是把 `AGU -> translate -> tag/data access -> forward/replay` 做成可守频的分层流水，同时让 store commit 和 `L2` 出口都沿最短物理方向闭合。这个域不能只按功能聚类，必须围绕 `L1D`、`DTLB` 和队列群布置。

### 7.2 推荐分区

- AGU 紧贴 memory issue 输出口，减少地址生成前的长线。
- `DTLB`、权限检查和 `L1D tag/data` 形成一组紧耦合访存热区。
- load queue、store address queue、store data queue 和 forwarding 比较网络贴近 `L1D` 一侧，减少老化、转发和 replay 往返。
- fill buffer、miss queue、prefetch egress 和 `L2` request 出口位于 core 边界，朝 tile 级缓存方向展开。

### 7.3 时序约束

- 地址形成、翻译、cache access 默认是明确分级的，不允许压成单一组合深路径。
- store-to-load forwarding 先本地命中，再做更远范围的比较和 replay 决策。
- snoop、维护和诊断路径不得进入 `L1D tag/data` 热流水。
- store commit 授权路径要朝 commit 脊柱闭合，miss 返回路径要朝 `L2` 边界闭合。

### 7.4 对后续模型的约束

- 行为模型需要带上队列分段、forwarding 优先级、bank 冲突、replay 队列和 `L2` 往返延迟边界。
- RTL 应把 AGU、translate、queue/hazard、align/forward、cache access、fill/replay、prefetch 明确拆开。

## 8. 行为模型落点

行为模型应覆盖：

- 地址生成
- 翻译命中与 fault
- load/store 入队
- store-to-load forwarding
- replay
- prefetch 请求形成
- store commit 生效点

## 9. RTL 落点

RTL 可以拆成：

- address translate
- queue and hazard
- align and forward
- cache access
- prefetch
- snoop
- loadstore top

## 10. 模块文档

- `loadstore_and_mmu/README.md`
- `loadstore_and_mmu/INDEX.md`
- `loadstore_and_mmu/data_path/README.md`
- `loadstore_and_mmu/control_path/README.md`
- `loadstore_and_mmu/top_mixed/README.md`
