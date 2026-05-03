# Decode And Uop

## 1. 角色

decode 负责把取指得到的原始指令转换成内部统一的 uop contract，并把架构层信息变成后端可消费的结构化字段。

## 2. 范围

decode 域包含：

- 指令长度识别
- RVC 展开
- RV64 标量指令解码
- CSR/system 类指令解码
- RVV 指令分类
- exception/illegal instruction 元数据形成
- uop 字段拼装

## 3. 固定目标

| 项目 | 定义 |
|---|---|
| Decode 宽度 | `16 inst/cycle` |
| Uop 形成宽度 | `16 uop/cycle` |
| RVC 并行展开 | `16-way` |
| Decode 输出目标 | 每周期饱和支撑 `16` 路 rename 输入 |

## 4. uop contract

朱雀的 uop 至少需要包含：

- 类别
- opcode
- 源寄存器
- 目的寄存器
- 立即数
- 内存属性
- CSR 属性
- vector 属性
- trap 属性
- 序号和上下文标签

## 5. 边界

decode 不负责：

- 物理寄存器分配
- 执行资源选择
- 精确 trap 最终裁决

这些职责分别属于 rename、issue 和 commit。

## 6. Floorplan 视角

### 6.1 物理目标

decode 的重点是把 `16 inst/cycle` 变成可切开的物理结构。朱雀的 decode 不能做成单体超宽译码器，而是要把长度识别、RVC 展开、局部分类和 uop 打包拆进多个并行 slice。

### 6.2 推荐分区

- decode 入口按 `4 x 4` slice 组织，每个 slice 直接接收本地 fetch slice 输出。
- 每个 slice 内部本地完成长度判断、RVC 展开、立即数提取和常见整数类 opcode 分类。
- 稀有系统指令、复杂 trap 元数据和少量全局一致性校验放在 slice 后段或单独聚合层。
- uop packer 的输出布局需要直接对齐 rename slice 的入口，减少 decode 到 rename 之间的横向重排。

### 6.3 时序约束

- 非法指令、系统类慢路径、调试类标记不能压在最短 decode 组合深度上。
- decode 与 rename 之间必须保留明确的切拍点或 queue 边界，避免 `16` 路字段一次性横跨中部主干。
- predecode 产生的边界信息要尽量在 slice 本地被消费，而不是统一回到单点后再分发。

### 6.4 对后续模型的约束

- 行为模型应按 slice 表达吞吐、背压和局部异常标记形成。
- RTL 需要把 predecode、compressed expand、main decode、uop pack 明确切成多级而不是单层大组合块。

## 7. 行为模型落点

行为模型应覆盖：

- 指令长度判断
- RVC 展开
- 典型整数/分支/LS/CSR/RVV 指令的 uop 形成
- 非法指令和未实现指令的异常元数据

## 8. RTL 落点

RTL 可以拆成：

- predecode helper
- compressed expand
- opcode classification
- uop packer
- decode top

## 9. 二级文档

- `decode_and_uop/data_path/README.md`
- `decode_and_uop/control_path/README.md`
- `decode_and_uop/README.md`
- `decode_and_uop/decode_pipeline_and_expansion.md`
- `decode_and_uop/uop_encoding_and_trap_metadata.md`

## 10. 模块文档

- `decode_and_uop/README.md`
- `decode_and_uop/INDEX.md`
- `decode_and_uop/data_path/README.md`
- `decode_and_uop/control_path/README.md`
- `decode_and_uop/top_mixed/README.md`
