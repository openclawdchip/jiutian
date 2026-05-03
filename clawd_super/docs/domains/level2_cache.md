# Level2 Cache

## 1. 角色

level2 cache 是 core 侧访存与 cluster fabric 之间的本地共享缓存层。它负责 tag/data 管理、bank 访问、请求流水、替换策略、prefetch 和与 cluster 的一致性接口。

## 2. 组成

- bank group
- tag array
- data array
- request pipe
- response path
- replacement policy
- prefetch helper
- coherence / snoop entry

## 3. 固定目标

| 项目 | 定义 |
|---|---|
| 容量 | `16MB / tile` |
| Bank 数 | `64` |
| Tag/Data 并发访问 | 支撑 `8` 核高并发访存 |
| MSHR | `128` |
| Prefetch queue | `48` |

## 4. 输入输出

| 输入 | 说明 |
|---|---|
| loadstore requests | 来自 core |
| cluster snoop/invalidate | 来自 cluster fabric |
| control events | 来自平台和调试域 |

| 输出 | 说明 |
|---|---|
| data response | 返回 core |
| miss request | 发往 cluster fabric |
| replacement / maintenance events | 发给控制域 |

## 5. 关键设计点

- bank 和 pipe 必须解耦
- tag/data 仲裁显式化
- 替换状态不与主数据路径纠缠
- prefetch 不破坏 demand request 时序

## 6. Floorplan 视角

### 6.1 物理目标

level2 cache 的目标不是形成一个逻辑上完整的中心缓存，而是把大容量 `L2` 切成贴近 tile 边界的分布式 bank 群。对朱雀来说，`L2` 的 hot pipe 必须围绕 bank access 展开，而 replacement、prefetch、目录和维护逻辑都要退到外围。

### 6.2 推荐分区

- `64` 个 bank 按多个 bank group 沿 tile 周边或核心群四周铺开。
- 每个 core 或 core 组面对相对更近的一组 `L2` 入口，减少 miss 请求的初始线长。
- tag/data hot pipe 本地化到 bank group，`MSHR`、replacement 和 prefetch 控制保持分层。
- 返回 core 的 data response 提前切拍，不把远端 bank 的宽数据无拍拉回核心。

### 6.3 时序约束

- tag 命中、data select、response return 不允许被替换和维护控制拖长。
- prefetch 与 demand request 只在受控边界共享资源，不进入同一最短仲裁环。
- 远距离 bank group 之间的协同默认带流水边界或边缘 buffer。

### 6.4 对后续模型的约束

- 行为模型需要体现 bank group、局部冲突、`MSHR` 分层和返回路径拍数。
- RTL 应把 bank pipe、request route、response return、replacement、prefetch、maintenance 明确拆层。

## 7. 行为模型落点

行为模型应覆盖：

- hit/miss
- bank 冲突
- replacement state 变更
- fill and response
- invalidate / snoop side effect

## 8. RTL 落点

RTL 拆为：

- tag/data primitive
- bank arb
- request pipe
- response path
- replacement
- prefetch
- level2 top

## 9. 二级文档

- `level2_cache/data_path/README.md`
- `level2_cache/control_path/README.md`
- `level2_cache/README.md`
- `level2_cache/bank_pipe_and_mshr.md`
- `level2_cache/coherence_fill_replacement_and_prefetch.md`

## 10. 模块文档

- `level2_cache/README.md`
- `level2_cache/INDEX.md`
- `level2_cache/data_path/README.md`
- `level2_cache/control_path/README.md`
- `level2_cache/top_mixed/README.md`
