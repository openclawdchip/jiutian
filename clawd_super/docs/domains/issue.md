# Issue

## 1. 角色

issue 负责接收 rename 后的 uop，按域放入队列，追踪源操作数 readiness，在资源允许时选择最合适的 entry 发射到执行端。

## 2. 设计目标

issue 域必须同时满足：

- 多队列分域
- oldest-ready 优先
- wakeup/select 分离
- resource-aware 发射
- flush/replay 后可恢复

## 3. 队列域

朱雀 issue 建议划分为：

- integer issue queue
- branch issue queue
- memory issue queue
- vector issue queue
- special/system issue queue

## 4. 固定目标

| 项目 | 定义 |
|---|---|
| Dispatch 接入宽度 | `16 uop/cycle` |
| Integer issue select | `16/cycle` |
| Memory issue select | `12/cycle` |
| Vector issue select | `12/cycle` |
| Integer queue | `128` entries |
| Branch queue | `48` entries |
| Memory queue | `96` entries |
| Vector queue | `128` entries |
| Special/System queue | `32` entries |

## 5. 关键部件

- ready table
- scoreboard
- forwarding match
- queue entry state
- age/select arbiter
- resource blocker
- replay/recovery path

## 6. 输入输出

| 输入 | 说明 |
|---|---|
| renamed uop | 来自 rename |
| writeback/forward | 来自执行和 loadstore |
| replay/recovery | 来自 loadstore、commit、debug |
| resource busy | 来自执行单元和后端资源 |

| 输出 | 说明 |
|---|---|
| issue grants | 发给各执行域 |
| backpressure | 反馈给 rename |
| occupancy / block stats | 反馈给 PMU 和调试域 |

## 7. 关键行为

- dispatch 入队
- source not-ready 阻塞
- writeback 唤醒
- port busy 延迟发射
- oldest-ready 选择
- replay 保留 entry
- flush 清除 younger work

## 8. Floorplan 视角

### 8.1 物理目标

issue 的核心是把 wakeup/select 做成局部闭环，而不是一个覆盖整核的大组合云。朱雀的 issue 必须按执行域和物理位置拆开，让最常用的 ready、select 和 bypass 在本地完成。

### 8.2 推荐分区

- integer、branch、memory、vector、special 五类队列各自靠近对应执行域。
- integer issue 再按低延迟整数簇分片，branch/select 更靠近 redirect 脊柱。
- memory queue 靠近 AGU 和 LSU 入口，vector queue 靠近 VRF 和向量簇边缘。
- ready table 和 scoreboard 尽量本地化，只把少量授予结果和必须的跨域依赖广播出去。

### 8.3 时序约束

- wakeup 与 select 至少分成两段：本地 ready 形成和本地发射选择。
- 最常用的旁路命中优先在本地簇内闭合，跨簇广播默认带流水边界。
- replay、flush 和 resource busy 事件不能要求所有 issue 区域在单拍组合收敛。

### 8.4 对后续模型的约束

- 行为模型需要带上分域队列、局部 ready、局部仲裁和跨域资源阻塞。
- RTL 需要把 queue entry、ready update、age compare、select、grant merge 拆层实现。

## 9. 行为模型落点

行为模型应先覆盖：

- integer/memory/vector/system 分域队列
- ready table 与 register bank 抽象
- oldest-ready select
- replay 和 branch flush
- 队列满的 backpressure

## 10. RTL 落点

RTL 可拆为：

- queue entry
- ready table
- forwarding network
- age/select
- per-domain queue
- issue top

## 11. 二级文档

- `issue/data_path/README.md`
- `issue/control_path/README.md`
- `issue/README.md`
- `issue/queues_wakeup_and_select.md`
- `issue/dispatch_replay_and_backpressure.md`

## 12. 模块文档

- `issue/README.md`
- `issue/INDEX.md`
- `issue/data_path/README.md`
- `issue/control_path/README.md`
- `issue/top_mixed/README.md`
