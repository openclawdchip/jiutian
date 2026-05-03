# Vector Execute

## 1. 角色

vector execute 负责 RVV 主体执行，包括 lane 运算、mask/predicate、permute、vector MAC、vector reduction 以及向量浮点分支。

## 2. 设计目标

- 明确 lane 级并行边界
- 把 control 和 datapath 分层
- 将 vector 写回、旁路和 load/store 配合统一起来

## 3. 子功能

- vector integer ALU
- predicate and mask
- permute and shuffle
- vector shift / saturate / round
- vector MAC / dot-product
- vector floating-point helper
- vector register writeback

## 4. 固定目标

| 单元 | 数量 |
|---|---:|
| Vector integer cluster | 12 |
| Vector permute cluster | 6 |
| Vector MAC / dot cluster | 8 |
| Vector FP cluster | 6 |
| Vector writeback merge path | 12 |

## 5. 输入输出

| 输入 | 说明 |
|---|---|
| vector issue packet | 来自 issue |
| VRF source data | 向量寄存器读端口 |
| scalar side inputs | 标量控制或广播结果 |

| 输出 | 说明 |
|---|---|
| vector writeback | 向量结果 |
| predicate side effects | 掩码或条件结果 |
| replay or fault | 与 loadstore 或系统控制联动 |

## 6. Floorplan 视角

### 6.1 物理目标

vector execute 的布局中心不是控制逻辑，而是 `VRF`。朱雀的向量域必须围绕 banked `VRF` 组织 lane、permute、MAC 和 FP 簇，让最贵的跨 lane 互联和回写线路尽量短。

### 6.2 推荐分区

- `VRF` 采用条带式 bank 组织，向量整数、permute、MAC、FP 围绕其边缘分区摆放。
- predicate 和 mask 逻辑位于 issue 入口与写回入口之间，承担向量域的控制边界。
- permute/shuffle 靠近 `VRF` 和 lane crossbar，一次只跨必要的 lane 群，不把全局交叉放到统一中心。
- MAC 和 reduction 更靠近各自的部分积与归约树，簇内先做本地累加，再出簇。

### 6.3 时序约束

- 向量写回采用分层聚合，先簇内合并，再进入 `VRF` 写口。
- 跨 lane permute、mask broadcast 和长距离归约默认含有结构化切拍点。
- 标量到向量的 side input 只在必要边界广播，不允许把所有控制都拖进 `VRF` 热区。

### 6.4 对后续模型的约束

- 行为模型需要显式体现 `VRF` bank、lane group、permute 网络、簇内归约和层级式写回。
- RTL 应把 predicate、valu、permute、vmac、vfp、writeback merge 分成独立簇。

## 7. 行为模型落点

行为模型应覆盖：

- lane 级整数运算
- mask 传播
- permute / predicate
- vector MAC 结果拼装
- 基本浮点向量操作抽象

## 8. RTL 落点

RTL 先按簇拆开：

- predicate cluster
- permute cluster
- valu cluster
- vmac cluster
- vf helper cluster
- vrf writeback cluster
- vector top

## 9. 二级文档

- `vector_execute/README.md`
- `vector_execute/lane_mask_and_permute.md`
- `vector_execute/mac_fp_and_vector_writeback.md`

## 10. 模块文档

- `vector_execute/README.md`
- `vector_execute/INDEX.md`
- `vector_execute/data_path/README.md`
- `vector_execute/control_path/README.md`
- `vector_execute/top_mixed/README.md`
