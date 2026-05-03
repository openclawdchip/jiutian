# Rename

## 1. 角色

rename 负责把架构寄存器映射到物理寄存器资源，同时建立依赖关系、维护 checkpoint，并为异常恢复提供可回滚的状态。

## 2. 核心结构

- integer map table
- floating map table
- vector map table
- integer free-list
- floating free-list
- vector free-list
- checkpoint table
- rollback / reclaim path

## 3. 固定目标

| 项目 | 定义 |
|---|---|
| Rename 宽度 | `16 uop/cycle` |
| Integer 分配宽度 | `16 dst/cycle` |
| Vector 分配宽度 | `12 dst/cycle` |
| Integer PRF | `640` |
| FP PRF | `512` |
| Vector PRF | `768` |
| Checkpoint | `96` live checkpoints |

## 4. 输入输出

| 输入 | 说明 |
|---|---|
| decoded uop | 来自 decode |
| commit reclaim | 来自 commit 的旧物理寄存器回收 |
| recovery event | 来自 commit/branch/debug 的恢复事件 |

| 输出 | 说明 |
|---|---|
| renamed uop | 送给 issue 的已物理化 uop |
| stall | 资源不足时的 backpressure |
| checkpoint id | 用于后续恢复 |

## 5. 状态

rename 必须稳定维护：

- 当前映射
- free-list 使用情况
- 每条 uop 的 old/new prf 关系
- checkpoint 快照

## 6. Floorplan 视角

### 6.1 物理目标

rename 的目标是把超宽物理寄存器分配和依赖建立压进中部短路径，同时避免 map table、free-list 和 checkpoint 互相拖长连线。它必须按域分开、按宽度切片，并且与 PRF 和 commit reclaim 保持稳定邻接关系。

### 6.2 推荐分区

- integer、FP、vector 三类映射和 free-list 物理分区，避免不同寄存器域共享大块多端口表。
- rename 入口按多 slice 组织，每个 slice 负责本地一组 uop 的寄存器读取、目标分配和标记生成。
- checkpoint 存储靠近 branch/commit 脊柱，缩短恢复与回滚路径。
- reclaim 返回口靠近 commit 输出，old prf 回收不穿越整个后端中心。

### 6.3 时序约束

- `16 uop/cycle` 的 rename 不允许所有目的寄存器在单点统一比较和分配。
- vector 映射和标量映射各自形成独立热路径，只有最终事务标签在出口统一。
- flush/recovery 需要支持 slice 化恢复，不应假定一次性重写全部表项。

### 6.4 对后续模型的约束

- 行为模型需要显式建模分域 free-list、slice 本地分配、checkpoint 建立和回滚传播。
- RTL 应拆成 map read、destination allocate、checkpoint capture、reclaim merge 和 recovery apply 几段。

## 7. 行为模型落点

行为模型应覆盖：

- 正常分配
- free-list 空时阻塞
- old prf 回收
- branch/checkpoint 建立
- flush 后恢复映射
- 多域寄存器独立回收

## 8. RTL 落点

RTL 先实现：

- map table primitive
- free-list
- checkpoint storage
- rename dispatch
- rollback control
- rename top

## 9. 二级文档

- `rename/data_path/README.md`
- `rename/control_path/README.md`
- `rename/README.md`
- `rename/map_tables_and_allocation.md`
- `rename/checkpoint_recovery_and_reclaim.md`

## 10. 模块文档

- `rename/README.md`
- `rename/INDEX.md`
- `rename/data_path/README.md`
- `rename/control_path/README.md`
- `rename/top_mixed/README.md`
