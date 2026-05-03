# Shared Cells And Models

## 1. 角色

shared cells and models 负责为整个朱雀工程提供基础小模块、抽象 RAM 模型、CDC 元件和可被多个域共享的轻量原语。

## 2. 典型内容

- one-read-one-write RAM model
- tag/data/victim RAM helper
- small FIFO
- arbiter
- CDC sync primitive
- clock gate wrapper
- common type helpers

## 3. 设计要求

- 尽量参数化
- 语义简单透明
- 不混入复杂业务逻辑
- 可独立测试

## 4. Floorplan 视角

### 4.1 物理目标

shared 域虽然不直接承担大块功能，但它决定朱雀能不能把 bank、slice、流水边界和局部仲裁真正落成可复用组件。共享原语必须天然适配高频、分布式和多实例复制的布局方式。

### 4.2 推荐约束

- RAM model 要支持 bank 化、独立端口方向和显式读写时序。
- FIFO、arbiter、queue helper 要支持局部仲裁和层级化汇总，而不是只支持单点集中结构。
- CDC、clock gate 和 reset wrapper 要把域边界、使能边界和测试可观测性明确暴露出来。
- 公共类型和 helper package 要能表达 bank id、slice id、lane id、cluster-local source id。

### 4.3 对后续模型的约束

- 行为模型需要把共享 primitive 的容量、端口、时序边界表达清楚，避免上层域私自发明不兼容语义。
- RTL 需要优先复用 shared primitive，保证不同域的 bank、queue 和 arbitrate 行为可统一验证。

## 5. 行为模型落点

shared 域的行为模型主要服务两个目标：

- 给上层域提供可执行依赖
- 给 RTL primitive 提供明确语义

## 6. RTL 落点

shared RTL 先做：

- RAM models
- CDC cells
- arbiters
- basic gates or wrappers
- shared package

## 6. 使用方式

所有复杂域都优先依赖 shared 提供的基础件，而不是在各自目录里私自复制一份小模块。

## 8. 二级文档

- `shared_cells_and_models/README.md`
- `shared_cells_and_models/memory_queue_and_arbiter_primitives.md`
- `shared_cells_and_models/cdc_clocking_and_common_types.md`

## 9. 模块文档

- `shared_cells_and_models/README.md`
- `shared_cells_and_models/INDEX.md`
- `shared_cells_and_models/data_path/README.md`
- `shared_cells_and_models/control_path/README.md`
- `shared_cells_and_models/top_mixed/README.md`
