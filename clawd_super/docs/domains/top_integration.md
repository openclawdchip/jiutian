# Top Integration

## 1. 角色

top integration 负责把朱雀的 core、tile、cluster 和 subsystem 级模块装配成一条可综合、可验证、可扩展的层级链。

## 2. 目标

top integration 不是只写一个顶层 wrapper，而是定义：

- 顶层层级关系
- 公共 package
- 公共接口
- clock/reset 入口
- domain 之间的边界
- 观测、调试和系统控制入口

## 3. 主要对象

| 模块 | 作用 |
|---|---|
| `zhuque_pkg` | 全局常量、枚举、公共类型 |
| `zhuque_core` | 核心顶层 |
| `zhuque_tile` | tile 顶层 |
| `zhuque_cluster` | cluster 顶层 |
| `zhuque_subsystem` | SoC host subsystem 顶层 |

## 4. 必须显式化的接口

- core 到 L1/L2 的访存接口
- core 到平台控制的 interrupt/debug 接口
- tile 到 cluster 的 cache/coherence/transport 接口
- cluster 到外部 subsystem 的 memory/fabric/service 接口

## 5. Floorplan 视角

### 5.1 物理目标

top integration 的职责之一，是把朱雀各级层次之间的物理边界在架构上先定义出来，而不是等 RTL 互连拉满之后再回头修。它需要明确哪些接口是本地短连、哪些接口天然跨层、哪些地方必须预留 pipeline 和 service spine。

### 5.2 推荐分区

- `zhuque_core` 内部围绕前端、中部调度区、执行区、`LSU` 和退休脊柱分区。
- `zhuque_tile` 负责把 core 群、`L2` bank group、本地目录与 tile 边缘端点组织成相对稳定的物理岛。
- `zhuque_cluster` 负责把多个 tile 与 shared slice、fabric edge、memory bridge 放到外层互连框架中。
- `zhuque_subsystem` 只接外部控制、内存和服务，不把高频主数据路径继续拖长。

### 5.3 时序约束

- 任何跨 core、跨 tile、跨 cluster 的宽接口都必须在文档中带有可见的切拍边界。
- clock/reset、debug/service、trace 与主数据面分层定义，避免在顶层互连里混成一类接口。
- 顶层 package 和 interface 需要天然支持 bank、slice、cluster-local id 和分段 credit。

### 5.4 对后续模型的约束

- 行为模型需要体现层级化 backpressure、分层 flush 广播和层级边界延迟。
- RTL 集成阶段必须允许接口先落成分层壳体，再逐域补全内部结构。

## 6. 行为模型落点

top integration 的行为模型不追求门级或 cycle-accurate，而是表达：

- 模块装配是否合法
- 事务沿层级的传播路径
- 关键 reset 和 flush 广播路径
- cluster 到 tile 再到 core 的 backpressure 传播

## 7. RTL 落点

RTL 阶段的 top integration 先完成：

- package
- interface
- 空壳 top
- 域连接
- 参数化实例化

等各域 RTL 成熟后，再补性能和低功耗细节。

## 8. 二级文档

- `top_integration/README.md`
- `top_integration/hierarchy_and_packaging.md`
- `top_integration/fabric_and_system_interfaces.md`

## 9. 模块文档

- `top_integration/README.md`
- `top_integration/INDEX.md`
- `top_integration/data_path/README.md`
- `top_integration/control_path/README.md`
- `top_integration/top_mixed/README.md`
