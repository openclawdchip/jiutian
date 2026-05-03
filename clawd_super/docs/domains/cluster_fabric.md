# Cluster Fabric

## 1. 角色

cluster fabric 负责把多个 tile、共享 slice、bridge 和集群服务联成一个统一的数据与控制平面。

## 2. 范围

cluster fabric 覆盖：

- transport
- slice
- cpu bridge
- debug/service bridge
- shared service logic
- memory side bridge
- cluster-local models

## 3. 固定目标

| 项目 | 定义 |
|---|---|
| Tile 规模 | `8 cores / tile` |
| Cluster 规模 | `8 tiles / cluster` |
| L3 slice | `32MB / tile` |
| Fabric 目标 | 面向 `4.0 GHz` 顶层频率分层切拍 |
| Fabric 链路 | 宽带 request/response 双向链路 |

## 4. 事务类型

| 类型 | 说明 |
|---|---|
| request | 来自 core/L2 的访问请求 |
| response | 数据、状态和确认返回 |
| snoop | 一致性广播或定向消息 |
| service | debug、配置、管理、监测类事务 |

## 5. 关键要求

- 传输层和功能层分离
- 桥接模块只做协议转换和 buffering
- slice 只处理自己负责的局部状态
- shared service 模块不污染主数据路径

## 6. Floorplan 视角

### 6.1 物理目标

cluster fabric 的目标是把长距离片上互连做成天然可切拍的边缘网络。它不是一条抽象总线，而是一组沿 tile 外缘、slice 外缘和桥接边界分布的 request/response/service 平面。

### 6.2 推荐分区

- tile 侧 ingress/egress、`L2` miss 出口和 cluster fabric 入口紧邻摆放。
- request/response 主数据平面与 debug/service 平面分离，避免管理事务污染主吞吐链路。
- directory、slice、bridge 采用局部拥有权和就近出口的布局方式，不把所有共享状态集中到单一中岛。
- memory side bridge 和跨 cluster 出口位于最外缘，天然承接更长的链路与更松的周期边界。

### 6.3 时序约束

- 所有长距离链路都要在协议层上允许显式切拍与 credit 缓冲。
- bridge 只承担协议转换、buffering 和域隔离，不承担大块功能计算。
- service、trace、配置和维护类事务默认通过独立侧带或低优先级面传输。

### 6.4 对后续模型的约束

- 行为模型需要表达分段 hop、edge buffer、route 选择、ownership 和双平面事务。
- RTL 应把 transport、slice、directory、bridge、service spine 分成独立层次。

## 7. 行为模型落点

行为模型应覆盖：

- 基本 request/response 通路
- bridge buffering
- slice route and ownership
- service request path
- broadcast / multicast 控制类事务

## 8. RTL 落点

RTL 可拆为：

- transport path
- slice path
- bridge family
- service family
- cluster top

## 9. 二级文档

- `cluster_fabric/data_path/README.md`
- `cluster_fabric/control_path/README.md`
- `cluster_fabric/README.md`
- `cluster_fabric/transport_routing_and_flow_control.md`
- `cluster_fabric/slices_directory_and_services.md`

## 10. 模块文档

- `cluster_fabric/README.md`
- `cluster_fabric/INDEX.md`
- `cluster_fabric/data_path/README.md`
- `cluster_fabric/control_path/README.md`
- `cluster_fabric/top_mixed/README.md`
