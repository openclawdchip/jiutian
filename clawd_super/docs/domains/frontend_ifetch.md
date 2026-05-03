# IFetch

## 1. 角色

ifetch 负责生成程序计数器、获取指令、维护预测状态、对齐指令边界，并将指令片段送入 decode 前队列。

## 2. 子功能

朱雀的 ifetch 拆成以下子功能：

- PC 选择和顺序递进
- branch target buffer
- direction predictor
- return stack
- indirect target prediction
- instruction cache 前端
- fetch queue
- replay 和 redirect
- RVC 边界识别

## 3. 固定目标

| 项目 | 定义 |
|---|---|
| Fetch 带宽 | `192B/cycle` |
| 指令供给目标 | 支撑 `16` 路译码 |
| Fetch queue | `96` entries |
| BTB | `32K` entries |
| Direction predictor | `128K` entries |
| RAS | `96` entries |
| Outstanding I-cache miss | `32` |

## 4. 关键接口

| 输入 | 说明 |
|---|---|
| redirect | 来自 commit、branch、debug 的重定向 |
| icache response | 指令 cache 返回 |
| control gates | 来自平台控制和低功耗域的使能 |

| 输出 | 说明 |
|---|---|
| fetch packet | 给 decode 的指令载荷 |
| predictor update | 给前端内部预测器的训练输入 |
| miss/replay events | 给 PMU 和调试域的事件 |

## 5. 状态对象

ifetch 至少需要维护：

- 当前 fetch pc
- 预测器表项
- 返回栈
- outstanding miss 状态
- fetch queue head/tail
- replay pending 状态

## 6. 事务定义

主要事务包括：

- 顺序取指
- 命中后入队
- miss 后等待并 replay
- branch/exception/debug redirect
- queue 满导致前端停顿

## 7. Floorplan 视角

### 7.1 物理目标

ifetch 的首要目标不是把预测功能做得最集中，而是把 `redirect -> next pc -> fast predict -> cache request` 这条闭环压到最短。为此，前端必须天然支持分片取指、分层预测和前后端解耦。

### 7.2 推荐分区

- `next-pc` 选择器、redirect 汇合点和 fast target 预测单元组成一条北侧快速脊柱。
- `BTB`、方向预测、`RAS` 和间接目标预测分层摆放，只有最短环需要的目标与方向信息留在快层。
- `L1I` 按多 bank 组织，fetch 数据从多个 slice 并行出线，而不是一条超宽集中总线。
- fetch align、RVC 边界识别和 predecode 位于 `L1I` 出口与 decode 入口之间，承担指令边界修整和局部标记任务。
- fetch queue 放在前端和 decode 之间，作为物理节拍隔离带。

### 7.3 时序约束

- `192B/cycle` 取指默认按多个 fetch slice 并行实现，不允许单体组合拼线。
- `L1I 256KB` 默认按多拍访问组织，命中延迟通过 line buffer、next-line 预取和 queue 解耦吸收。
- predictor training、替换、统计和维护更新不得进入 fetch 最短命中路径。
- redirect 返回通路必须短于 predictor 训练通路，debug 和异常的重定向也复用同一快速返回脊柱。

### 7.4 对后续模型的约束

- 行为模型需要显式体现 fetch slice、queue 容量、bank 冲突和 replay 重取。
- RTL 需要把 fast predict、slow update、icache bank access、align/predecode 拆成独立流水边界。

## 8. 行为模型落点

行为模型应覆盖：

- 顺序 pc 推进
- redirect 优先级
- fetch queue 接收与阻塞
- predictor update
- miss/replay
- RVC 2B/4B 指令边界

## 9. RTL 落点

RTL 应拆成：

- predictor 子模块
- icache interface
- fetch queue
- redirect/replay control
- top ifetch orchestrator

## 10. 模块文档

- `frontend_ifetch/README.md`
- `frontend_ifetch/INDEX.md`
- `frontend_ifetch/data_path/README.md`
- `frontend_ifetch/control_path/README.md`
- `frontend_ifetch/top_mixed/README.md`
